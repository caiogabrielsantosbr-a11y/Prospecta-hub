"""
Facebook ADS Extractor — Playwright Workers
Port of content_script.js + background.js multi-step scraping logic.
Two workers: feed scraping + contact extraction.
"""
import asyncio
import re
import sys
import threading
from urllib.parse import urlparse, parse_qs, unquote
from playwright.async_api import async_playwright, Page

from database.supabase_client import get_supabase_client

# Regex patterns (ported from content_script.js)
PATTERNS = {
    "email": re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+", re.IGNORECASE),
    "phone": re.compile(r"(?:\+?\d{2}\s?)?\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}"),
    "handle": re.compile(r"@[\w\.]+"),
}


def extract_contacts_from_text(text: str, html: str = "") -> dict:
    """Extract emails, phones, and Instagram handles from page text + links."""
    emails = list(set(PATTERNS["email"].findall(text)))
    phones = list(set(PATTERNS["phone"].findall(text)))
    handles = list(set(PATTERNS["handle"].findall(text)))
    instagram = ""

    # Parse links from HTML for mailto, tel, whatsapp, instagram
    for match in re.finditer(r'href="(mailto:[^"]+)"', html, re.IGNORECASE):
        email = match.group(1).replace("mailto:", "").split("?")[0]
        if "@" in email:
            emails.append(email)

    for match in re.finditer(r'href="(tel:[^"]+)"', html, re.IGNORECASE):
        phone = match.group(1).replace("tel:", "").split("?")[0]
        if phone:
            phones.append(phone)

    for match in re.finditer(r'href="[^"]*(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\d+)', html):
        phones.append(match.group(1))

    for match in re.finditer(r'href="[^"]*instagram\.com/([^/?"\s]+)', html):
        handle = f"@{match.group(1)}"
        if handle not in handles:
            handles.append(handle)
        if not instagram:
            instagram = handle

    return {
        "emails": list(set(emails)),
        "phones": list(set(phones)),
        "handles": list(set(handles)),
        "instagram": instagram,
    }


def remove_utms(url: str) -> str:
    """Strip UTM parameters from URL."""
    try:
        parsed = urlparse(url)
        from urllib.parse import urlencode, parse_qs
        params = {k: v[0] for k, v in parse_qs(parsed.query).items() if not k.startswith("utm_")}
        clean = parsed._replace(query=urlencode(params) if params else "")
        return clean.geturl()
    except Exception:
        return url


async def facebook_feed_worker(info, tm):
    """
    Phase 1: Scroll the Facebook Ads Library search results to collect ad cards.
    On Windows, runs in a dedicated thread with its own ProactorEventLoop.
    """
    if sys.platform == 'win32':
        main_loop = asyncio.get_event_loop()
        exception_holder = [None]

        def _run_in_thread():
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_facebook_feed_work(info, tm, main_loop))
            except Exception as e:
                exception_holder[0] = e
            finally:
                loop.close()

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        while thread.is_alive():
            await asyncio.sleep(0.5)
        thread.join()
        if exception_holder[0]:
            raise exception_holder[0]
    else:
        await _facebook_feed_work(info, tm)


async def _broadcast_safe(tm, info, main_loop=None):
    """Broadcast task update, safely from any thread."""
    if main_loop and main_loop != asyncio.get_event_loop():
        future = asyncio.run_coroutine_threadsafe(tm.broadcast(info), main_loop)
        future.result(timeout=5)
    else:
        await tm.broadcast(info)


