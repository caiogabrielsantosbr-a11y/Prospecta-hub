"""
Google Maps Extractor — API Router
Uses Playwright to scrape business data from Google Maps.
"""
import json
import os
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query
from services.task_manager import task_manager, TaskInfo
from modules.gmap.worker import gmap_worker
from database.supabase_client import get_supabase_client
from middleware.auth import get_optional_user

router = APIRouter()

def get_progress_file(user_id: Optional[str]) -> str:
    uid = user_id if user_id else "anonymous"
    # Ensure safe filename
    uid = "".join(c for c in uid if c.isalnum() or c in ('-', '_'))
    return f"backend/data/gmap_progress_{uid}.json"


def load_progress(user_id: Optional[str]):
    """Load progress from JSON file for specific user"""
    file_path = get_progress_file(user_id)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading progress: {e}")
    return {"completed_cities": {}}


def save_progress(progress, user_id: Optional[str]):
    """Save progress to JSON file for specific user"""
    file_path = get_progress_file(user_id)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving progress: {e}")


@router.get("/progress")
async def get_progress(user_id: Optional[str] = Depends(get_optional_user)):
    """Get extraction progress for all cities"""
    return load_progress(user_id)


@router.post("/progress/mark-completed")
async def mark_city_completed(
    location_set: str = Body(...),
    city: str = Body(...),
    user_id: Optional[str] = Depends(get_optional_user)
):
    """Mark a city as completed"""
    progress = load_progress(user_id)
    city_key = f"{location_set}:{city}"
    progress["completed_cities"][city_key] = True
    save_progress(progress, user_id)
    return {"success": True, "city_key": city_key}


@router.post("/progress/reset")
async def reset_progress(user_id: Optional[str] = Depends(get_optional_user)):
    """Reset all progress"""
    progress = {"completed_cities": {}}
    save_progress(progress, user_id)
    return {"success": True, "message": "Progress reset"}


@router.post("/start")
async def start_gmap(
    searchTerm: str = Body(...),
    cities: list[str] = Body(...),
    delay: int = Body(2000),
    headless: bool = Body(True),
    extractEmails: bool = Body(True),
    user_id: Optional[str] = Depends(get_optional_user),
):
    config = {
        "searchTerm": searchTerm,
        "cities": cities,
        "delay": delay,
        "headless": headless,
        "extractEmails": extractEmails,
        "user_id": user_id,
    }
    task_id = await task_manager.create_task("gmap", config, gmap_worker)
    return {"task_id": task_id, "total": len(cities)}


@router.get("/results/{task_id}")
async def get_gmap_results(
    task_id: str,
    limit: int = Query(default=100, ge=1, description="Maximum number of leads to return"),
    offset: int = Query(default=0, ge=0, description="Number of leads to skip for pagination")
):
    """
    Query leads from Supabase by task_id with pagination support.
    
    Args:
        task_id: The task ID to filter leads by
        limit: Maximum number of leads to return (default: 100, minimum: 1)
        offset: Number of leads to skip for pagination (default: 0, minimum: 0)
    
    Returns:
        List of lead dictionaries with all fields, or empty list if none found
    """
    supabase_client = get_supabase_client()
    
    # Check if Supabase integration is available
    if not supabase_client.is_available():
        return {
            "error": "Supabase integration is not available",
            "message": "Please check SUPABASE_URL and SUPABASE_KEY environment variables",
            "results": []
        }
    
    # Query leads from Supabase
    leads = await supabase_client.get_leads_by_task(task_id, limit=limit, offset=offset)
    
    # Return results in the same format as before (maintaining backward compatibility)
    return [
        {
            "nome": lead.get("nome"),
            "telefone": lead.get("telefone"),
            "website": lead.get("website"),
            "endereco": lead.get("endereco"),
            "cidade": lead.get("cidade")
        }
        for lead in leads
    ]


@router.get("/supabase/results/{task_id}")
async def get_supabase_results(
    task_id: str,
    limit: int = Query(default=100, ge=1, description="Maximum number of leads to return"),
    offset: int = Query(default=0, ge=0, description="Number of leads to skip for pagination")
):
    """
    Query leads from Supabase by task_id with pagination support.
    
    Args:
        task_id: The task ID to filter leads by
        limit: Maximum number of leads to return (default: 100, minimum: 1)
        offset: Number of leads to skip for pagination (default: 0, minimum: 0)
    
    Returns:
        List of lead dictionaries with all fields, or empty list if none found
    """
    supabase_client = get_supabase_client()
    
    # Check if Supabase integration is available
    if not supabase_client.is_available():
        return {
            "error": "Supabase integration is not available",
            "message": "Please check SUPABASE_URL and SUPABASE_KEY environment variables",
            "results": []
        }
    
    # Query leads from Supabase
    leads = await supabase_client.get_leads_by_task(task_id, limit=limit, offset=offset)
    
    # Return results (empty list if none found, status 200)
    return leads

