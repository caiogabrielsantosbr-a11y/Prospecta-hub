"""
Tests for GMap Router Supabase Integration Endpoints

This module tests the new Supabase endpoints added to the GMap router,
specifically the GET /api/gmap/supabase/results/{task_id} endpoint.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    with patch('modules.gmap.router.get_supabase_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestSupabaseResultsEndpoint:
    """Tests for GET /api/gmap/supabase/results/{task_id} endpoint"""
    
    def test_endpoint_returns_leads_with_all_fields(self, mock_supabase_client):
        """
        Test that the endpoint returns leads with all fields when data exists.
        
        Validates: Requirements 6.1, 6.3
        """
        # Arrange
        task_id = "test-task-123"
        expected_leads = [
            {
                "id": 1,
                "nome": "Business A",
                "telefone": "+55 11 1234-5678",
                "website": "https://business-a.com",
                "endereco": "Rua A, 123",
                "cidade": "São Paulo, SP",
                "url": "https://www.google.com/maps/place/business-a",
                "conjunto_de_locais": "Capitais do Brasil",
                "task_id": task_id,
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": 2,
                "nome": "Business B",
                "telefone": "Sem Telefone",
                "website": "Sem Website",
                "endereco": "Rua B, 456",
                "cidade": "Rio de Janeiro, RJ",
                "url": "https://www.google.com/maps/place/business-b",
                "conjunto_de_locais": "Capitais do Brasil",
                "task_id": task_id,
                "created_at": "2024-01-15T10:31:00Z"
            }
        ]
        
        mock_supabase_client.is_available.return_value = True
        mock_supabase_client.get_leads_by_task = AsyncMock(return_value=expected_leads)
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}")
        
        # Assert
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        
        # Verify all fields are present in first lead
        assert results[0]["nome"] == "Business A"
        assert results[0]["telefone"] == "+55 11 1234-5678"
        assert results[0]["website"] == "https://business-a.com"
        assert results[0]["endereco"] == "Rua A, 123"
        assert results[0]["cidade"] == "São Paulo, SP"
        assert results[0]["url"] == "https://www.google.com/maps/place/business-a"
        assert results[0]["conjunto_de_locais"] == "Capitais do Brasil"
        assert results[0]["task_id"] == task_id
        assert "created_at" in results[0]
        
        # Verify client was called with correct parameters
        mock_supabase_client.get_leads_by_task.assert_called_once_with(
            task_id, limit=100, offset=0
        )
    
    def test_endpoint_returns_empty_list_for_nonexistent_task(self, mock_supabase_client):
        """
        Test that the endpoint returns empty list with status 200 for non-existent task_id.
        
        Validates: Requirements 6.5
        """
        # Arrange
        task_id = "nonexistent-task"
        mock_supabase_client.is_available.return_value = True
        mock_supabase_client.get_leads_by_task = AsyncMock(return_value=[])
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}")
        
        # Assert
        assert response.status_code == 200
        results = response.json()
        assert results == []
        assert isinstance(results, list)
    
    def test_endpoint_supports_pagination_with_limit(self, mock_supabase_client):
        """
        Test that the endpoint supports pagination with limit parameter.
        
        Validates: Requirements 6.4
        """
        # Arrange
        task_id = "test-task-123"
        limit = 50
        expected_leads = [{"nome": f"Business {i}"} for i in range(limit)]
        
        mock_supabase_client.is_available.return_value = True
        mock_supabase_client.get_leads_by_task = AsyncMock(return_value=expected_leads)
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}?limit={limit}")
        
        # Assert
        assert response.status_code == 200
        results = response.json()
        assert len(results) == limit
        
        # Verify client was called with correct limit
        mock_supabase_client.get_leads_by_task.assert_called_once_with(
            task_id, limit=limit, offset=0
        )
    
    def test_endpoint_supports_pagination_with_offset(self, mock_supabase_client):
        """
        Test that the endpoint supports pagination with offset parameter.
        
        Validates: Requirements 6.4
        """
        # Arrange
        task_id = "test-task-123"
        offset = 100
        expected_leads = [{"nome": f"Business {i}"} for i in range(100, 150)]
        
        mock_supabase_client.is_available.return_value = True
        mock_supabase_client.get_leads_by_task = AsyncMock(return_value=expected_leads)
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}?offset={offset}")
        
        # Assert
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 50
        
        # Verify client was called with correct offset
        mock_supabase_client.get_leads_by_task.assert_called_once_with(
            task_id, limit=100, offset=offset
        )
    
    def test_endpoint_supports_pagination_with_limit_and_offset(self, mock_supabase_client):
        """
        Test that the endpoint supports pagination with both limit and offset parameters.
        
        Validates: Requirements 6.4
        """
        # Arrange
        task_id = "test-task-123"
        limit = 25
        offset = 50
        expected_leads = [{"nome": f"Business {i}"} for i in range(50, 75)]
        
        mock_supabase_client.is_available.return_value = True
        mock_supabase_client.get_leads_by_task = AsyncMock(return_value=expected_leads)
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}?limit={limit}&offset={offset}")
        
        # Assert
        assert response.status_code == 200
        results = response.json()
        assert len(results) == limit
        
        # Verify client was called with correct parameters
        mock_supabase_client.get_leads_by_task.assert_called_once_with(
            task_id, limit=limit, offset=offset
        )
    
    def test_endpoint_uses_default_pagination_values(self, mock_supabase_client):
        """
        Test that the endpoint uses default values (limit=100, offset=0) when not specified.
        
        Validates: Requirements 6.3
        """
        # Arrange
        task_id = "test-task-123"
        mock_supabase_client.is_available.return_value = True
        mock_supabase_client.get_leads_by_task = AsyncMock(return_value=[])
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}")
        
        # Assert
        assert response.status_code == 200
        
        # Verify client was called with default values
        mock_supabase_client.get_leads_by_task.assert_called_once_with(
            task_id, limit=100, offset=0
        )
    
    def test_endpoint_returns_error_when_supabase_unavailable(self, mock_supabase_client):
        """
        Test that the endpoint returns error message when Supabase is unavailable.
        
        Validates: Requirements 4.3
        """
        # Arrange
        task_id = "test-task-123"
        mock_supabase_client.is_available.return_value = False
        
        # Act
        client = TestClient(app)
        response = client.get(f"/api/gmap/supabase/results/{task_id}")
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "error" in result
        assert "Supabase integration is not available" in result["error"]
        assert "results" in result
        assert result["results"] == []
        
        # Verify get_leads_by_task was NOT called
        mock_supabase_client.get_leads_by_task.assert_not_called()
    
    def test_endpoint_rejects_negative_limit(self):
        """
        Test that the endpoint rejects negative limit values.
        """
        # Act
        client = TestClient(app)
        response = client.get("/api/gmap/supabase/results/test-task?limit=-1")
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_endpoint_rejects_negative_offset(self):
        """
        Test that the endpoint rejects negative offset values.
        """
        # Act
        client = TestClient(app)
        response = client.get("/api/gmap/supabase/results/test-task?offset=-1")
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_endpoint_rejects_zero_limit(self):
        """
        Test that the endpoint rejects zero limit value (minimum is 1).
        """
        # Act
        client = TestClient(app)
        response = client.get("/api/gmap/supabase/results/test-task?limit=0")
        
        # Assert
        assert response.status_code == 422  # Validation error
