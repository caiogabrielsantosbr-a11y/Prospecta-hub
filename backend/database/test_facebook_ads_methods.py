"""
Unit tests for Facebook Ads methods in Supabase client.
"""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from database.supabase_client import SupabaseClient
import httpx


class TestFacebookAdsLeadsMethods:
    """Test suite for Facebook Ads leads methods."""
    
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
    def sample_facebook_lead(self):
        """Sample Facebook lead data for testing."""
        return {
            'name': 'Test Page',
            'page_url': 'https://facebook.com/testpage',
            'ad_url': 'https://facebook.com/ads/123',
            'page_id': 'page123',
            'emails': 'test@example.com',
            'phones': '+55 11 98765-4321',
            'instagram': '@testpage',
            'stage': 'feed',
            'task_id': 'task-123'
        }
    
    @pytest.mark.asyncio
    async def test_insert_facebook_lead_success(self, mock_client, sample_facebook_lead):
        """Test successful Facebook lead insertion."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mock_client.insert_facebook_lead(sample_facebook_lead)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_insert_facebook_lead_missing_name(self, mock_client):
        """Test that insert_facebook_lead fails when 'name' field is missing."""
        lead_without_name = {
            'page_url': 'https://facebook.com/testpage',
            'task_id': 'task-123'
        }
        
        result = await mock_client.insert_facebook_lead(lead_without_name)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_facebook_lead_correct_url(self, mock_client, sample_facebook_lead):
        """Test that insert_facebook_lead uses correct Supabase REST API URL."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            await mock_client.insert_facebook_lead(sample_facebook_lead)
            
            # Verify the URL
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/facebook_ads_leads'
    
    @pytest.mark.asyncio
    async def test_insert_facebook_leads_batch_success(self, mock_client):
        """Test successful batch insertion of Facebook leads."""
        leads = [
            {'name': 'Page 1', 'task_id': 'task-123'},
            {'name': 'Page 2', 'task_id': 'task-123'},
            {'name': 'Page 3', 'task_id': 'task-123'}
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            success, failures = await mock_client.insert_facebook_leads_batch(leads)
            
            assert success == 3
            assert failures == 0
    
    @pytest.mark.asyncio
    async def test_get_facebook_leads_by_task_success(self, mock_client):
        """Test successful retrieval of Facebook leads by task_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Page 1', 'task_id': 'task-123'},
            {'id': 2, 'name': 'Page 2', 'task_id': 'task-123'}
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            results = await mock_client.get_facebook_leads_by_task('task-123')
            
            assert len(results) == 2
            assert results[0]['name'] == 'Page 1'
    
    @pytest.mark.asyncio
    async def test_get_facebook_leads_by_task_correct_url(self, mock_client):
        """Test that get_facebook_leads_by_task uses correct URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await mock_client.get_facebook_leads_by_task('task-123')
            
            # Verify the URL
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/facebook_ads_leads'
    
    @pytest.mark.asyncio
    async def test_update_facebook_lead_contacts_success(self, mock_client):
        """Test successful update of Facebook lead contacts."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
            
            result = await mock_client.update_facebook_lead_contacts(
                id=1,
                emails='new@example.com',
                phones='+55 11 99999-9999',
                instagram='@newhandle'
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_facebook_lead_contacts_partial(self, mock_client):
        """Test partial update of Facebook lead contacts (only some fields)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_patch = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.patch = mock_patch
            
            result = await mock_client.update_facebook_lead_contacts(
                id=1,
                emails='new@example.com'
            )
            
            assert result is True
            
            # Verify only emails was in the payload
            call_args = mock_patch.call_args
            assert call_args[1]['json'] == {'emails': 'new@example.com'}
    
    @pytest.mark.asyncio
    async def test_update_facebook_lead_contacts_no_fields(self, mock_client):
        """Test update with no fields returns True (nothing to update)."""
        result = await mock_client.update_facebook_lead_contacts(id=1)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_facebook_lead_contacts_missing_id(self, mock_client):
        """Test that update fails when id is missing."""
        result = await mock_client.update_facebook_lead_contacts(
            id=None,
            emails='test@example.com'
        )
        
        assert result is False