async def _facebook_feed_work(info, tm, main_loop=None):
    """
    Core Feed scraping logic.
    """
    config = info.config
    keyword = config.get("keyword", "")
    delay = config.get("delay", 3000) / 1000

    info.stats = {"queue": 0, "done": 0, "leads": 0, "errors": 0}
    info.add_log(f"Buscando feed: '{keyword}'", "info")
    await _broadcast_safe(tm, info, main_loop)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = await context.new_page()

        # Navigate to Ads Library
        ads_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&q={keyword}&search_type=keyword_unordered&media_type=all"
        await page.goto(ads_url, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        seen_ads = set()
        no_new_attempts = 0
        max_no_new = 10

        while not info.is_cancelled() and no_new_attempts < max_no_new:
            if not main_loop:
                await info.wait_if_paused()

            # Scroll
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(delay)

            # Scrape cards using JavaScript (port of scrapeCards)
            found_items = await page.evaluate("""
                (() => {
                    const results = [];
                    // Find links to Facebook pages that also have ad links
                    const allLinks = document.querySelectorAll('a[href*="facebook.com/"]');
                    const pageLinks = new Map();

                    for (const link of allLinks) {
                        const href = link.href;
                        if (!href.includes('/ads/library') && !href.includes('l.facebook.com')) {
                            const name = link.innerText?.trim();
                            if (name && name.length > 1 && name.length < 100) {
                                const page = href.split('?')[0];
                                if (!pageLinks.has(page)) {
                                    pageLinks.set(page, name);
                                }
                            }
                        }
                    }

                    // Find ad destination links
                    const adLinks = document.querySelectorAll('a[href*="l.facebook.com/l.php?u="]');
                    for (const adLink of adLinks) {
                        try {
                            const raw = adLink.href;
                            const u = new URL(raw).searchParams.get("u");
                            const adUrl = u ? decodeURIComponent(u) : raw;

                            // Find closest page link
                            const card = adLink.closest('div[class]');
                            if (card) {
                                const pageLinkEl = card.querySelector('a[href*="facebook.com/"]:not([href*="ads/library"]):not([href*="l.facebook.com"])');
                                if (pageLinkEl) {
                                    const name = pageLinkEl.innerText?.trim();
                                    const pageUrl = pageLinkEl.href.split('?')[0];
                                    results.push({ name: name || '', page: pageUrl, ad: adUrl });
                                }
                            }
                        } catch(e) {}
                    }

                    return results;
                })()
            """)

            new_count = 0
            for item in found_items:
                key = f"{item['page']}::{item['ad']}"
                if key not in seen_ads:
                    seen_ads.add(key)
                    new_count += 1
                    ad_url = remove_utms(item["ad"])

                    # Save to Supabase
                    supabase = get_supabase_client()
                    lead_data = {
                        'name': item["name"],
                        'page_url': item["page"],
                        'ad_url': ad_url,
                        'task_id': info.id,
                    }
                    await supabase.insert_facebook_lead(lead_data)

                    info.stats["leads"] += 1

            if new_count > 0:
                no_new_attempts = 0
                info.add_log(f"+{new_count} anúncios ({len(seen_ads)} total)", "success")
            else:
                no_new_attempts += 1
                # Try clicking "Ver mais" / "See more"
                try:
                    see_more = await page.query_selector("text=Ver mais")
                    if not see_more:
                        see_more = await page.query_selector("text=See more results")
                    if see_more:
                        await see_more.click()
                        await asyncio.sleep(2)
                        no_new_attempts = 0
                except Exception:
                    pass

            info.stats["done"] = len(seen_ads)
            info.progress = min(90, len(seen_ads) * 2)  # Approximate
            await _broadcast_safe(tm, info, main_loop)

        await browser.close()

    info.add_log(f"Feed finalizado! {info.stats['leads']} anúncios coletados.", "success")


async def facebook_contacts_worker(info, tm):
    """
    Phase 2: Visit each ad page/profile to extract contact info.
    On Windows, runs in a dedicated thread with its own ProactorEventLoop.
    """
    if sys.platform == 'win32':
        main_loop = asyncio.get_event_loop()
        exception_holder = [None]

        def _run_in_thread():
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_facebook_contacts_work(info, tm, main_loop))
            except Exception as e:
                exception_holder[0] = e
            finally:
                loop.close()

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()
        while thread.is_alive():
            await asyncio.sleep(0.5)
        thread.join()
        if exception_holder[0]:
            raise exception_holder[0]
    else:
        await _facebook_contacts_work(info, tm)


