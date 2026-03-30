"""
Unit tests for locations router - GET /api/locations endpoint
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from modules.locations.router import router

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestGetAllLocations:
    """Test suite for GET /api/locations endpoint"""
    
    def test_get_all_locations_from_supabase_success(self):
        """Test successful retrieval of location sets from Supabase"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        # Mock location sets data
        mock_location_sets = [
            {
                "id": "uuid-1",
                "name": "Capitais do Brasil",
                "description": "Todas as 27 capitais brasileiras",
                "file_path": "uuid-1.json",
                "location_count": 27,
                "created_at": "2025-01-15T10:30:00Z"
            },
            {
                "id": "uuid-2",
                "name": "Sudeste Brasil",
                "description": "Estados do Sudeste",
                "file_path": "uuid-2.json",
                "location_count": 4,
                "created_at": "2025-01-14T09:20:00Z"
            }
        ]
        
        # Create async mock for get_all_location_sets
        async def mock_get_all():
            return mock_location_sets
        
        mock_client.get_all_location_sets = mock_get_all
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify first location set
        assert data[0]["id"] == "uuid-1"
        assert data[0]["name"] == "Capitais do Brasil"
        assert data[0]["location_count"] == 27
        assert data[0]["storage_url"] == "https://test.supabase.co/storage/v1/object/public/location-files/uuid-1.json"
        
        # Verify second location set
        assert data[1]["id"] == "uuid-2"
        assert data[1]["name"] == "Sudeste Brasil"
        assert data[1]["location_count"] == 4
        assert data[1]["storage_url"] == "https://test.supabase.co/storage/v1/object/public/location-files/uuid-2.json"
    
    def test_get_all_locations_empty_result(self):
        """Test that empty results return empty list"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        # Create async mock that returns empty list
        async def mock_get_all():
            return []
        
        mock_client.get_all_location_sets = mock_get_all
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_all_locations_fallback_to_filesystem_when_supabase_unavailable(self, tmp_path):
        """Test fallback to file system when Supabase is unavailable"""
        # Mock Supabase client as unavailable
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        
        # Create temporary JSON files
        locais_dir = tmp_path / "locais"
        locais_dir.mkdir()
        
        # Create test JSON file
        test_file = locais_dir / "test-locations.json"
        test_file.write_text('{"nome": "Test Set", "descricao": "Test description", "locais": ["City 1", "City 2"]}')
        
        # Patch get_supabase_client and LOCAIS_DIR
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            with patch('modules.locations.router.LOCAIS_DIR', locais_dir):
                response = client.get("/api/locations")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nome"] == "Test Set"
        assert data[0]["descricao"] == "Test description"
        assert len(data[0]["locais"]) == 2
    
    def test_get_all_locations_fallback_returns_empty_when_no_files(self, tmp_path):
        """Test fallback returns empty list when no JSON files exist"""
        # Mock Supabase client as unavailable
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        
        # Create empty directory
        locais_dir = tmp_path / "locais"
        locais_dir.mkdir()
        
        # Patch get_supabase_client and LOCAIS_DIR
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            with patch('modules.locations.router.LOCAIS_DIR', locais_dir):
                response = client.get("/api/locations")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_all_locations_handles_supabase_exception(self):
        """Test that Supabase exceptions are handled properly"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises exception
        async def mock_get_all():
            raise Exception("Database connection error")
        
        mock_client.get_all_location_sets = mock_get_all
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations")
        
        # Assertions
        assert response.status_code == 500
        assert "Database connection error" in response.json()["detail"]
    
    def test_get_all_locations_includes_all_metadata_fields(self):
        """Test that all required metadata fields are included in response"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        # Mock location set with all fields
        mock_location_sets = [
            {
                "id": "uuid-1",
                "name": "Test Set",
                "description": "Test description",
                "file_path": "uuid-1.json",
                "location_count": 10,
                "created_at": "2025-01-15T10:30:00Z"
            }
        ]
        
        # Create async mock
        async def mock_get_all():
            return mock_location_sets
        
        mock_client.get_all_location_sets = mock_get_all
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        # Verify all required fields are present
        location_set = data[0]
        assert "id" in location_set
        assert "name" in location_set
        assert "description" in location_set
        assert "file_path" in location_set
        assert "location_count" in location_set
        assert "created_at" in location_set
        assert "storage_url" in location_set
        
        # Verify values
        assert location_set["id"] == "uuid-1"
        assert location_set["name"] == "Test Set"
        assert location_set["description"] == "Test description"
        assert location_set["file_path"] == "uuid-1.json"
        assert location_set["location_count"] == 10
        assert location_set["created_at"] == "2025-01-15T10:30:00Z"
        assert location_set["storage_url"] == "https://test.supabase.co/storage/v1/object/public/location-files/uuid-1.json"



class TestCreateLocationSet:
    """Test suite for POST /api/locations endpoint"""
    
    def test_create_location_set_success(self):
        """Test successful location set creation"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        # Mock created record
        mock_created_record = {
            "id": "uuid-123",
            "name": "Test Capitals",
            "description": "Test description",
            "file_path": "uuid-123.json",
            "location_count": 2,
            "created_at": "2025-01-15T10:30:00Z"
        }
        
        # Create async mock for create_location_set
        async def mock_create(name, description, locations):
            return mock_created_record
        
        mock_client.create_location_set = mock_create
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "Test Capitals",
                "description": "Test description",
                "locations": ["São Paulo, SP", "Rio de Janeiro, RJ"]
            })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "uuid-123"
        assert data["name"] == "Test Capitals"
        assert data["description"] == "Test description"
        assert data["location_count"] == 2
        assert data["file_path"] == "uuid-123.json"
        assert data["storage_url"] == "https://test.supabase.co/storage/v1/object/public/location-files/uuid-123.json"
    
    def test_create_location_set_trims_whitespace(self):
        """Test that whitespace is trimmed from location strings"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        # Track the locations passed to create_location_set
        captured_locations = []
        
        async def mock_create(name, description, locations):
            captured_locations.extend(locations)
            return {
                "id": "uuid-123",
                "name": name,
                "description": description,
                "file_path": "uuid-123.json",
                "location_count": len(locations),
                "created_at": "2025-01-15T10:30:00Z"
            }
        
        mock_client.create_location_set = mock_create
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "Test Set",
                "description": "Test",
                "locations": ["  São Paulo, SP  ", " Rio de Janeiro, RJ"]
            })
        
        # Assertions
        assert response.status_code == 200
        # Verify locations were trimmed by Pydantic validator
        assert captured_locations == ["São Paulo, SP", "Rio de Janeiro, RJ"]
    
    def test_create_location_set_duplicate_name(self):
        """Test duplicate name rejection"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises duplicate error
        async def mock_create(name, description, locations):
            raise Exception("duplicate key value violates unique constraint")
        
        mock_client.create_location_set = mock_create
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "Duplicate Test",
                "description": "Test",
                "locations": ["São Paulo, SP"]
            })
        
        # Assertions
        assert response.status_code == 409
        error = response.json()
        assert error["detail"]["error"] == "duplicate_name"
        assert "already exists" in error["detail"]["message"]
    
    def test_create_location_set_empty_locations(self):
        """Test empty locations array rejection"""
        response = client.post("/api/locations", json={
            "name": "Empty Test",
            "description": "Test",
            "locations": []
        })
        
        # Assertions - Pydantic validation should catch this
        assert response.status_code == 422  # Unprocessable Entity from Pydantic
    
    def test_create_location_set_non_string_locations(self):
        """Test non-string location values rejection"""
        response = client.post("/api/locations", json={
            "name": "Invalid Test",
            "description": "Test",
            "locations": ["São Paulo, SP", 123, "Rio de Janeiro, RJ"]
        })
        
        # Assertions - Pydantic validation should catch this
        assert response.status_code == 422  # Unprocessable Entity from Pydantic
    
    def test_create_location_set_name_too_short(self):
        """Test name length validation (too short)"""
        response = client.post("/api/locations", json={
            "name": "AB",  # Only 2 characters
            "description": "Test",
            "locations": ["São Paulo, SP"]
        })
        
        # Assertions - Pydantic validation should catch this
        assert response.status_code == 422  # Unprocessable Entity from Pydantic
    
    def test_create_location_set_name_too_long(self):
        """Test name length validation (too long)"""
        long_name = "A" * 101  # 101 characters
        response = client.post("/api/locations", json={
            "name": long_name,
            "description": "Test",
            "locations": ["São Paulo, SP"]
        })
        
        # Assertions - Pydantic validation should catch this
        assert response.status_code == 422  # Unprocessable Entity from Pydantic
    
    def test_create_location_set_description_too_long(self):
        """Test description length validation"""
        long_description = "A" * 501  # 501 characters
        response = client.post("/api/locations", json={
            "name": "Test Set",
            "description": long_description,
            "locations": ["São Paulo, SP"]
        })
        
        # Assertions - Pydantic validation should catch this
        assert response.status_code == 422  # Unprocessable Entity from Pydantic
    
    def test_create_location_set_supabase_unavailable(self):
        """Test error when Supabase is unavailable"""
        # Mock Supabase client as unavailable
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "Test Set",
                "description": "Test",
                "locations": ["São Paulo, SP"]
            })
        
        # Assertions
        assert response.status_code == 503
        error = response.json()
        assert error["detail"]["error"] == "supabase_unavailable"
    
    def test_create_location_set_upload_failure(self):
        """Test handling of storage upload failures"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises upload error
        async def mock_create(name, description, locations):
            raise Exception("Failed to upload location file to storage")
        
        mock_client.create_location_set = mock_create
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "Test Set",
                "description": "Test",
                "locations": ["São Paulo, SP"]
            })
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "upload_failed"
    
    def test_create_location_set_with_whitespace_only_locations(self):
        """Test rejection of locations that are only whitespace"""
        response = client.post("/api/locations", json={
            "name": "Test Set",
            "description": "Test",
            "locations": ["São Paulo, SP", "   ", "Rio de Janeiro, RJ"]
        })
        
        # Assertions - Pydantic validator should catch this
        assert response.status_code == 422  # Unprocessable Entity from Pydantic
    
    def test_create_location_set_minimum_valid_name(self):
        """Test creation with minimum valid name length (3 characters)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        async def mock_create(name, description, locations):
            return {
                "id": "uuid-123",
                "name": name,
                "description": description,
                "file_path": "uuid-123.json",
                "location_count": len(locations),
                "created_at": "2025-01-15T10:30:00Z"
            }
        
        mock_client.create_location_set = mock_create
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "ABC",  # Exactly 3 characters
                "description": "Test",
                "locations": ["São Paulo, SP"]
            })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ABC"
    
    def test_create_location_set_maximum_valid_name(self):
        """Test creation with maximum valid name length (100 characters)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        async def mock_create(name, description, locations):
            return {
                "id": "uuid-123",
                "name": name,
                "description": description,
                "file_path": "uuid-123.json",
                "location_count": len(locations),
                "created_at": "2025-01-15T10:30:00Z"
            }
        
        mock_client.create_location_set = mock_create
        
        max_name = "A" * 100  # Exactly 100 characters
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": max_name,
                "description": "Test",
                "locations": ["São Paulo, SP"]
            })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == max_name
    
    def test_create_location_set_maximum_valid_description(self):
        """Test creation with maximum valid description length (500 characters)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.get_url.return_value = "https://test.supabase.co"
        
        async def mock_create(name, description, locations):
            return {
                "id": "uuid-123",
                "name": name,
                "description": description,
                "file_path": "uuid-123.json",
                "location_count": len(locations),
                "created_at": "2025-01-15T10:30:00Z"
            }
        
        mock_client.create_location_set = mock_create
        
        max_description = "A" * 500  # Exactly 500 characters
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.post("/api/locations", json={
                "name": "Test Set",
                "description": max_description,
                "locations": ["São Paulo, SP"]
            })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == max_description



