"""
Email Extractor — API Router
Extracts emails from domains using RDAP + page scraping.
"""
import asyncio
import re
from typing import Optional

import httpx
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from database.db import async_session
from database.models import EmailResult
from services.task_manager import task_manager, TaskInfo
from services.csv_exporter import to_csv_bytes

router = APIRouter()

# ── Constants ────────────────────────────────────────────────
SOCIAL_DOMAINS = [
    "instagram.com", "facebook.com", "twitter.com", "linkedin.com",
    "youtube.com", "tiktok.com", "pinterest.com", "snapchat.com",
    "reddit.com", "whatsapp.com", "telegram.me", "vk.com",
]

CONTACT_PATHS = ["", "/contato", "/contact", "/fale-conosco", "/contato/", "/sobre", "/about"]

IGNORE_USERS = ["exemplo", "ex", "email", "seuemail", "nome", "user", "usuario", "teste", "test", "admin", "domain", "contato_exemplo"]
IGNORE_DOMAINS_LIST = ["exemplo.com", "email.com", "teste.com", "dominio.com", "example.com", "domain.com"]
IGNORE_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".js", ".css", ".woff", ".ttf"]

MAX_RETRIES = 5


# ── Helpers ──────────────────────────────────────────────────
def extract_domain(raw: str) -> str:
    """Clean domain from URL or raw input."""
    url = raw.strip()
    if not url:
        return ""
    if not url.startswith("http"):
        url = "http://" + url
    try:
        from urllib.parse import urlparse
        return urlparse(url).hostname or raw.strip()
    except Exception:
        return raw.strip()


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
    if any(sd in domain.lower() for sd in SOCIAL_DOMAINS):
        return None
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


# ── Worker ───────────────────────────────────────────────────
async def email_worker(info: TaskInfo, tm: "TaskManager"):
    """Background worker for email extraction."""
    config = info.config
    domains = config.get("domains", [])
    delay = config.get("delay", 1.0)
    proxy = config.get("proxy", None)

    # Filter duplicates
    domains = list(dict.fromkeys(domains))

    queue = list(domains)
    retry_counts: dict[str, int] = {}
    total_original = len(queue)
    processed = 0  # Track actual processed count

    info.stats = {"queue": len(queue), "done": 0, "leads": 0, "errors": 0}
    await tm.broadcast(info)

    transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
    async with httpx.AsyncClient(transport=transport, verify=False) as client:
        while queue:
            if info.is_cancelled():
                break
            await info.wait_if_paused()

            domain = queue.pop(0)
            processed += 1

            # Skip social domains
            if any(sd in domain.lower() for sd in SOCIAL_DOMAINS):
                info.stats["errors"] += 1
                info.stats["done"] += 1
                info.stats["queue"] = len(queue)
                # Calculate progress based on original total, capped at 100%
                info.progress = min(100, (info.stats["done"] / total_original) * 100)
                await tm.broadcast(info)
                continue

            email = None
            source = ""

            # 1. RDAP
            email = await fetch_rdap_email(domain, client)
            if email:
                source = "RDAP"

            # 2. Page scraping
            if not email:
                email = await fetch_page_email(domain, client)
                if email:
                    source = "Reciclagem"

            if email:
                info.stats["leads"] += 1
                info.add_log(f"✓ {domain} → {email} ({source})", "success")

                # Save to DB
                async with async_session() as session:
                    session.add(EmailResult(
                        domain=domain, email=email, source=source, task_id=info.id
                    ))
                    await session.commit()
            else:
                retries = retry_counts.get(domain, 0) + 1
                retry_counts[domain] = retries
                if retries <= MAX_RETRIES:
                    queue.append(domain)
                else:
                    info.stats["errors"] += 1
                    info.add_log(f"✗ {domain} — sem email", "error")

            info.stats["done"] += 1
            info.stats["queue"] = len(queue)
            # Calculate progress based on original total, capped at 100%
            info.progress = min(100, (info.stats["done"] / total_original) * 100)
            await tm.broadcast(info)

            await asyncio.sleep(delay)


# ── Routes ───────────────────────────────────────────────────
@router.post("/start")
async def start_extraction(
    domains: list[str] = Body(...),
    delay: float = Body(1.0),
    proxy: Optional[str] = Body(None),
):
    """Start email extraction task."""
    clean_domains = [extract_domain(d) for d in domains if d.strip()]
    clean_domains = [d for d in clean_domains if d]

    if not clean_domains:
        return {"error": "No valid domains provided"}

    config = {"domains": clean_domains, "delay": delay, "proxy": proxy}
    task_id = await task_manager.create_task("emails", config, email_worker)
    return {"task_id": task_id, "total": len(clean_domains)}


@router.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get results for a specific task."""
    from sqlalchemy import select
    async with async_session() as session:
        stmt = select(EmailResult).where(EmailResult.task_id == task_id)
        results = (await session.execute(stmt)).scalars().all()
        return [
            {"domain": r.domain, "email": r.email, "source": r.source}
            for r in results
        ]


@router.get("/export/{task_id}")
async def export_results(task_id: str, format: str = "csv"):
    """Export task results as CSV or Excel."""
    from sqlalchemy import select
    async with async_session() as session:
        stmt = select(EmailResult).where(EmailResult.task_id == task_id)
        results = (await session.execute(stmt)).scalars().all()

    rows = [{"Dominio": r.domain, "Email": r.email, "Fonte": r.source} for r in results]
    fields = ["Dominio", "Email", "Fonte"]

    if format == "excel":
        from services.csv_exporter import to_excel_bytes
        content = to_excel_bytes(rows, fields, "Emails")
        return StreamingResponse(
            iter([content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=emails_{task_id}.xlsx"},
        )
    else:
        content = to_csv_bytes(rows, fields)
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=emails_{task_id}.csv"},
        )
