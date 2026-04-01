"""
Gmail Integration Router
OAuth2 + Gmail API via httpx (zero extra dependencies)
"""
import os
import json
import base64
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode, quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from middleware.auth import get_current_user

router = APIRouter()

# ── Constants ────────────────────────────────────────────────
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_BASE       = "https://gmail.googleapis.com/gmail/v1"
GEMINI_URL       = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

GMAIL_SCOPES = " ".join([
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
])

SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY         = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY", ""))
GMAIL_CLIENT_ID      = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET  = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REDIRECT_URI   = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY", "")


# ── Supabase helpers ─────────────────────────────────────────

def sb_headers(service: bool = False):
    key = SUPABASE_SERVICE_KEY if service else SUPABASE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


async def sb_get(table: str, params: dict, service: bool = False) -> list:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/{table}", params=params, headers=sb_headers(service))
        r.raise_for_status()
        return r.json()


async def sb_insert(table: str, data: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{SUPABASE_URL}/rest/v1/{table}", json=data, headers=sb_headers(service=True))
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else {}


async def sb_update(table: str, match: dict, data: dict) -> None:
    params = {k: f"eq.{v}" for k, v in match.items()}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.patch(f"{SUPABASE_URL}/rest/v1/{table}", params=params, json=data, headers=sb_headers(service=True))
        r.raise_for_status()


async def sb_delete(table: str, match: dict) -> None:
    params = {k: f"eq.{v}" for k, v in match.items()}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.delete(f"{SUPABASE_URL}/rest/v1/{table}", params=params, headers=sb_headers(service=True))
        r.raise_for_status()


# ── Token helpers ────────────────────────────────────────────

async def _refresh_access_token(account: dict) -> str:
    """Exchange refresh_token for a new access_token and update Supabase."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(GOOGLE_TOKEN_URL, data={
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "refresh_token": account["refresh_token"],
            "grant_type": "refresh_token",
        })
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to refresh Gmail token. Please reconnect the account.")
        data = r.json()

    new_token  = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    expiry     = datetime.now(timezone.utc).isoformat()

    await sb_update("gmail_accounts", {"id": account["id"]}, {
        "access_token": new_token,
        "token_expiry": expiry,
    })
    return new_token


async def get_valid_token(account: dict) -> str:
    """Return a valid access_token, refreshing if needed."""
    expiry = account.get("token_expiry")
    if expiry:
        try:
            exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (exp_dt - now).total_seconds() > 300:
                return account["access_token"]
        except Exception:
            pass
    return await _refresh_access_token(account)


async def get_account(account_id: str, user_id: str) -> dict:
    """Fetch and validate a gmail_account belonging to the user."""
    rows = await sb_get("gmail_accounts", {"id": f"eq.{account_id}", "user_id": f"eq.{user_id}"})
    if not rows:
        raise HTTPException(status_code=404, detail="Account not found")
    return rows[0]


# ── Gmail API helpers ────────────────────────────────────────

def _decode_part(part: dict) -> str:
    """Decode base64url encoded email body part."""
    data = part.get("body", {}).get("data", "")
    if not data:
        return ""
    padded = data.replace("-", "+").replace("_", "/")
    padded += "=" * (4 - len(padded) % 4)
    try:
        return base64.b64decode(padded).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_body(payload: dict) -> dict:
    """Recursively extract text/plain and text/html from Gmail message payload."""
    mime = payload.get("mimeType", "")
    result = {"text": "", "html": ""}

    if mime == "text/plain":
        result["text"] = _decode_part(payload)
    elif mime == "text/html":
        result["html"] = _decode_part(payload)
    elif "parts" in payload:
        for part in payload["parts"]:
            sub = _extract_body(part)
            if sub["text"]:
                result["text"] = sub["text"]
            if sub["html"]:
                result["html"] = sub["html"]
    return result


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _make_reply_raw(to: str, subject: str, body_html: str, thread_id: str,
                    message_id_header: str, sender_name: str = "") -> str:
    """Build RFC 2822 reply and return base64url encoded raw string."""
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    msg["In-Reply-To"] = message_id_header
    msg["References"] = message_id_header

    part_html = MIMEText(body_html, "html", "utf-8")
    msg.attach(part_html)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return raw


# ── ENDPOINTS ────────────────────────────────────────────────

@router.get("/auth-url")
async def get_auth_url(user_id: str = Depends(get_current_user)):
    """Return Google OAuth2 authorization URL."""
    if not GMAIL_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GMAIL_CLIENT_ID not configured in backend .env")

    params = {
        "client_id": GMAIL_CLIENT_ID,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": GMAIL_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id,
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"url": url}


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(code: str, state: str):
    """
    Receive OAuth2 code from Google, exchange for tokens, save to Supabase.
    state = user_id passed through the OAuth flow.
    Returns HTML that closes the popup and notifies the opener.
    """
    user_id = state

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "redirect_uri": GMAIL_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if r.status_code != 200:
            return HTMLResponse(content=_popup_html(False, "Falha ao obter tokens do Google: " + r.text), status_code=400)
        tokens = r.json()

    access_token  = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in    = tokens.get("expires_in", 3600)

    if not refresh_token:
        return HTMLResponse(content=_popup_html(False, "Google não retornou refresh_token. Revogue o acesso em myaccount.google.com e tente novamente."), status_code=400)

    # Get Gmail email address
    async with httpx.AsyncClient(timeout=15) as c:
        profile_r = await c.get(
            f"{GMAIL_BASE}/users/me/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if profile_r.status_code != 200:
            return HTMLResponse(content=_popup_html(False, "Falha ao obter perfil do Gmail"), status_code=400)
        gmail_email = profile_r.json().get("emailAddress", "")

    # Upsert into gmail_accounts
    existing = await sb_get("gmail_accounts", {"user_id": f"eq.{user_id}", "email": f"eq.{gmail_email}"})
    expiry = datetime.now(timezone.utc).isoformat()

    if existing:
        await sb_update("gmail_accounts", {"id": existing[0]["id"]}, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": expiry,
            "active": True,
        })
    else:
        await sb_insert("gmail_accounts", {
            "user_id": user_id,
            "email": gmail_email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": expiry,
            "active": True,
        })

    return HTMLResponse(content=_popup_html(True, gmail_email))


def _popup_html(success: bool, message: str) -> str:
    if success:
        return f"""<!DOCTYPE html><html><body>
<script>
  if (window.opener) {{
    window.opener.postMessage({{type:'gmail_connected', email:'{message}'}}, '*');
  }}
  window.close();
</script>
<p>Conta <strong>{message}</strong> conectada! Esta janela vai fechar automaticamente.</p>
</body></html>"""
    else:
        return f"""<!DOCTYPE html><html><body>
<script>
  if (window.opener) {{
    window.opener.postMessage({{type:'gmail_error', error:'{message}'}}, '*');
  }}
  setTimeout(() => window.close(), 4000);
</script>
<p style="color:red">Erro: {message}</p>
</body></html>"""


@router.get("/accounts")
async def list_accounts(user_id: str = Depends(get_current_user)):
    """List all Gmail accounts connected by the user."""
    rows = await sb_get("gmail_accounts", {
        "user_id": f"eq.{user_id}",
        "select": "id,email,active,created_at",
        "order": "created_at.asc",
    })
    return rows


@router.delete("/accounts/{account_id}")
async def disconnect_account(account_id: str, user_id: str = Depends(get_current_user)):
    """Disconnect (delete) a Gmail account."""
    rows = await sb_get("gmail_accounts", {"id": f"eq.{account_id}", "user_id": f"eq.{user_id}"})
    if not rows:
        raise HTTPException(status_code=404, detail="Account not found")
    await sb_delete("gmail_accounts", {"id": account_id})
    return {"success": True}


@router.get("/messages")
async def list_messages(
    account_id: str,
    filter: str = Query("all"),   # all | unread | replied | week | attachment
    search: str = Query(""),
    page_token: str = Query(""),
    user_id: str = Depends(get_current_user),
):
    """List inbox emails for a connected Gmail account."""
    account = await get_account(account_id, user_id)
    token   = await get_valid_token(account)

    # Build Gmail query
    q_parts = ["in:inbox"]
    if filter == "unread":
        q_parts.append("is:unread")
    elif filter == "replied":
        q_parts.append("label:sent")
    elif filter == "week":
        q_parts.append("newer_than:7d")
    elif filter == "attachment":
        q_parts.append("has:attachment")
    if search:
        q_parts.append(search)
    q = " ".join(q_parts)

    params = {"maxResults": "20", "q": q}
    if page_token:
        params["pageToken"] = page_token

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{GMAIL_BASE}/users/me/messages",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Gmail API error: " + r.text)
        data = r.json()

    message_ids = [m["id"] for m in data.get("messages", [])]
    next_page   = data.get("nextPageToken", "")

    if not message_ids:
        return {"messages": [], "nextPageToken": ""}

    # Fetch metadata for each message (format=metadata is lighter)
    async with httpx.AsyncClient(timeout=30) as c:
        tasks = [
            c.get(
                f"{GMAIL_BASE}/users/me/messages/{mid}",
                params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date", "To"]},
                headers={"Authorization": f"Bearer {token}"},
            )
            for mid in message_ids
        ]
        import asyncio
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    messages = []
    for resp in responses:
        if isinstance(resp, Exception):
            continue
        if resp.status_code != 200:
            continue
        msg = resp.json()
        hdrs = msg.get("payload", {}).get("headers", [])
        messages.append({
            "id":        msg["id"],
            "thread_id": msg.get("threadId", ""),
            "from":      _get_header(hdrs, "From"),
            "subject":   _get_header(hdrs, "Subject"),
            "date":      _get_header(hdrs, "Date"),
            "to":        _get_header(hdrs, "To"),
            "snippet":   msg.get("snippet", ""),
            "unread":    "UNREAD" in msg.get("labelIds", []),
        })

    return {"messages": messages, "nextPageToken": next_page}


@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    account_id: str,
    user_id: str = Depends(get_current_user),
):
    """Fetch full email content (body HTML/text + headers)."""
    account = await get_account(account_id, user_id)
    token   = await get_valid_token(account)

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{GMAIL_BASE}/users/me/messages/{message_id}",
            params={"format": "full"},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Gmail API error: " + r.text)
        msg = r.json()

    payload = msg.get("payload", {})
    hdrs    = payload.get("headers", [])
    body    = _extract_body(payload)

    # Mark as read
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(
                f"{GMAIL_BASE}/users/me/messages/{message_id}/modify",
                json={"removeLabelIds": ["UNREAD"]},
                headers={"Authorization": f"Bearer {token}"},
            )
    except Exception:
        pass

    return {
        "id":           message_id,
        "thread_id":    msg.get("threadId", ""),
        "from":         _get_header(hdrs, "From"),
        "to":           _get_header(hdrs, "To"),
        "subject":      _get_header(hdrs, "Subject"),
        "date":         _get_header(hdrs, "Date"),
        "message_id_header": _get_header(hdrs, "Message-ID"),
        "body_html":    body["html"],
        "body_text":    body["text"],
        "snippet":      msg.get("snippet", ""),
    }


class ReplyRequest(BaseModel):
    account_id: str
    message_id: str
    thread_id: str
    to: str
    subject: str
    body: str


@router.post("/reply")
async def reply_email(req: ReplyRequest, user_id: str = Depends(get_current_user)):
    """Send a reply to an email thread."""
    account = await get_account(req.account_id, user_id)
    token   = await get_valid_token(account)

    # Fetch original message-id header for threading
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            f"{GMAIL_BASE}/users/me/messages/{req.message_id}",
            params={"format": "metadata", "metadataHeaders": ["Message-ID"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        orig_hdrs = r.json().get("payload", {}).get("headers", []) if r.status_code == 200 else []
    message_id_header = _get_header(orig_hdrs, "Message-ID")

    raw = _make_reply_raw(
        to=req.to,
        subject=req.subject,
        body_html=req.body,
        thread_id=req.thread_id,
        message_id_header=message_id_header,
    )

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{GMAIL_BASE}/users/me/messages/send",
            json={"raw": raw, "threadId": req.thread_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=r.status_code, detail="Failed to send reply: " + r.text)

    return {"success": True, "message_id": r.json().get("id")}


class ClassifyRequest(BaseModel):
    account_id: str
    message_id: str


@router.post("/classify")
async def classify_email(req: ClassifyRequest, user_id: str = Depends(get_current_user)):
    """
    Classify an email using Gemini 1.5 Flash (free tier).
    Returns: {label, confidence, reason}
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured in backend .env")

    account = await get_account(req.account_id, user_id)
    token   = await get_valid_token(account)

    # Fetch email content
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{GMAIL_BASE}/users/me/messages/{req.message_id}",
            params={"format": "full"},
            headers={"Authorization": f"Bearer {token}"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Failed to fetch email")
        msg = r.json()

    payload  = msg.get("payload", {})
    hdrs     = payload.get("headers", [])
    subject  = _get_header(hdrs, "Subject")
    body_obj = _extract_body(payload)
    body     = body_obj["text"] or body_obj["html"] or msg.get("snippet", "")
    body     = body[:2000]  # Limit for API

    prompt = f"""Você é um assistente de prospecção comercial brasileiro.
Classifique este email de resposta a uma proposta de prospecção:

Assunto: {subject}
Corpo: {body}

Responda APENAS com um JSON válido, sem markdown, sem explicações adicionais:
{{"label": "Interesse"|"Sem interesse"|"Pergunta"|"Irrelevante"|"Aguardar", "confidence": 0-100, "reason": "motivo em 1 frase"}}"""

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200},
            },
        )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Gemini API error: " + r.text)

    try:
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip markdown code block if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse Gemini response: {e}")


# ── Email Templates ──────────────────────────────────────────

@router.get("/templates")
async def list_templates(user_id: str = Depends(get_current_user)):
    rows = await sb_get("email_templates", {
        "user_id": f"eq.{user_id}",
        "select": "*",
        "order": "created_at.desc",
    })
    return rows


class TemplateRequest(BaseModel):
    name: str
    subject: str
    body: str


@router.post("/templates")
async def create_template(req: TemplateRequest, user_id: str = Depends(get_current_user)):
    row = await sb_insert("email_templates", {
        "user_id": user_id,
        "name": req.name,
        "subject": req.subject,
        "body": req.body,
    })
    return row


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, user_id: str = Depends(get_current_user)):
    rows = await sb_get("email_templates", {"id": f"eq.{template_id}", "user_id": f"eq.{user_id}"})
    if not rows:
        raise HTTPException(status_code=404, detail="Template not found")
    await sb_delete("email_templates", {"id": template_id})
    return {"success": True}
