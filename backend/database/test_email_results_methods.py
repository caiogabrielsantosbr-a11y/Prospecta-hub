"""
Unit tests for email_results methods in Supabase client.
"""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from database.supabase_client import SupabaseClient
import httpx


class TestEmailResultsMethods:
    """Test suite for email_results methods."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock SupabaseClient with valid credentials."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            client = SupabaseClient()
            yield client
    
    @pytest.fixture
    def sample_email_result(self):
        """Sample email result data for testing."""
        return {
            'domain': 'example.com',
            'email': 'contact@example.com',
            'source': 'RDAP',
            'task_id': 'task-123'
        }
    
    @pytest.mark.asyncio
    async def test_insert_email_result_success(self, mock_client, sample_email_result):
        """Test successful email result insertion."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mock_client.insert_email_result(sample_email_result)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_insert_email_result_missing_domain(self, mock_client):
        """Test that insert_email_result fails when 'domain' field is missing."""
        result_without_domain = {
            'email': 'test@example.com',
            'task_id': 'task-123'
        }
        
        result = await mock_client.insert_email_result(result_without_domain)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_email_result_correct_url(self, mock_client, sample_email_result):
        """Test that insert_email_result uses correct Supabase REST API URL."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            await mock_client.insert_email_result(sample_email_result)
            
            # Verify the URL
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/email_results'
    
    @pytest.mark.asyncio
    async def test_insert_email_results_batch_success(self, mock_client):
        """Test successful batch insertion of email results."""
        results = [
            {'domain': 'example1.com', 'email': 'test1@example1.com', 'task_id': 'task-123'},
            {'domain': 'example2.com', 'email': 'test2@example2.com', 'task_id': 'task-123'},
            {'domain': 'example3.com', 'email': None, 'task_id': 'task-123'}
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            success, failures = await mock_client.insert_email_results_batch(results)
            
            assert success == 3
            assert failures == 0
    
    @pytest.mark.asyncio
    async def test_get_email_results_by_task_success(self, mock_client):
        """Test successful retrieval of email results by task_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'domain': 'example1.com', 'email': 'test1@example1.com', 'task_id': 'task-123'},
            {'id': 2, 'domain': 'example2.com', 'email': 'test2@example2.com', 'task_id': 'task-123'}
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            results = await mock_client.get_email_results_by_task('task-123')
            
            assert len(results) == 2
            assert results[0]['domain'] == 'example1.com'
    
    @pytest.mark.asyncio
    async def test_get_email_results_by_task_correct_url(self, mock_client):
        """Test that get_email_results_by_task uses correct URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await mock_client.get_email_results_by_task('task-123')
            
            # Verify the URL
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/email_results'

