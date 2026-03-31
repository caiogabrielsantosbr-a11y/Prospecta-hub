"""
Leads API Router - User-specific lead management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from middleware.auth import get_current_user
import httpx
import os

router = APIRouter()

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')


@router.get("/api/leads")
async def get_leads(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    conjunto: Optional[str] = None,
    cidade: Optional[str] = None,
    search: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """
    Get leads for the authenticated user with filters and pagination
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build query parameters
            params = {
                'user_id': f'eq.{user_id}',
                'select': '*',
                'order': 'created_at.desc',
                'limit': str(limit),
                'offset': str(offset)
            }
            
            # Add filters
            if conjunto:
                params['conjunto_de_locais'] = f'eq.{conjunto}'
            if cidade:
                params['cidade'] = f'eq.{cidade}'
            if search:
                params['or'] = f'(nome.ilike.%{search}%,telefone.ilike.%{search}%,website.ilike.%{search}%)'
            
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params=params,
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch leads: {response.text}"
                )
            
            leads = response.json()
            
            # Get total count
            count_params = {
                'user_id': f'eq.{user_id}',
                'select': 'count'
            }
            if conjunto:
                count_params['conjunto_de_locais'] = f'eq.{conjunto}'
            if cidade:
                count_params['cidade'] = f'eq.{cidade}'
            if search:
                count_params['or'] = f'(nome.ilike.%{search}%,telefone.ilike.%{search}%,website.ilike.%{search}%)'
            
            count_response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params=count_params,
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json',
                    'Prefer': 'count=exact'
                }
            )
            
            total = int(count_response.headers.get('Content-Range', '0').split('/')[-1])
            
            return {
                'leads': leads,
                'total': total
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/leads/stats")
async def get_leads_stats(
    user_id: str = Depends(get_current_user)
):
    """
    Get statistics for user's leads
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get all leads for user
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params={
                    'user_id': f'eq.{user_id}',
                    'select': 'telefone,email,website'
                },
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch leads: {response.text}"
                )
            
            leads = response.json()
            
            # Calculate stats
            total = len(leads)
            with_phone = sum(1 for l in leads if l.get('telefone') and l['telefone'] != 'Sem Telefone')
            with_email = sum(1 for l in leads if l.get('email'))
            with_website = sum(1 for l in leads if l.get('website') and l['website'] != 'Sem Website')
            
            return {
                'total': total,
                'with_phone': with_phone,
                'with_email': with_email,
                'with_website': with_website,
                'without_phone': total - with_phone,
                'without_website': total - with_website
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/leads/conjuntos")
async def get_conjuntos(
    user_id: str = Depends(get_current_user)
):
    """
    Get unique conjunto_de_locais values for user's leads
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params={
                    'user_id': f'eq.{user_id}',
                    'select': 'conjunto_de_locais'
                },
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch conjuntos: {response.text}"
                )
            
            leads = response.json()
            conjuntos = sorted(set(l['conjunto_de_locais'] for l in leads if l.get('conjunto_de_locais')))
            
            return {'conjuntos': conjuntos}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/leads/cidades")
async def get_cidades(
    conjunto: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get unique cidade values for a specific conjunto for user's leads
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params={
                    'user_id': f'eq.{user_id}',
                    'conjunto_de_locais': f'eq.{conjunto}',
                    'select': 'cidade'
                },
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch cidades: {response.text}"
                )
            
            leads = response.json()
            cidades = sorted(set(l['cidade'] for l in leads if l.get('cidade')))
            
            return {'cidades': cidades}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/leads/{lead_id}")
async def update_lead(
    lead_id: int,
    lead_data: dict,
    user_id: str = Depends(get_current_user)
):
    """
    Update a lead (only if it belongs to the user)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First check if lead belongs to user
            check_response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params={
                    'id': f'eq.{lead_id}',
                    'user_id': f'eq.{user_id}',
                    'select': 'id'
                },
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if check_response.status_code != 200 or not check_response.json():
                raise HTTPException(
                    status_code=404,
                    detail="Lead not found or you don't have permission"
                )
            
            # Update the lead
            update_response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params={'id': f'eq.{lead_id}'},
                json=lead_data,
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                }
            )
            
            if update_response.status_code != 200:
                raise HTTPException(
                    status_code=update_response.status_code,
                    detail=f"Failed to update lead: {update_response.text}"
                )
            
            return update_response.json()[0]
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a lead (only if it belongs to the user)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Delete with user_id check
            response = await client.delete(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params={
                    'id': f'eq.{lead_id}',
                    'user_id': f'eq.{user_id}'
                },
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 204:
                raise HTTPException(
                    status_code=404,
                    detail="Lead not found or you don't have permission"
                )
            
            return {'message': 'Lead deleted successfully'}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/leads/export")
async def export_leads(
    filters: dict,
    user_id: str = Depends(get_current_user)
):
    """
    Export all leads matching filters for the authenticated user
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Build query parameters
            params = {
                'user_id': f'eq.{user_id}',
                'select': '*',
                'order': 'created_at.desc'
            }
            
            # Add filters
            if filters.get('conjunto'):
                params['conjunto_de_locais'] = f'eq.{filters["conjunto"]}'
            if filters.get('cidade'):
                params['cidade'] = f'eq.{filters["cidade"]}'
            if filters.get('search'):
                params['or'] = f'(nome.ilike.%{filters["search"]}%,telefone.ilike.%{filters["search"]}%,website.ilike.%{filters["search"]}%)'
            
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/gmap_leads",
                params=params,
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to export leads: {response.text}"
                )
            
            leads = response.json()
            
            return {
                'leads': leads,
                'count': len(leads)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