async def _facebook_contacts_work(info, tm, main_loop=None):
    """
    Core Contacts extraction logic.
    """
    config = info.config
    delay = config.get("delay", 2000) / 1000

    # Get unprocessed leads from Supabase
    supabase = get_supabase_client()
    all_leads = await supabase.get_facebook_leads_by_task(info.id)
    
    # Filter for leads without contact info (emails is None)
    leads = [lead for lead in all_leads if not lead.get('emails')]

    total = len(leads)
    if total == 0:
        info.add_log("Nenhum lead para processar. Execute o Feed primeiro.", "warning")
        await _broadcast_safe(tm, info, main_loop)
        return

    info.stats = {"queue": total, "done": 0, "leads": 0, "errors": 0}
    info.add_log(f"Processando {total} leads...", "info")
    await _broadcast_safe(tm, info, main_loop)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        for i, lead in enumerate(leads):
            if info.is_cancelled():
                break
            if not main_loop:
                await info.wait_if_paused()

            all_contacts = {"emails": [], "phones": [], "instagram": ""}
            page_id = lead.get('page_id')  # Get existing page_id

            # Step 1: Visit landing page (ad URL) for contact info
            if lead.get('ad_url'):
                try:
                    await page.goto(lead['ad_url'], wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)

                    text = await page.evaluate("document.body.innerText")
                    html = await page.evaluate("document.body.innerHTML")
                    contacts = extract_contacts_from_text(text, html)

                    all_contacts["emails"].extend(contacts["emails"])
                    all_contacts["phones"].extend(contacts["phones"])
                    if contacts["instagram"]:
                        all_contacts["instagram"] = contacts["instagram"]
                except Exception:
                    pass

            # Step 2: Visit Facebook page
            if lead.get('page_url'):
                try:
                    await page.goto(lead['page_url'], wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)

                    text = await page.evaluate("document.body.innerText")
                    html = await page.evaluate("document.body.innerHTML")
                    contacts = extract_contacts_from_text(text, html)

                    all_contacts["emails"].extend(contacts["emails"])
                    all_contacts["phones"].extend(contacts["phones"])
                    if not all_contacts["instagram"] and contacts["instagram"]:
                        all_contacts["instagram"] = contacts["instagram"]

                    # Try to find Page ID from transparency
                    page_id_match = re.search(r"\d{10,20}", text)
                    if page_id_match:
                        page_id = page_id_match.group(0)
                except Exception:
                    pass

            # Deduplicate
            has_data = all_contacts["emails"] or all_contacts["phones"] or all_contacts["instagram"]
            emails_str = "; ".join(set(all_contacts["emails"])) if all_contacts["emails"] else None
            phones_str = "; ".join(set(all_contacts["phones"])) if all_contacts["phones"] else None

            # Update Supabase
            supabase = get_supabase_client()
            await supabase.update_facebook_lead_contacts(
                id=lead['id'],
                emails=emails_str,
                phones=phones_str,
                instagram=all_contacts["instagram"] or None
            )

            if has_data:
                info.stats["leads"] += 1
                info.add_log(f"✓ {lead['name']}: {emails_str or phones_str or all_contacts['instagram']}", "success")
            else:
                info.stats["errors"] += 1
                info.add_log(f"✗ {lead['name']}: sem contato", "error")

            info.stats["done"] = i + 1
            info.stats["queue"] = total - (i + 1)
            info.progress = ((i + 1) / total) * 100
            await _broadcast_safe(tm, info, main_loop)

            await asyncio.sleep(delay)

        await browser.close()

    info.add_log(f"Contatos finalizados! {info.stats['leads']} com dados.", "success")