class TestPreviewLocationSet:
    """Test suite for GET /api/locations/{location_set_id}/preview endpoint"""
    
    def test_preview_location_set_success(self):
        """Test successful preview with default limit (10 locations)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock preview data
        mock_preview_data = {
            "id": "uuid-123",
            "name": "Test Capitals",
            "preview": [f"City {i}, ST" for i in range(10)],
            "total_count": 27,
            "showing": 10
        }
        
        # Create async mock for get_location_set_preview
        async def mock_preview(location_set_id, limit):
            return mock_preview_data
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "uuid-123"
        assert data["name"] == "Test Capitals"
        assert len(data["preview"]) == 10
        assert data["total_count"] == 27
        assert data["showing"] == 10
    
    def test_preview_location_set_custom_limit(self):
        """Test preview with custom limit parameter"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock preview data with 5 locations
        mock_preview_data = {
            "id": "uuid-123",
            "name": "Test Set",
            "preview": [f"City {i}, ST" for i in range(5)],
            "total_count": 100,
            "showing": 5
        }
        
        # Create async mock
        async def mock_preview(location_set_id, limit):
            return mock_preview_data
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview?limit=5")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview"]) == 5
        assert data["showing"] == 5
    
    def test_preview_location_set_fewer_than_limit(self):
        """Test preview when location set has fewer locations than limit"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock preview data with only 3 locations
        mock_preview_data = {
            "id": "uuid-123",
            "name": "Small Set",
            "preview": ["City 1, ST", "City 2, ST", "City 3, ST"],
            "total_count": 3,
            "showing": 3
        }
        
        # Create async mock
        async def mock_preview(location_set_id, limit):
            return mock_preview_data
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview"]) == 3
        assert data["total_count"] == 3
        assert data["showing"] == 3
    
    def test_preview_location_set_not_found(self):
        """Test preview when location set does not exist"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises not found error
        async def mock_preview(location_set_id, limit):
            raise Exception("Location set not found: uuid-nonexistent")
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-nonexistent/preview")
        
        # Assertions
        assert response.status_code == 404
        error = response.json()
        assert error["detail"]["error"] == "location_set_not_found"
    
    def test_preview_location_set_file_not_found(self):
        """Test preview when location file is missing from storage"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises file not found error
        async def mock_preview(location_set_id, limit):
            raise Exception("Location file not found: uuid-123.json")
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview")
        
        # Assertions
        assert response.status_code == 404
        error = response.json()
        assert error["detail"]["error"] == "file_not_found"
    
    def test_preview_location_set_parsing_error(self):
        """Test preview when JSON parsing fails"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises parsing error
        async def mock_preview(location_set_id, limit):
            raise Exception("Failed to parse location file: Invalid JSON")
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "parsing_failed"
    
    def test_preview_location_set_download_error(self):
        """Test preview when download from storage fails"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises download error
        async def mock_preview(location_set_id, limit):
            raise Exception("Network error downloading location file")
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "download_failed"
    
    def test_preview_location_set_supabase_unavailable(self):
        """Test preview when Supabase is unavailable"""
        # Mock Supabase client as unavailable
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview")
        
        # Assertions
        assert response.status_code == 503
        error = response.json()
        assert error["detail"]["error"] == "supabase_unavailable"
    
    def test_preview_location_set_invalid_limit_too_small(self):
        """Test preview with limit less than 1"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview?limit=0")
        
        # Assertions
        assert response.status_code == 400
        error = response.json()
        assert error["detail"]["error"] == "invalid_limit"
        assert "at least 1" in error["detail"]["message"]
    
    def test_preview_location_set_invalid_limit_too_large(self):
        """Test preview with limit greater than 1000"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview?limit=1001")
        
        # Assertions
        assert response.status_code == 400
        error = response.json()
        assert error["detail"]["error"] == "invalid_limit"
        assert "not exceed 1000" in error["detail"]["message"]
    
    def test_preview_location_set_limit_boundary_min(self):
        """Test preview with minimum valid limit (1)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock preview data with 1 location
        mock_preview_data = {
            "id": "uuid-123",
            "name": "Test Set",
            "preview": ["City 1, ST"],
            "total_count": 100,
            "showing": 1
        }
        
        # Create async mock
        async def mock_preview(location_set_id, limit):
            return mock_preview_data
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview?limit=1")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview"]) == 1
    
    def test_preview_location_set_limit_boundary_max(self):
        """Test preview with maximum valid limit (1000)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock preview data with 1000 locations
        mock_preview_data = {
            "id": "uuid-123",
            "name": "Large Set",
            "preview": [f"City {i}, ST" for i in range(1000)],
            "total_count": 5000,
            "showing": 1000
        }
        
        # Create async mock
        async def mock_preview(location_set_id, limit):
            return mock_preview_data
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview?limit=1000")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview"]) == 1000
    
    def test_preview_location_set_returns_first_locations_in_order(self):
        """Test that preview returns first N locations in correct order"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock preview data with specific ordered locations
        expected_locations = [
            "São Paulo, SP",
            "Rio de Janeiro, RJ",
            "Belo Horizonte, MG",
            "Curitiba, PR",
            "Porto Alegre, RS"
        ]
        
        mock_preview_data = {
            "id": "uuid-123",
            "name": "Capitais",
            "preview": expected_locations,
            "total_count": 27,
            "showing": 5
        }
        
        # Create async mock
        async def mock_preview(location_set_id, limit):
            return mock_preview_data
        
        mock_client.get_location_set_preview = mock_preview
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/preview?limit=5")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["preview"] == expected_locations
        # Verify order is preserved
        for i, location in enumerate(expected_locations):
            assert data["preview"][i] == location



