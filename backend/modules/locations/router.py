"""
Locations API - Manage location sets from Supabase
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List
from pathlib import Path
import json
from database.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/locations", tags=["locations"])


class LocationSetCreate(BaseModel):
    """Request model for creating a new location set"""
    name: str = Field(..., min_length=3, max_length=100, description="Unique name for the location set")
    description: str = Field(..., max_length=500, description="Description of the location set")
    locations: List[str] = Field(..., min_length=1, description="Array of location strings")
    
    @field_validator('locations')
    @classmethod
    def validate_locations(cls, v):
        """Validate that all locations are non-empty strings"""
        if not v:
            raise ValueError("Location set must contain at least one location")
        
        # Check all items are strings
        if not all(isinstance(loc, str) for loc in v):
            raise ValueError("All locations must be strings")
        
        # Trim whitespace and filter out empty strings
        trimmed = [loc.strip() for loc in v]
        empty_count = sum(1 for loc in trimmed if not loc)
        
        if empty_count > 0:
            raise ValueError("All location strings must be non-empty after trimming whitespace")
        
        return trimmed

LOCAIS_DIR = Path(__file__).parent.parent.parent / "locais"


@router.post("")
async def create_location_set(data: LocationSetCreate):
    """
    Create a new location set by uploading to Supabase Storage.

    Validates:
    - Name length (3-100 characters)
    - Description length (max 500 characters)
    - Locations array has at least 1 location
    - Each location is a non-empty string
    - Trims whitespace from location strings

    Returns:
        dict: Created location set metadata with id, name, description,
              file_path, location_count, and created_at

    Raises:
        HTTPException 400: Validation errors (invalid lengths, empty locations, non-string values)
        HTTPException 409: Duplicate name error
        HTTPException 413: File size exceeds 10MB limit
        HTTPException 500: Storage or database errors
    """
    try:
        supabase_client = get_supabase_client()

        # Check if Supabase integration is available (try reload first)
        if not supabase_client.is_available():
            supabase_client.reload_credentials()
        if not supabase_client.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )
        
        # Validate file size (approximate check - 10MB limit)
        # Estimate JSON size: each location ~50 chars average, plus overhead
        estimated_size = len(data.locations) * 50 + 1000
        max_size = 10 * 1024 * 1024  # 10MB
        
        if estimated_size > max_size:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_too_large",
                    "message": "Location file exceeds 10MB size limit",
                    "details": {"estimated_size": estimated_size, "max_size": max_size}
                }
            )
        
        # Call create_location_set method
        created_record = await supabase_client.create_location_set(
            name=data.name,
            description=data.description,
            locations=data.locations
        )
        
        # Add storage_url to response
        supabase_url = supabase_client.get_url()
        created_record['storage_url'] = f"{supabase_url}/storage/v1/object/public/location-files/{created_record['file_path']}"
        
        return created_record
    
    except HTTPException:
        # Re-raise HTTPException without modification
        raise
        
    except ValueError as e:
        # Validation errors from create_location_set
        error_msg = str(e)
        
        if "name must be between 3 and 100 characters" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_name_length",
                    "message": error_msg,
                    "details": {"name_length": len(data.name)}
                }
            )
        elif "description must not exceed 500 characters" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_description_length",
                    "message": error_msg,
                    "details": {"description_length": len(data.description)}
                }
            )
        elif "must contain at least one" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "empty_locations",
                    "message": error_msg
                }
            )
        elif "must be strings" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_location_format",
                    "message": error_msg
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "message": error_msg
                }
            )
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for Supabase unavailable error
        if "Supabase integration is disabled" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )
        
        # Check for duplicate name error
        if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "duplicate_name",
                    "message": f"Location set with name '{data.name}' already exists"
                }
            )
        
        # Check for upload failure
        if "upload" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "upload_failed",
                    "message": "Failed to upload location file to storage"
                }
            )
        
        # Generic error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error",
                "message": f"Failed to create location set: {error_msg}"
            }
        )


@router.get("")
async def get_all_locations():
    """Get all available location sets from Supabase"""
    try:
        supabase_client = get_supabase_client()

        # Check if Supabase integration is available (try reload first)
        if not supabase_client.is_available():
            supabase_client.reload_credentials()
        if not supabase_client.is_available():
            # Fallback to file system for backward compatibility
            if not LOCAIS_DIR.exists():
                return []
            
            locations = []
            for json_file in LOCAIS_DIR.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        locations.append(data)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
                    continue
            
            return locations
        
        # Get location sets from Supabase
        location_sets = await supabase_client.get_all_location_sets()
        
        # Add storage_url to each location set for frontend to download JSON
        supabase_url = supabase_client.get_url()
        for location_set in location_sets:
            file_path = location_set.get('file_path', '')
            location_set['storage_url'] = f"{supabase_url}/storage/v1/object/public/location-files/{file_path}"
        
        return location_sets
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{location_set_id}/preview")
async def preview_location_set(location_set_id: str, limit: int = 10):
    """
    Preview the first N locations from a location set.
    
    Downloads the Location_JSON file from Supabase Storage and returns
    the first N locations (default: 10).
    
    Args:
        location_set_id: UUID of the location set
        limit: Maximum number of locations to return (default: 10)
    
    Returns:
        dict: Preview data with fields:
            - id: UUID of the location set
            - name: Location set name
            - preview: List of first N location strings
            - total_count: Total number of locations in the set
            - showing: Number of locations in the preview
    
    Raises:
        HTTPException 404: Location set not found
        HTTPException 500: Download or parsing errors
        HTTPException 503: Supabase unavailable
    """
    try:
        supabase_client = get_supabase_client()
        
        # Check if Supabase integration is available (try reload first)
        if not supabase_client.is_available():
            supabase_client.reload_credentials()
        if not supabase_client.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )

        # Validate limit parameter
        if limit < 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_limit",
                    "message": "Limit must be at least 1"
                }
            )
        
        if limit > 1000:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_limit",
                    "message": "Limit must not exceed 1000"
                }
            )
        
        # Call get_location_set_preview method
        preview_data = await supabase_client.get_location_set_preview(
            location_set_id=location_set_id,
            limit=limit
        )
        
        return preview_data
    
    except HTTPException:
        # Re-raise HTTPException without modification
        raise
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for Supabase unavailable error
        if "Supabase integration is disabled" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )
        
        # Check for file not found in storage (more specific, check first)
        if "Location file not found" in error_msg or "file not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "file_not_found",
                    "message": "Location file not found in storage"
                }
            )
        
        # Check for location set not found (less specific, check after file not found)
        if "Location set not found" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "location_set_not_found",
                    "message": f"Location set with id '{location_set_id}' not found"
                }
            )
        
        # Check for parsing errors
        if "parse" in error_msg.lower() or "json" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "parsing_failed",
                    "message": "Failed to parse location file"
                }
            )
        
        # Check for download errors
        if "download" in error_msg.lower() or "network" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "download_failed",
                    "message": "Failed to download location file from storage"
                }
            )
        
        # Generic error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error",
                "message": f"Failed to preview location set: {error_msg}"
            }
        )

@router.get("/{location_set_id}/full")
async def get_location_set_full(location_set_id: str):
    """
    Get the complete location array from a location set.
    
    Downloads the Location_JSON file from Supabase Storage and returns
    all locations for use in the GMap extractor.
    
    Args:
        location_set_id: UUID of the location set
    
    Returns:
        dict: Full location data with fields:
            - id: UUID of the location set
            - name: Location set name
            - locations: Complete list of all location strings
            - total_count: Total number of locations in the set
    
    Raises:
        HTTPException 404: Location set not found
        HTTPException 500: Download or parsing errors
        HTTPException 503: Supabase unavailable
    """
    try:
        supabase_client = get_supabase_client()
        
        # Check if Supabase integration is available (try reload first)
        if not supabase_client.is_available():
            supabase_client.reload_credentials()
        if not supabase_client.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )

        # Call get_location_set_full method
        full_data = await supabase_client.get_location_set_full(
            location_set_id=location_set_id
        )
        
        return full_data
    
    except HTTPException:
        # Re-raise HTTPException without modification
        raise
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for Supabase unavailable error
        if "Supabase integration is disabled" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )
        
        # Check for file not found in storage (more specific, check first)
        if "Location file not found" in error_msg or "file not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "file_not_found",
                    "message": "Location file not found in storage"
                }
            )
        
        # Check for location set not found (less specific, check after file not found)
        if "Location set not found" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "location_set_not_found",
                    "message": f"Location set with id '{location_set_id}' not found"
                }
            )
        
        # Check for parsing errors
        if "parse" in error_msg.lower() or "json" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "parsing_failed",
                    "message": "Failed to parse location file"
                }
            )
        
        # Check for download errors
        if "download" in error_msg.lower() or "network" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "download_failed",
                    "message": "Failed to download location file from storage"
                }
            )
        
        # Generic error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error",
                "message": f"Failed to get full location set: {error_msg}"
            }
        )

@router.delete("/{location_set_id}")
async def delete_location_set(location_set_id: str):
    """
    Delete a location set by removing both the JSON file from Supabase Storage 
    and the metadata record from the database.
    
    This endpoint:
    1. Retrieves the location set metadata to get the file_path
    2. Attempts to delete the JSON file from Supabase Storage
    3. Deletes the metadata record from location_sets table
    4. Handles file deletion failures gracefully (logs error but continues with database deletion)
    
    Args:
        location_set_id: UUID of the location set to delete
    
    Returns:
        dict: Success confirmation with deleted location set details
    
    Raises:
        HTTPException 404: Location set not found
        HTTPException 500: Database or storage errors
        HTTPException 503: Supabase unavailable
    """
    try:
        supabase_client = get_supabase_client()
        
        # Check if Supabase integration is available (try reload first)
        if not supabase_client.is_available():
            supabase_client.reload_credentials()
        if not supabase_client.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )

        # Call delete_location_set method
        success = await supabase_client.delete_location_set(
            location_set_id=location_set_id
        )
        
        if success:
            return {
                "success": True,
                "message": f"Location set deleted successfully",
                "id": location_set_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "deletion_failed",
                    "message": "Failed to delete location set"
                }
            )
    
    except HTTPException:
        # Re-raise HTTPException without modification
        raise
    
    except Exception as e:
        error_msg = str(e)
        
        # Check for Supabase unavailable error
        if "Supabase integration is disabled" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "supabase_unavailable",
                    "message": "Supabase integration is not available. Please configure SUPABASE_URL and SUPABASE_KEY."
                }
            )
        
        # Check for location set not found
        if "Location set not found" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "location_set_not_found",
                    "message": f"Location set with id '{location_set_id}' not found"
                }
            )
        
        # Check for authentication errors
        if "Authentication error" in error_msg or "authentication" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "authentication_error",
                    "message": "Failed to authenticate with storage service"
                }
            )
        
        # Generic error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "server_error",
                "message": f"Failed to delete location set: {error_msg}"
            }
        )

@router.get("/{location_name}")
async def get_location_by_name(location_name: str):
    """Get a specific location set by name"""
    try:
        for json_file in LOCAIS_DIR.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('nome') == location_name:
                    return data
        
        raise HTTPException(status_code=404, detail="Location set not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
