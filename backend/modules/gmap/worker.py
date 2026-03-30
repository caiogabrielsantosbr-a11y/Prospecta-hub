"""
Google Maps Extractor — Playwright Worker
Port of content.js + background.js scraping logic.
Uses Playwright to navigate Google Maps, collect business URLs, and extract details.
Includes email extraction from website domains.
"""
import asyncio
import re
import sys
import threading
from typing import Optional
import httpx
from playwright.async_api import async_playwright, Page, Browser
from playwright.async_api import TimeoutError as PlaywrightTimeout

from database.supabase_client import get_supabase_client
from modules.gmap.location_utils import load_location_set_name


# ── Email Extraction Helpers ──
IGNORE_USERS = ["exemplo", "ex", "email", "seuemail", "nome", "user", "usuario", "teste", "test", "admin", "domain", "contato_exemplo"]
IGNORE_DOMAINS_LIST = ["exemplo.com", "email.com", "teste.com", "dominio.com", "example.com", "domain.com"]
IGNORE_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".js", ".css", ".woff", ".ttf"]
CONTACT_PATHS = ["", "/contato", "/contact", "/fale-conosco", "/sobre", "/about"]


def extract_domain_from_url(url: str) -> str:
    """Extract clean domain from URL."""
    if not url or url == "Sem Website":
        return ""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if url.startswith("http") else f"http://{url}")
        return parsed.hostname or ""
    except Exception:
        return ""


def extract_best_email(text: str) -> Optional[str]:
    """Extract the best email from page text, filtering junk."""
    raw_emails = re.findall(r"[\w\.\-]+@[\w\.\-]+\.\w+", text, re.IGNORECASE)
    if not raw_emails:
        return None

    for email in set(raw_emails):
        clean = email.strip()
        lower = clean.lower()
        parts = lower.split("@")
        if len(parts) != 2:
            continue
        user, domain = parts

        if any(lower.endswith(ext) for ext in IGNORE_EXTS):
            continue
        if user in IGNORE_USERS or domain in IGNORE_DOMAINS_LIST:
            continue
        if len(user) < 2 or len(domain) < 3:
            continue
        return clean
    return None


async def fetch_rdap_email(domain: str, client: httpx.AsyncClient) -> Optional[str]:
    """Fetch email from RDAP registry."""
    url = (
        f"https://rdap.registro.br/domain/{domain}"
        if domain.lower().endswith(".com.br")
        else f"https://rdapserver.net/domain/{domain}"
    )
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        for ent in data.get("entities", []):
            vc = ent.get("vcardArray")
            if vc and len(vc) > 1:
                for item in vc[1]:
                    if item[0] == "email":
                        return item[3].replace("mailto:", "").strip()
    except Exception:
        pass
    return None


async def fetch_page_email(domain: str, client: httpx.AsyncClient) -> Optional[str]:
    """Scrape contact pages for emails."""
    for path in CONTACT_PATHS:
        url = f"https://{domain}{path}"
        try:
            resp = await client.get(url, timeout=10, follow_redirects=True)
            if resp.status_code == 200:
                email = extract_best_email(resp.text)
                if email:
                    return email
        except Exception:
            continue
    return None


async def extract_email_from_website(website: str, info, tm, main_loop=None) -> Optional[str]:
    """Extract email from website domain using RDAP + page scraping."""
    domain = extract_domain_from_url(website)
    if not domain:
        return None
    
    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Try RDAP first
            email = await fetch_rdap_email(domain, client)
            if email:
                return email
            
            # Try page scraping
            email = await fetch_page_email(domain, client)
            return email
    except Exception as e:
        info.add_log(f"Erro ao extrair email de {domain}: {str(e)}", "warning")
        await _broadcast_safe(tm, info, main_loop)
        return None