class TestGetLocationSetFull:
    """Test suite for GET /api/locations/{location_set_id}/full endpoint"""
    
    def test_get_location_set_full_success(self):
        """Test successful retrieval of complete location array"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock full location data
        all_locations = [f"City {i}, ST" for i in range(100)]
        mock_full_data = {
            "id": "uuid-123",
            "name": "Test Capitals",
            "locations": all_locations,
            "total_count": 100
        }
        
        # Create async mock for get_location_set_full
        async def mock_full(location_set_id):
            return mock_full_data
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "uuid-123"
        assert data["name"] == "Test Capitals"
        assert len(data["locations"]) == 100
        assert data["total_count"] == 100
        assert data["locations"] == all_locations
    
    def test_get_location_set_full_small_set(self):
        """Test retrieval of small location set (fewer than 10 locations)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock small location set
        small_locations = ["City 1, ST", "City 2, ST", "City 3, ST"]
        mock_full_data = {
            "id": "uuid-123",
            "name": "Small Set",
            "locations": small_locations,
            "total_count": 3
        }
        
        # Create async mock
        async def mock_full(location_set_id):
            return mock_full_data
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["locations"]) == 3
        assert data["total_count"] == 3
        assert data["locations"] == small_locations
    
    def test_get_location_set_full_large_set(self):
        """Test retrieval of large location set (thousands of locations)"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock large location set
        large_locations = [f"City {i}, ST" for i in range(5000)]
        mock_full_data = {
            "id": "uuid-123",
            "name": "Large Set",
            "locations": large_locations,
            "total_count": 5000
        }
        
        # Create async mock
        async def mock_full(location_set_id):
            return mock_full_data
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["locations"]) == 5000
        assert data["total_count"] == 5000
    
    def test_get_location_set_full_not_found(self):
        """Test full retrieval when location set does not exist"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises not found error
        async def mock_full(location_set_id):
            raise Exception("Location set not found: uuid-nonexistent")
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-nonexistent/full")
        
        # Assertions
        assert response.status_code == 404
        error = response.json()
        assert error["detail"]["error"] == "location_set_not_found"
    
    def test_get_location_set_full_file_not_found(self):
        """Test full retrieval when location file is missing from storage"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises file not found error
        async def mock_full(location_set_id):
            raise Exception("Location file not found: uuid-123.json")
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 404
        error = response.json()
        assert error["detail"]["error"] == "file_not_found"
    
    def test_get_location_set_full_parsing_error(self):
        """Test full retrieval when JSON parsing fails"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises parsing error
        async def mock_full(location_set_id):
            raise Exception("Failed to parse location file: Invalid JSON")
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "parsing_failed"
    
    def test_get_location_set_full_download_error(self):
        """Test full retrieval when download from storage fails"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises download error
        async def mock_full(location_set_id):
            raise Exception("Network error downloading location file")
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "download_failed"
    
    def test_get_location_set_full_supabase_unavailable(self):
        """Test full retrieval when Supabase is unavailable"""
        # Mock Supabase client as unavailable
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 503
        error = response.json()
        assert error["detail"]["error"] == "supabase_unavailable"
    
    def test_get_location_set_full_preserves_order(self):
        """Test that full retrieval preserves location order"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock locations with specific order
        expected_locations = [
            "São Paulo, SP",
            "Rio de Janeiro, RJ",
            "Belo Horizonte, MG",
            "Curitiba, PR",
            "Porto Alegre, RS",
            "Salvador, BA",
            "Brasília, DF",
            "Fortaleza, CE",
            "Recife, PE",
            "Goiânia, GO"
        ]
        
        mock_full_data = {
            "id": "uuid-123",
            "name": "Capitais",
            "locations": expected_locations,
            "total_count": 10
        }
        
        # Create async mock
        async def mock_full(location_set_id):
            return mock_full_data
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["locations"] == expected_locations
        # Verify order is preserved
        for i, location in enumerate(expected_locations):
            assert data["locations"][i] == location
    
    def test_get_location_set_full_returns_all_fields(self):
        """Test that full retrieval returns all required fields"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Mock full data
        mock_full_data = {
            "id": "uuid-123",
            "name": "Test Set",
            "locations": ["City 1, ST", "City 2, ST"],
            "total_count": 2
        }
        
        # Create async mock
        async def mock_full(location_set_id):
            return mock_full_data
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        assert "id" in data
        assert "name" in data
        assert "locations" in data
        assert "total_count" in data
        
        # Verify values
        assert data["id"] == "uuid-123"
        assert data["name"] == "Test Set"
        assert isinstance(data["locations"], list)
        assert data["total_count"] == 2
    
    def test_get_location_set_full_handles_generic_exception(self):
        """Test that generic exceptions are handled properly"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises generic exception
        async def mock_full(location_set_id):
            raise Exception("Unexpected error occurred")
        
        mock_client.get_location_set_full = mock_full
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.get("/api/locations/uuid-123/full")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "server_error"
        assert "Unexpected error occurred" in error["detail"]["message"]



