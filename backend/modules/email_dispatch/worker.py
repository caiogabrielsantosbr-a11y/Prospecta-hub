"""
Email Dispatch Service — Send emails via SMTP or API.
Processes a spreadsheet of recipients and tracks sent status.
"""
import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from database.db import async_session
from database.models import EmailDispatch


class EmailSender:
    """SMTP email sender with retry and tracking."""

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", 587))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Prospecting Hub")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.user)

    def is_configured(self) -> bool:
        return bool(self.user and self.password and self.host)

    async def send_email(self, to: str, subject: str, body_html: str) -> dict:
        """Send a single email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to

            # Plain text fallback
            import re
            plain = re.sub(r"<[^>]+>", "", body_html)
            msg.attach(MIMEText(plain, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            # Run SMTP in thread to not block event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._smtp_send, to, msg)

            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _smtp_send(self, to: str, msg: MIMEMultipart):
        """Blocking SMTP send (run in executor)."""
        with smtplib.SMTP(self.host, self.port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.user, self.password)
            server.sendmail(self.from_email, to, msg.as_string())


async def dispatch_worker(info, tm):
    """
    Background worker for email dispatch.
    Processes a list of recipients, sends personalized emails,
    and tracks status in the database.
    """
    config = info.config
    recipients = config.get("recipients", [])  # [{email, name, ...}]
    subject = config.get("subject", "")
    template = config.get("template", "")  # HTML with {{nome}}, {{email}} placeholders
    delay = config.get("delay", 5)  # seconds between emails

    sender = EmailSender()
    if not sender.is_configured():
        info.add_log("❌ SMTP não configurado! Verifique o .env", "error")
        info.status = "failed"
        return

    total = len(recipients)
    info.stats = {"total": total, "sent": 0, "failed": 0, "pending": total}
    info.add_log(f"Disparo iniciado: {total} destinatários", "info")
    info.add_log(f"SMTP: {sender.host}:{sender.port}", "info")
    await tm.broadcast(info)

    for i, recipient in enumerate(recipients):
        if info.is_cancelled():
            break
        await info.wait_if_paused()

        email = recipient.get("email", "")
        name = recipient.get("name", email.split("@")[0])

        if not email or "@" not in email:
            info.stats["failed"] += 1
            info.add_log(f"✗ Email inválido: {email}", "error")
            continue

        # Personalize template
        body = template.replace("{{nome}}", name).replace("{{email}}", email)
        personalized_subject = subject.replace("{{nome}}", name)

        result = await sender.send_email(email, personalized_subject, body)

        # Save to DB
        async with async_session() as session:
            session.add(EmailDispatch(
                recipient_email=email,
                recipient_name=name,
                subject=personalized_subject,
                status="sent" if result["success"] else "failed",
                error_detail=result.get("error"),
                task_id=info.id,
            ))
            await session.commit()

        if result["success"]:
            info.stats["sent"] += 1
            info.add_log(f"✓ Enviado: {email}", "success")
        else:
            info.stats["failed"] += 1
            info.add_log(f"✗ Falha: {email} — {result['error']}", "error")

        info.stats["pending"] = total - (i + 1)
        info.progress = ((i + 1) / total) * 100
        await tm.broadcast(info)

        if i < total - 1:
            await asyncio.sleep(delay)

    info.add_log(f"Disparo finalizado! {info.stats['sent']}/{total} enviados.", "success")