async def wait_and_get(page: Page, selector: str, timeout: int = 8000) -> bool:
    """Wait for a selector to appear on the page."""
    try:
        await page.wait_for_selector(selector, timeout=timeout, state="visible")
        return True
    except Exception as e:
        print(f"[GMap] Timeout waiting for {selector}: {e}")
        return False


async def collect_urls(page: Page, search_query: str, info, tm, main_loop=None) -> list[str]:
    """
    Navigate to Google Maps with a search query and scroll the feed
    to collect all business URLs (mirrors content.js startCollecting).
    """
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
    info.add_log(f"Navegando: {url}", "info")
    await _broadcast_safe(tm, info, main_loop)

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)
    except Exception as e:
        info.add_log(f"Erro ao carregar página: {str(e)}", "error")
        return []

    # Wait for feed
    feed_selector = "div[role='feed']"
    found = await wait_and_get(page, feed_selector, 15000)
    if not found:
        info.add_log("Feed não encontrado. Verifique a busca.", "warning")
        await _broadcast_safe(tm, info, main_loop)
        return []

    info.add_log("Feed encontrado! Iniciando coleta...", "success")
    await _broadcast_safe(tm, info, main_loop)

    # Scroll loop
    end_of_list = False
    consecutive_no_new = 0
    last_count = 0
    max_attempts = 30  # Limite de tentativas

    for attempt in range(max_attempts):
        if info.is_cancelled() or end_of_list:
            break
        
        if not main_loop:
            await info.wait_if_paused()

        # Scroll feed to bottom
        try:
            await page.evaluate("""
                const feed = document.querySelector("div[role='feed']");
                if (feed) {
                    feed.scrollTop = feed.scrollHeight;
                }
            """)
        except Exception as e:
            info.add_log(f"Erro ao scrollar: {str(e)}", "warning")
        
        await asyncio.sleep(2)

        # Check end of list
        try:
            body_text = await page.evaluate("document.body.innerText")
            if "Você chegou ao final da lista" in body_text or "You've reached the end of the list" in body_text:
                info.add_log("Final da lista detectado", "info")
                end_of_list = True
                break
        except Exception:
            pass

        # Check stagnation
        try:
            current_count = await page.evaluate("""
                document.querySelectorAll('a[href*="/maps/place/"]').length
            """)
            
            if current_count == last_count:
                consecutive_no_new += 1
                if consecutive_no_new > 5:
                    info.add_log(f"Sem novos resultados após {consecutive_no_new} tentativas", "info")
                    end_of_list = True
                    break
            else:
                consecutive_no_new = 0
                last_count = current_count
                if current_count % 10 == 0:  # Log a cada 10 itens
                    info.add_log(f"Coletando URLs... ({current_count} encontradas)", "info")
                    await _broadcast_safe(tm, info, main_loop)
        except Exception as e:
            info.add_log(f"Erro ao contar URLs: {str(e)}", "warning")

    # Collect all unique hrefs
    try:
        urls = await page.evaluate("""
            [...new Set(
                Array.from(document.querySelectorAll('a[href*="/maps/place/"]'))
                    .map(a => a.href)
                    .filter(h => h.includes('/place/'))
            )]
        """)
    except Exception as e:
        info.add_log(f"Erro ao coletar URLs: {str(e)}", "error")
        return []

    info.add_log(f"✓ {len(urls)} URLs coletadas", "success")
    await _broadcast_safe(tm, info, main_loop)
    return urls


