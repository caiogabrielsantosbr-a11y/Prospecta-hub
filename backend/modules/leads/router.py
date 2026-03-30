"""
Leads Management Router — API endpoints for lead management.
Provides CRUD operations and filtering for leads from Supabase.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/")
async def get_leads(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    conjunto: Optional[str] = None,
    cidade: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get leads with pagination and filtering.
    
    Query Parameters:
    - limit: Number of leads to return (1-1000, default 100)
    - offset: Number of leads to skip (default 0)
    - conjunto: Filter by conjunto_de_locais
    - cidade: Filter by cidade
    - search: Search in nome, telefone, website
    """
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        leads = await supabase.get_leads_filtered(
            limit=limit,
            offset=offset,
            conjunto=conjunto,
            cidade=cidade,
            search=search
        )
        
        # Get total count for pagination
        total = await supabase.count_leads(conjunto=conjunto, cidade=cidade, search=search)
        
        return {
            "leads": leads,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leads: {str(e)}")


@router.get("/stats")
async def get_leads_stats():
    """Get statistics about leads."""
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        stats = await supabase.get_leads_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/conjuntos")
async def get_conjuntos():
    """Get list of all conjunto_de_locais values."""
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        conjuntos = await supabase.get_distinct_conjuntos()
        return {"conjuntos": conjuntos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conjuntos: {str(e)}")


@router.get("/cidades")
async def get_cidades(conjunto: Optional[str] = None):
    """Get list of all cidades, optionally filtered by conjunto."""
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        cidades = await supabase.get_distinct_cidades(conjunto=conjunto)
        return {"cidades": cidades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cidades: {str(e)}")


@router.delete("/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead by ID."""
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        success = await supabase.delete_lead(lead_id)
        if not success:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"message": "Lead deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting lead: {str(e)}")


@router.put("/{lead_id}")
async def update_lead(lead_id: int, lead_data: dict):
    """Update a lead by ID."""
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        success = await supabase.update_lead(lead_id, lead_data)
        if not success:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"message": "Lead updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating lead: {str(e)}")


@router.post("/export")
async def export_leads(filters: dict):
    """Export leads to CSV based on filters."""
    supabase = get_supabase_client()
    
    if not supabase.is_available():
        raise HTTPException(status_code=503, detail="Supabase integration is not available")
    
    try:
        # Get all leads matching filters (no limit)
        leads = await supabase.get_leads_filtered(
            limit=10000,
            offset=0,
            conjunto=filters.get("conjunto"),
            cidade=filters.get("cidade"),
            search=filters.get("search")
        )
        
        return {"leads": leads, "count": len(leads)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting leads: {str(e)}")