class TestDeleteLocationSet:
    """Test suite for DELETE /api/locations/{location_set_id} endpoint"""
    
    def test_delete_location_set_success(self):
        """Test successful location set deletion"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock for delete_location_set
        async def mock_delete(location_set_id):
            return True
        
        mock_client.delete_location_set = mock_delete
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-123")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
        assert data["id"] == "uuid-123"
    
    def test_delete_location_set_not_found(self):
        """Test deletion when location set does not exist"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises not found error
        async def mock_delete(location_set_id):
            raise Exception("Location set not found: uuid-nonexistent")
        
        mock_client.delete_location_set = mock_delete
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-nonexistent")
        
        # Assertions
        assert response.status_code == 404
        error = response.json()
        assert error["detail"]["error"] == "location_set_not_found"
        assert "uuid-nonexistent" in error["detail"]["message"]
    
    def test_delete_location_set_supabase_unavailable(self):
        """Test deletion when Supabase is unavailable"""
        # Mock Supabase client as unavailable
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-123")
        
        # Assertions
        assert response.status_code == 503
        error = response.json()
        assert error["detail"]["error"] == "supabase_unavailable"
        assert "not available" in error["detail"]["message"]
    
    def test_delete_location_set_authentication_error(self):
        """Test deletion when authentication fails"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises authentication error
        async def mock_delete(location_set_id):
            raise Exception("Authentication error")
        
        mock_client.delete_location_set = mock_delete
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-123")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "authentication_error"
        assert "authenticate" in error["detail"]["message"]
    
    def test_delete_location_set_returns_false(self):
        """Test deletion when delete_location_set returns False"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that returns False
        async def mock_delete(location_set_id):
            return False
        
        mock_client.delete_location_set = mock_delete
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-123")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "deletion_failed"
        assert "Failed to delete" in error["detail"]["message"]
    
    def test_delete_location_set_handles_generic_exception(self):
        """Test that generic exceptions are handled properly"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises generic exception
        async def mock_delete(location_set_id):
            raise Exception("Unexpected database error")
        
        mock_client.delete_location_set = mock_delete
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-123")
        
        # Assertions
        assert response.status_code == 500
        error = response.json()
        assert error["detail"]["error"] == "server_error"
        assert "Unexpected database error" in error["detail"]["message"]
    
    def test_delete_location_set_with_valid_uuid_format(self):
        """Test deletion with a properly formatted UUID"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Track the location_set_id passed to delete_location_set
        captured_id = []
        
        async def mock_delete(location_set_id):
            captured_id.append(location_set_id)
            return True
        
        mock_client.delete_location_set = mock_delete
        
        valid_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete(f"/api/locations/{valid_uuid}")
        
        # Assertions
        assert response.status_code == 200
        assert captured_id[0] == valid_uuid
        data = response.json()
        assert data["id"] == valid_uuid
    
    def test_delete_location_set_handles_supabase_disabled_exception(self):
        """Test deletion when Supabase integration is disabled"""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        
        # Create async mock that raises Supabase disabled error
        async def mock_delete(location_set_id):
            raise Exception("Supabase integration is disabled")
        
        mock_client.delete_location_set = mock_delete
        
        # Patch get_supabase_client
        with patch('modules.locations.router.get_supabase_client', return_value=mock_client):
            response = client.delete("/api/locations/uuid-123")
        
        # Assertions
        assert response.status_code == 503
        error = response.json()
        assert error["detail"]["error"] == "supabase_unavailable"
        assert "not available" in error["detail"]["message"]