async def extract_place_details(page: Page, url: str) -> dict:
    """
    Navigate to a Google Maps place page and extract business details.
    Mirrors content.js scrapeDetails().
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        # Wait for name
        name_found = await wait_and_get(page, "h1.DUwDvf", 10000)
        if not name_found:
            return {"nome": "Erro - Timeout", "telefone": "", "website": "", "endereco": "", "error": "Timeout"}

        data = await page.evaluate(r"""
            (() => {
                const d = { nome: '', telefone: 'Sem Telefone', website: 'Sem Website', endereco: '' };

                // Nome
                const nameEl = document.querySelector('h1.DUwDvf');
                if (nameEl) d.nome = nameEl.innerText.trim();

                // Website
                const webBtn = document.querySelector('a[data-item-id="authority"]');
                if (webBtn) d.website = webBtn.getAttribute('href');

                // Telefone - Múltiplas estratégias
                const phoneBtn = document.querySelector('button[data-item-id*="phone:tel:"]');
                if (phoneBtn) {
                    let text = phoneBtn.innerText.trim().replace(/[^\d\s\-\(\)\+]/g, '').trim();
                    d.telefone = text || 'Sem Telefone';
                } else {
                    // Fallback: procurar por ícone de telefone
                    const buttons = document.querySelectorAll('button');
                    for (const b of buttons) {
                        const icon = b.querySelector('img[src*="phone_"]');
                        if (icon) {
                            d.telefone = b.innerText.trim().replace(/[^\d\s\-\(\)\+]/g, '');
                            break;
                        }
                    }
                    
                    // Fallback 2: procurar por aria-label com "phone"
                    if (d.telefone === 'Sem Telefone') {
                        for (const b of buttons) {
                            const ariaLabel = b.getAttribute('aria-label');
                            if (ariaLabel && ariaLabel.toLowerCase().includes('phone')) {
                                const match = b.innerText.match(/[\d\s\-\(\)\+]+/);
                                if (match) {
                                    d.telefone = match[0].trim();
                                    break;
                                }
                            }
                        }
                    }
                }

                // Endereço
                const addrBtn = document.querySelector('button[data-item-id="address"]');
                if (addrBtn) {
                    d.endereco = addrBtn.getAttribute('aria-label')
                        ? addrBtn.getAttribute('aria-label').replace('Endereço: ', '').replace('Address: ', '')
                        : addrBtn.innerText;
                }

                return d;
            })()
        """)
        return data
    except PlaywrightTimeout:
        return {"nome": "Erro - Timeout", "telefone": "", "website": "", "endereco": "", "error": "Timeout"}
    except Exception as e:
        return {"nome": "Erro", "telefone": "", "website": "", "endereco": "", "error": str(e)}


async def gmap_worker(info, tm):
    """
    Background worker for Google Maps extraction.
    On Windows, Playwright is run in a dedicated thread with its own
    ProactorEventLoop to avoid the NotImplementedError from uvicorn's
    reload-mode SelectorEventLoop.
    """
    if sys.platform == 'win32':
        # Run Playwright in a dedicated thread with ProactorEventLoop
        main_loop = asyncio.get_event_loop()
        exception_holder = [None]

        def _run_in_thread():
            # Create a fresh ProactorEventLoop for this thread
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_gmap_playwright_work(info, tm, main_loop))
            except Exception as e:
                exception_holder[0] = e
            finally:
                loop.close()

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        # Wait for thread to finish without blocking the event loop
        while thread.is_alive():
            await asyncio.sleep(0.5)
        thread.join()

        if exception_holder[0]:
            raise exception_holder[0]
    else:
        await _gmap_playwright_work(info, tm)


async def _broadcast_safe(tm, info, main_loop=None):
    """Broadcast task update, safely from any thread."""
    if main_loop and main_loop != asyncio.get_event_loop():
        future = asyncio.run_coroutine_threadsafe(tm.broadcast(info), main_loop)
        future.result(timeout=5)
    else:
        await tm.broadcast(info)


async def _gmap_playwright_work(info, tm, main_loop=None):
    """
    Core Playwright logic — runs URL collection and detail extraction.
    Phase 1: Collect URLs by scrolling the search feed
    Phase 2: Visit each URL to extract business details
    Phase 3: Extract email from website if available
    """
    # Initialize Supabase client singleton
    supabase_client = get_supabase_client()
    
    # Check if Supabase integration is available
    if not supabase_client.is_available():
        # Try to reload credentials in case they were added after initialization
        info.add_log("Tentando recarregar credenciais do Supabase...", "info")
        if supabase_client.reload_credentials():
            info.add_log("✓ Supabase conectado com sucesso!", "success")
        else:
            info.add_log("⚠️ Supabase indisponível - leads serão salvos apenas localmente", "warning")
    else:
        info.add_log("✓ Supabase conectado", "success")
    
    config = info.config
    cities = config.get("cities", [])
    search_term = config.get("searchTerm", "")
    delay = config.get("delay", 2000) / 1000
    headless = config.get("headless", True)  # Novo parâmetro para navegador visual
    extract_emails = config.get("extractEmails", True)  # Novo parâmetro para extração de email

    # Identify location set name from cities list
    location_set_name = load_location_set_name(cities)
    info.add_log(f"Conjunto de locais identificado: {location_set_name}", "info")
    await _broadcast_safe(tm, info, main_loop)

    all_urls = []
    total_cities = len(cities)

    # Initialize statistics including Supabase tracking
    info.stats = {
        "queue": 0,
        "done": 0,
        "leads": 0,
        "errors": 0,
        "phase": "collecting",
        "supabase_success": 0,
        "supabase_failures": 0,
        "emails_extracted": 0
    }
    supabase_consecutive_failures = 0
    
    mode_msg = "Navegador: " + ("Oculto" if headless else "Visual")
    email_msg = " | Extração de email: " + ("Ativada" if extract_emails else "Desativada")
    info.add_log(f"Iniciando: '{search_term}' em {total_cities} cidades", "info")
    info.add_log(mode_msg + email_msg, "info")
    await _broadcast_safe(tm, info, main_loop)

    try:
        async with async_playwright() as p:
            info.add_log("Iniciando navegador...", "info")
            await _broadcast_safe(tm, info, main_loop)
            
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            context = await browser.new_context(
                locale="pt-BR",
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            
            # Remover detecção de automação
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            info.add_log("Navegador iniciado!", "success")
            await _broadcast_safe(tm, info, main_loop)

            # ── PHASE 1: Collect URLs from each city ──
            for i, city in enumerate(cities):
                if info.is_cancelled():
                    break
                # Note: wait_if_paused uses the main event loop's Event,
                # so we check is_cancelled instead in threaded mode
                if not main_loop:
                    await info.wait_if_paused()

                query = f"{search_term} em {city}"
                info.add_log(f"[{i+1}/{total_cities}] Coletando: {city}...", "info")
                info.progress = (i / total_cities) * 30  # 0-30% for collection
                await _broadcast_safe(tm, info, main_loop)

                urls = await collect_urls(page, query, info, tm, main_loop)
                all_urls.extend(urls)
                info.add_log(f"{city}: {len(urls)} URLs", "success")
                await _broadcast_safe(tm, info, main_loop)
                await asyncio.sleep(delay)

            # Deduplicate
            all_urls = list(dict.fromkeys(all_urls))
            info.add_log(f"Total: {len(all_urls)} URLs únicas para extrair", "success")
            await _broadcast_safe(tm, info, main_loop)

            if len(all_urls) == 0:
                info.add_log("Nenhuma URL coletada. Verifique o termo de busca.", "warning")
                await browser.close()
                return

            # ── PHASE 2: Extract details from each URL ──
            info.stats["phase"] = "extracting"
            info.stats["queue"] = len(all_urls)
            total_urls = len(all_urls)

            for j, url in enumerate(all_urls):
                if info.is_cancelled():
                    break
                if not main_loop:
                    await info.wait_if_paused()

                info.add_log(f"Extraindo {j+1}/{total_urls}...", "info")
                data = await extract_place_details(page, url)

                if data.get("nome") and data["nome"] not in ["Erro", "Erro - Timeout"]:
                    info.stats["leads"] += 1
                    
                    # Extract email from website if enabled
                    email_extraido = None
                    if extract_emails and data.get("website") and data["website"] != "Sem Website":
                        info.add_log(f"Extraindo email de {data['website']}...", "info")
                        await _broadcast_safe(tm, info, main_loop)
                        email_extraido = await extract_email_from_website(data["website"], info, tm, main_loop)
                        if email_extraido:
                            info.stats["emails_extracted"] += 1
                            info.add_log(f"✓ Email encontrado: {email_extraido}", "success")
                        else:
                            info.add_log(f"✗ Nenhum email encontrado no site", "warning")
                        await _broadcast_safe(tm, info, main_loop)
                    
                    log_msg = f"✓ {data['nome']} — {data.get('telefone', 'N/A')}"
                    if email_extraido:
                        log_msg += f" — {email_extraido}"
                    info.add_log(log_msg, "success")

                    # Find which city from the URL or address
                    cidade = ""
                    for c in cities:
                        city_name = c.split(",")[0].strip().lower()
                        if city_name in data.get("endereco", "").lower():
                            cidade = c
                            break

                    # Save to Supabase
                    if supabase_client.is_available():
                        try:
                            lead_data = {
                                'nome': data["nome"],
                                'telefone': data.get("telefone", ""),
                                'website': data.get("website", ""),
                                'email': email_extraido or "",  # Add extracted email
                                'endereco': data.get("endereco", ""),
                                'cidade': cidade,
                                'url': url,
                                'conjunto_de_locais': location_set_name,
                                'task_id': info.id
                            }
                            success = await supabase_client.insert_lead(lead_data)
                            if success:
                                info.stats["supabase_success"] += 1
                                supabase_consecutive_failures = 0
                            else:
                                info.stats["supabase_failures"] += 1
                                supabase_consecutive_failures += 1
                                info.add_log(f"⚠️ Supabase: Falha ao salvar '{data['nome']}'", "warning")
                                
                                # Detect 5+ consecutive failures and log warning
                                if supabase_consecutive_failures >= 5:
                                    info.add_log(
                                        f"⚠️ {supabase_consecutive_failures} falhas consecutivas no Supabase",
                                        "error"
                                    )
                        except Exception as e:
                            info.stats["supabase_failures"] += 1
                            supabase_consecutive_failures += 1
                            info.add_log(f"❌ Erro Supabase: {type(e).__name__} - {data['nome']}", "error")
                            
                            # Detect 5+ consecutive failures and log warning
                            if supabase_consecutive_failures >= 5:
                                info.add_log(
                                    f"⚠️ {supabase_consecutive_failures} falhas consecutivas no Supabase",
                                    "error"
                                )
                            # Continue extraction despite Supabase error
                    else:
                        # Supabase unavailable - log warning but continue extraction
                        info.add_log(f"⚠️ Supabase indisponível: '{data['nome']}' não foi salvo", "warning")
                else:
                    info.stats["errors"] += 1
                    error_msg = data.get("error", "Desconhecido")
                    info.add_log(f"✗ Falha: {error_msg}", "error")

                info.stats["done"] = j + 1
                info.stats["queue"] = total_urls - (j + 1)
                info.progress = 30 + ((j + 1) / max(total_urls, 1)) * 70  # 30-100%
                await _broadcast_safe(tm, info, main_loop)

                await asyncio.sleep(delay)

            await browser.close()
            
            # Final log with statistics including Supabase and emails
            final_msg = f"Extração finalizada! {info.stats['leads']} leads extraídos."
            if extract_emails:
                final_msg += f" {info.stats['emails_extracted']} emails encontrados."
            if supabase_client.is_available():
                final_msg += f" Supabase: {info.stats['supabase_success']} sucessos, {info.stats['supabase_failures']} falhas."
            
            info.add_log(final_msg, "success")
            await _broadcast_safe(tm, info, main_loop)
            
    except Exception as e:
        info.add_log(f"Erro fatal: {str(e)}", "error")
        info.status = "failed"
        await _broadcast_safe(tm, info, main_loop)
        raise
