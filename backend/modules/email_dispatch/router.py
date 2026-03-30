"""
Email Dispatch — API Router
Send bulk emails via SMTP with template personalization.
"""
from typing import Optional
from fastapi import APIRouter, Body
from services.task_manager import task_manager
from modules.email_dispatch.worker import dispatch_worker

router = APIRouter()


@router.post("/start")
async def start_dispatch(
    recipients: list[dict] = Body(...),
    subject: str = Body(...),
    template: str = Body(...),
    delay: int = Body(5),
):
    """Start email dispatch.
    recipients: [{email, name}]
    template: HTML string with {{nome}} and {{email}} placeholders
    """
    config = {
        "recipients": recipients,
        "subject": subject,
        "template": template,
        "delay": delay,
    }
    task_id = await task_manager.create_task("email_dispatch", config, dispatch_worker)
    return {"task_id": task_id, "total": len(recipients)}


@router.get("/results/{task_id}")
async def get_dispatch_results(task_id: str):
    from sqlalchemy import select
    from database.db import async_session
    from database.models import EmailDispatch
    async with async_session() as session:
        stmt = select(EmailDispatch).where(EmailDispatch.task_id == task_id)
        results = (await session.execute(stmt)).scalars().all()
        return [
            {
                "email": r.recipient_email,
                "name": r.recipient_name,
                "subject": r.subject,
                "status": r.status,
                "error": r.error_detail,
            }
            for r in results
        ]
