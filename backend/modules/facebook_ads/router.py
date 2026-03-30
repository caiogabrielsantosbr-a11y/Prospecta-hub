"""
Facebook ADS Extractor — API Router
Uses Playwright to scrape the Facebook Ads Library.
"""
from fastapi import APIRouter, Body
from services.task_manager import task_manager
from modules.facebook_ads.worker import facebook_feed_worker, facebook_contacts_worker

router = APIRouter()


@router.post("/start-feed")
async def start_feed(keyword: str = Body(...), delay: int = Body(2000)):
    config = {"keyword": keyword, "delay": delay, "mode": "feed"}
    task_id = await task_manager.create_task("facebook_feed", config, facebook_feed_worker)
    return {"task_id": task_id}


@router.post("/start-contacts")
async def start_contacts(delay: int = Body(2000)):
    config = {"delay": delay, "mode": "contacts"}
    task_id = await task_manager.create_task("facebook_contacts", config, facebook_contacts_worker)
    return {"task_id": task_id}


@router.get("/results/{task_id}")
async def get_facebook_results(task_id: str):
    from sqlalchemy import select
    from database.db import async_session
    from database.models import FacebookAdsLead
    async with async_session() as session:
        stmt = select(FacebookAdsLead).where(FacebookAdsLead.task_id == task_id)
        results = (await session.execute(stmt)).scalars().all()
        return [
            {"name": r.name, "page_url": r.page_url, "ad_url": r.ad_url,
             "page_id": r.page_id, "emails": r.emails, "phones": r.phones,
             "instagram": r.instagram}
            for r in results
        ]
