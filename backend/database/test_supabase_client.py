"""
Unit tests for Supabase client module.
"""
import os
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from database.supabase_client import SupabaseClient, get_supabase_client
import httpx


class TestSupabaseClient:
    """Test suite for SupabaseClient class."""
    
    def test_singleton_pattern(self):
        """Test that SupabaseClient implements singleton pattern correctly."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client1 = SupabaseClient()
        client2 = SupabaseClient()
        
        # Both should be the same instance
        assert client1 is client2
    
    def test_get_supabase_client_returns_singleton(self):
        """Test that get_supabase_client returns the same instance."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client1 = get_supabase_client()
        client2 = get_supabase_client()
        
        # Both should be the same instance
        assert client1 is client2
    
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    def test_initialization_with_valid_credentials(self):
        """Test client initialization with valid credentials."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        assert client.is_available() is True
        assert client.get_url() == 'https://test.supabase.co'
        assert client.get_key() == 'test-key'
    
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True)
    def test_initialization_with_missing_credentials(self, caplog):
        """Test client initialization with missing credentials logs warning."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with caplog.at_level('WARNING'):
            client = SupabaseClient()
        
        assert client.is_available() is False
        assert client.get_url() is None
        assert client.get_key() is None
        assert 'Supabase credentials missing' in caplog.text
        assert 'SUPABASE_URL' in caplog.text
        assert 'SUPABASE_KEY' in caplog.text
    
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': ''}, clear=True)
    def test_initialization_with_missing_key(self, caplog):
        """Test client initialization with missing SUPABASE_KEY logs warning."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with caplog.at_level('WARNING'):
            client = SupabaseClient()
        
        assert client.is_available() is False
        assert 'SUPABASE_KEY' in caplog.text
    
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': 'test-key'}, clear=True)
    def test_initialization_with_missing_url(self, caplog):
        """Test client initialization with missing SUPABASE_URL logs warning."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with caplog.at_level('WARNING'):
            client = SupabaseClient()
        
        assert client.is_available() is False
        assert 'SUPABASE_URL' in caplog.text
    
    @patch.dict(os.environ, {'SUPABASE_URL': '  https://test.supabase.co  ', 'SUPABASE_KEY': '  test-key  '})
    def test_credentials_are_stripped(self):
        """Test that credentials are stripped of whitespace."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        assert client.get_url() == 'https://test.supabase.co'
        assert client.get_key() == 'test-key'


class TestInsertLead:
    """Test suite for insert_lead method."""
    
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
    def sample_lead(self):
        """Sample lead data for testing."""
        return {
            'nome': 'Test Business',
            'telefone': '+55 11 98765-4321',
            'website': 'https://test.com',
            'endereco': 'Rua Test, 123',
            'cidade': 'São Paulo, SP',
            'url': 'https://www.google.com/maps/place/test',
            'conjunto_de_locais': 'Capitais do Brasil',
            'task_id': 'task-123'
        }
    
    @pytest.mark.asyncio
    async def test_insert_lead_success(self, mock_client, sample_lead):
        """Test successful lead insertion."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mock_client.insert_lead(sample_lead)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_insert_lead_when_disabled(self, sample_lead):
        """Test that insert_lead returns False when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.insert_lead(sample_lead)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_lead_missing_nome(self, mock_client):
        """Test that insert_lead fails when 'nome' field is missing."""
        lead_without_nome = {
            'telefone': '+55 11 98765-4321',
            'cidade': 'São Paulo, SP'
        }
        
        result = await mock_client.insert_lead(lead_without_nome)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_lead_authentication_error(self, mock_client, sample_lead):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mock_client.insert_lead(sample_lead)
            
            assert result is False
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_insert_lead_rate_limiting_with_retry(self, mock_client, sample_lead):
        """Test that rate limiting triggers retry with exponential backoff."""
        # First two attempts return 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(side_effect=[mock_response_429, mock_response_429, mock_response_success])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.insert_lead(sample_lead)
                
                assert result is True
                assert mock_post.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_insert_lead_rate_limiting_exhausted(self, mock_client, sample_lead):
        """Test that rate limiting fails after max retries."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await mock_client.insert_lead(sample_lead, max_retries=3)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_lead_network_error_with_retry(self, mock_client, sample_lead):
        """Test that network errors trigger retry with exponential backoff."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            # First two attempts raise network error, third succeeds
            mock_post = AsyncMock(side_effect=[
                httpx.ConnectError('Connection failed'),
                httpx.TimeoutException('Timeout'),
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.insert_lead(sample_lead)
                
                assert result is True
                assert mock_post.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_insert_lead_network_error_exhausted(self, mock_client, sample_lead):
        """Test that network errors fail after max retries."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectError('Connection failed')
            )
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await mock_client.insert_lead(sample_lead, max_retries=3)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_lead_exponential_backoff_timing(self, mock_client, sample_lead):
        """Test that exponential backoff increases wait time correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await mock_client.insert_lead(sample_lead, max_retries=3)
                
                # Check that sleep was called with increasing times
                # First retry: 2^0 + jitter = ~1 second
                # Second retry: 2^1 + jitter = ~2 seconds
                assert mock_sleep.call_count == 2
                
                # Verify first wait is around 1 second (2^0 + jitter)
                first_wait = mock_sleep.call_args_list[0][0][0]
                assert 1.0 <= first_wait <= 2.0
                
                # Verify second wait is around 2 seconds (2^1 + jitter)
                second_wait = mock_sleep.call_args_list[1][0][0]
                assert 2.0 <= second_wait <= 3.0
    
    @pytest.mark.asyncio
    async def test_insert_lead_http_error(self, mock_client, sample_lead):
        """Test that other HTTP errors fail immediately without retry."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            result = await mock_client.insert_lead(sample_lead)
            
            assert result is False
            assert mock_post.call_count == 1  # No retry for 500 errors
    
    @pytest.mark.asyncio
    async def test_insert_lead_unexpected_exception(self, mock_client, sample_lead):
        """Test that unexpected exceptions are caught and logged."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=ValueError('Unexpected error')
            )
            
            result = await mock_client.insert_lead(sample_lead)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_lead_correct_payload(self, mock_client, sample_lead):
        """Test that insert_lead sends correct payload to Supabase."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            await mock_client.insert_lead(sample_lead)
            
            # Verify the call was made with correct parameters
            call_args = mock_post.call_args
            assert call_args[1]['json'] == sample_lead
            assert call_args[1]['headers']['apikey'] == 'test-key'
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-key'
            assert call_args[1]['headers']['Content-Type'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_insert_lead_correct_url(self, mock_client, sample_lead):
        """Test that insert_lead uses correct Supabase REST API URL."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            await mock_client.insert_lead(sample_lead)
            
            # Verify the URL
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/gmap_leads'


class TestInsertLeadsBatch:
    """Test suite for insert_leads_batch method."""
    
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
    def sample_leads(self):
        """Sample leads data for testing."""
        return [
            {
                'nome': 'Business 1',
                'telefone': '+55 11 98765-4321',
                'website': 'https://test1.com',
                'endereco': 'Rua Test 1, 123',
                'cidade': 'São Paulo, SP',
                'url': 'https://www.google.com/maps/place/test1',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-123'
            },
            {
                'nome': 'Business 2',
                'telefone': '+55 21 98765-4321',
                'website': 'https://test2.com',
                'endereco': 'Rua Test 2, 456',
                'cidade': 'Rio de Janeiro, RJ',
                'url': 'https://www.google.com/maps/place/test2',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-123'
            },
            {
                'nome': 'Business 3',
                'telefone': '+55 31 98765-4321',
                'website': 'https://test3.com',
                'endereco': 'Rua Test 3, 789',
                'cidade': 'Belo Horizonte, MG',
                'url': 'https://www.google.com/maps/place/test3',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-123'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_batch_insert_success(self, mock_client, sample_leads):
        """Test successful batch insertion of leads."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            success, failures = await mock_client.insert_leads_batch(sample_leads)
            
            assert success == 3
            assert failures == 0
    
    @pytest.mark.asyncio
    async def test_batch_insert_when_disabled(self, sample_leads):
        """Test that batch insert returns (0, total) when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            success, failures = await client.insert_leads_batch(sample_leads)
            
            assert success == 0
            assert failures == 3
    
    @pytest.mark.asyncio
    async def test_batch_insert_empty_list(self, mock_client):
        """Test batch insert with empty list returns (0, 0)."""
        success, failures = await mock_client.insert_leads_batch([])
        
        assert success == 0
        assert failures == 0
    
    @pytest.mark.asyncio
    async def test_batch_insert_with_invalid_leads(self, mock_client):
        """Test batch insert filters out leads without 'nome' field."""
        leads = [
            {'nome': 'Valid Business', 'cidade': 'São Paulo, SP'},
            {'telefone': '+55 11 98765-4321', 'cidade': 'Rio de Janeiro, RJ'},  # Missing nome
            {'nome': 'Another Valid', 'cidade': 'Belo Horizonte, MG'}
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            success, failures = await mock_client.insert_leads_batch(leads)
            
            assert success == 2  # Only 2 valid leads
            assert failures == 1  # 1 invalid lead
    
    @pytest.mark.asyncio
    async def test_batch_insert_all_invalid(self, mock_client):
        """Test batch insert with all invalid leads."""
        leads = [
            {'telefone': '+55 11 98765-4321'},  # Missing nome
            {'cidade': 'Rio de Janeiro, RJ'}    # Missing nome
        ]
        
        success, failures = await mock_client.insert_leads_batch(leads)
        
        assert success == 0
        assert failures == 2
    
    @pytest.mark.asyncio
    async def test_batch_insert_authentication_error(self, mock_client, sample_leads):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            success, failures = await mock_client.insert_leads_batch(sample_leads)
            
            assert success == 0
            assert failures == 3
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_batch_insert_fallback_to_individual(self, mock_client, sample_leads):
        """Test that batch insert falls back to individual inserts on failure."""
        # Batch insert fails with 500 error
        mock_response_batch_fail = MagicMock()
        mock_response_batch_fail.status_code = 500
        mock_response_batch_fail.text = 'Internal Server Error'
        
        # Individual inserts succeed
        mock_response_individual_success = MagicMock()
        mock_response_individual_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            # First call (batch) fails, subsequent calls (individual) succeed
            mock_post = AsyncMock(side_effect=[
                mock_response_batch_fail,
                mock_response_individual_success,
                mock_response_individual_success,
                mock_response_individual_success
            ])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            success, failures = await mock_client.insert_leads_batch(sample_leads)
            
            assert success == 3
            assert failures == 0
            assert mock_post.call_count == 4  # 1 batch + 3 individual
    
    @pytest.mark.asyncio
    async def test_batch_insert_partial_failure_in_fallback(self, mock_client, sample_leads):
        """Test that fallback to individual inserts handles partial failures."""
        # Batch insert fails
        mock_response_batch_fail = MagicMock()
        mock_response_batch_fail.status_code = 500
        mock_response_batch_fail.text = 'Internal Server Error'
        
        # Individual inserts: first succeeds, second fails, third succeeds
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = 'Error'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(side_effect=[
                mock_response_batch_fail,
                mock_response_success,
                mock_response_fail,
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            success, failures = await mock_client.insert_leads_batch(sample_leads)
            
            assert success == 2
            assert failures == 1
    
    @pytest.mark.asyncio
    async def test_batch_insert_rate_limiting_with_retry(self, mock_client, sample_leads):
        """Test that rate limiting triggers retry with exponential backoff."""
        # First two attempts return 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(side_effect=[mock_response_429, mock_response_429, mock_response_success])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                success, failures = await mock_client.insert_leads_batch(sample_leads)
                
                assert success == 3
                assert failures == 0
                assert mock_post.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_batch_insert_network_error_with_retry(self, mock_client, sample_leads):
        """Test that network errors trigger retry with exponential backoff."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            # First two attempts raise network error, third succeeds
            mock_post = AsyncMock(side_effect=[
                httpx.ConnectError('Connection failed'),
                httpx.TimeoutException('Timeout'),
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                success, failures = await mock_client.insert_leads_batch(sample_leads)
                
                assert success == 3
                assert failures == 0
                assert mock_post.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_batch_insert_network_error_fallback(self, mock_client, sample_leads):
        """Test that exhausted network retries fall back to individual inserts."""
        # Individual inserts succeed
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            # Batch attempts all fail with network error, then individual inserts succeed
            mock_post = AsyncMock(side_effect=[
                httpx.ConnectError('Connection failed'),
                httpx.ConnectError('Connection failed'),
                httpx.ConnectError('Connection failed'),
                mock_response_success,
                mock_response_success,
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                success, failures = await mock_client.insert_leads_batch(sample_leads)
                
                assert success == 3
                assert failures == 0
                assert mock_post.call_count == 6  # 3 batch attempts + 3 individual
    
    @pytest.mark.asyncio
    async def test_batch_insert_correct_payload(self, mock_client, sample_leads):
        """Test that batch insert sends correct payload to Supabase."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            await mock_client.insert_leads_batch(sample_leads)
            
            # Verify the call was made with correct parameters
            call_args = mock_post.call_args
            assert isinstance(call_args[1]['json'], list)
            assert len(call_args[1]['json']) == 3
            assert call_args[1]['json'][0]['nome'] == 'Business 1'
            assert call_args[1]['headers']['apikey'] == 'test-key'
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-key'
    
    @pytest.mark.asyncio
    async def test_batch_insert_timeout_increased(self, mock_client, sample_leads):
        """Test that batch insert uses longer timeout (60s) than single insert (30s)."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http_class:
            mock_http = MagicMock()
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http_class.return_value = mock_http
            
            await mock_client.insert_leads_batch(sample_leads)
            
            # Verify AsyncClient was created with 60s timeout
            mock_http_class.assert_called_once_with(timeout=60.0)



class TestCheckDuplicate:
    """Test suite for check_duplicate method."""
    
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
    
    @pytest.mark.asyncio
    async def test_check_duplicate_exists(self, mock_client):
        """Test that check_duplicate returns True when lead exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 1}]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_duplicate_not_exists(self, mock_client):
        """Test that check_duplicate returns False when lead does not exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_when_disabled(self):
        """Test that check_duplicate returns False when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_missing_nome(self, mock_client):
        """Test that check_duplicate returns False when nome is missing."""
        result = await mock_client.check_duplicate(
            nome='',
            cidade='São Paulo, SP',
            url='https://www.google.com/maps/place/test'
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_missing_cidade(self, mock_client):
        """Test that check_duplicate returns False when cidade is missing."""
        result = await mock_client.check_duplicate(
            nome='Test Business',
            cidade='',
            url='https://www.google.com/maps/place/test'
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_missing_url(self, mock_client):
        """Test that check_duplicate returns False when url is missing."""
        result = await mock_client.check_duplicate(
            nome='Test Business',
            cidade='São Paulo, SP',
            url=''
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is False
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_http_error(self, mock_client):
        """Test that HTTP errors return False."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_network_error(self, mock_client):
        """Test that network errors return False."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError('Connection failed')
            )
            
            result = await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_unexpected_exception(self, mock_client):
        """Test that unexpected exceptions return False."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=ValueError('Unexpected error')
            )
            
            result = await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_duplicate_correct_query_params(self, mock_client):
        """Test that check_duplicate sends correct query parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            # Verify the call was made with correct parameters
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/gmap_leads'
            assert call_args[1]['params']['nome'] == 'eq.Test Business'
            assert call_args[1]['params']['cidade'] == 'eq.São Paulo, SP'
            assert call_args[1]['params']['url'] == 'eq.https://www.google.com/maps/place/test'
            assert call_args[1]['params']['select'] == 'id'
            assert call_args[1]['params']['limit'] == '1'
    
    @pytest.mark.asyncio
    async def test_check_duplicate_correct_headers(self, mock_client):
        """Test that check_duplicate sends correct headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await mock_client.check_duplicate(
                nome='Test Business',
                cidade='São Paulo, SP',
                url='https://www.google.com/maps/place/test'
            )
            
            # Verify headers
            call_args = mock_get.call_args
            assert call_args[1]['headers']['apikey'] == 'test-key'
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-key'
            assert call_args[1]['headers']['Content-Type'] == 'application/json'



class TestGetLeadsByTask:
    """Test suite for get_leads_by_task method."""
    
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
    def sample_leads_response(self):
        """Sample leads response from Supabase."""
        return [
            {
                'id': 1,
                'nome': 'Business 1',
                'telefone': '+55 11 98765-4321',
                'website': 'https://test1.com',
                'endereco': 'Rua Test 1, 123',
                'cidade': 'São Paulo, SP',
                'url': 'https://www.google.com/maps/place/test1',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-123',
                'created_at': '2024-01-15T10:00:00Z'
            },
            {
                'id': 2,
                'nome': 'Business 2',
                'telefone': '+55 21 98765-4321',
                'website': 'https://test2.com',
                'endereco': 'Rua Test 2, 456',
                'cidade': 'Rio de Janeiro, RJ',
                'url': 'https://www.google.com/maps/place/test2',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-123',
                'created_at': '2024-01-15T11:00:00Z'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_success(self, mock_client, sample_leads_response):
        """Test successful retrieval of leads by task_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_task('task-123')
            
            assert len(result) == 2
            assert result[0]['nome'] == 'Business 1'
            assert result[1]['nome'] == 'Business 2'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_empty_result(self, mock_client):
        """Test that empty results return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_task('nonexistent-task')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_when_disabled(self):
        """Test that query returns empty list when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.get_leads_by_task('task-123')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_missing_task_id(self, mock_client):
        """Test that missing task_id returns empty list."""
        result = await mock_client.get_leads_by_task('')
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_with_pagination(self, mock_client, sample_leads_response):
        """Test pagination parameters are passed correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_task('task-123', limit=50, offset=10)
            
            # Verify pagination parameters
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == '50'
            assert call_args[1]['params']['offset'] == '10'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_default_pagination(self, mock_client, sample_leads_response):
        """Test default pagination values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_task('task-123')
            
            # Verify default pagination
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == '100'
            assert call_args[1]['params']['offset'] == '0'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_invalid_limit(self, mock_client, sample_leads_response):
        """Test that invalid limit is corrected to default."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_task('task-123', limit=0)
            
            # Verify limit was corrected to default
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == '100'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_invalid_offset(self, mock_client, sample_leads_response):
        """Test that invalid offset is corrected to default."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_task('task-123', offset=-5)
            
            # Verify offset was corrected to default
            call_args = mock_get.call_args
            assert call_args[1]['params']['offset'] == '0'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_correct_query_params(self, mock_client, sample_leads_response):
        """Test that correct query parameters are sent."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await mock_client.get_leads_by_task('task-123')
            
            # Verify query parameters
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/gmap_leads'
            assert call_args[1]['params']['task_id'] == 'eq.task-123'
            assert call_args[1]['params']['select'] == '*'
            assert call_args[1]['params']['order'] == 'created_at.desc'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_task('task-123')
            
            assert result == []
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_http_error(self, mock_client):
        """Test that HTTP errors return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_task('task-123')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_network_error(self, mock_client):
        """Test that network errors return empty list."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError('Connection failed')
            )
            
            result = await mock_client.get_leads_by_task('task-123')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_task_unexpected_exception(self, mock_client):
        """Test that unexpected exceptions return empty list."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=ValueError('Unexpected error')
            )
            
            result = await mock_client.get_leads_by_task('task-123')
            
            assert result == []


class TestGetLeadsByLocationSet:
    """Test suite for get_leads_by_location_set method."""
    
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
    def sample_leads_response(self):
        """Sample leads response from Supabase."""
        return [
            {
                'id': 1,
                'nome': 'Business 1',
                'telefone': '+55 11 98765-4321',
                'website': 'https://test1.com',
                'endereco': 'Rua Test 1, 123',
                'cidade': 'São Paulo, SP',
                'url': 'https://www.google.com/maps/place/test1',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-123',
                'created_at': '2024-01-15T10:00:00Z'
            },
            {
                'id': 2,
                'nome': 'Business 2',
                'telefone': '+55 21 98765-4321',
                'website': 'https://test2.com',
                'endereco': 'Rua Test 2, 456',
                'cidade': 'Rio de Janeiro, RJ',
                'url': 'https://www.google.com/maps/place/test2',
                'conjunto_de_locais': 'Capitais do Brasil',
                'task_id': 'task-456',
                'created_at': '2024-01-15T11:00:00Z'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_success(self, mock_client, sample_leads_response):
        """Test successful retrieval of leads by location set."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            assert len(result) == 2
            assert result[0]['conjunto_de_locais'] == 'Capitais do Brasil'
            assert result[1]['conjunto_de_locais'] == 'Capitais do Brasil'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_empty_result(self, mock_client):
        """Test that empty results return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_location_set('Nonexistent Set')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_when_disabled(self):
        """Test that query returns empty list when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.get_leads_by_location_set('Capitais do Brasil')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_missing_location_set(self, mock_client):
        """Test that missing location_set returns empty list."""
        result = await mock_client.get_leads_by_location_set('')
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_with_pagination(self, mock_client, sample_leads_response):
        """Test pagination parameters are passed correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil', limit=50, offset=10)
            
            # Verify pagination parameters
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == '50'
            assert call_args[1]['params']['offset'] == '10'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_default_pagination(self, mock_client, sample_leads_response):
        """Test default pagination values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            # Verify default pagination
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == '100'
            assert call_args[1]['params']['offset'] == '0'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_invalid_limit(self, mock_client, sample_leads_response):
        """Test that invalid limit is corrected to default."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil', limit=-10)
            
            # Verify limit was corrected to default
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == '100'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_invalid_offset(self, mock_client, sample_leads_response):
        """Test that invalid offset is corrected to default."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil', offset=-5)
            
            # Verify offset was corrected to default
            call_args = mock_get.call_args
            assert call_args[1]['params']['offset'] == '0'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_correct_query_params(self, mock_client, sample_leads_response):
        """Test that correct query parameters are sent."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_leads_response
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            # Verify query parameters
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/gmap_leads'
            assert call_args[1]['params']['conjunto_de_locais'] == 'eq.Capitais do Brasil'
            assert call_args[1]['params']['select'] == '*'
            assert call_args[1]['params']['order'] == 'created_at.desc'
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            assert result == []
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_http_error(self, mock_client):
        """Test that HTTP errors return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_network_error(self, mock_client):
        """Test that network errors return empty list."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError('Connection failed')
            )
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_leads_by_location_set_unexpected_exception(self, mock_client):
        """Test that unexpected exceptions return empty list."""
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=ValueError('Unexpected error')
            )
            
            result = await mock_client.get_leads_by_location_set('Capitais do Brasil')
            
            assert result == []


class TestLocationSetsMethods:
    """Test suite for Location Sets methods."""
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_create_location_set_success(self):
        """Test successful location set creation."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        # Mock the upload and insert methods
        with patch.object(client, '_upload_location_file', new_callable=AsyncMock) as mock_upload, \
             patch.object(client, '_insert_location_set_metadata', new_callable=AsyncMock) as mock_insert:
            
            mock_upload.return_value = True
            mock_insert.return_value = {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test description',
                'file_path': 'some-uuid.json',
                'location_count': 3,
                'created_at': '2025-01-15T10:00:00Z'
            }
            
            result = await client.create_location_set(
                name='Test Set',
                description='Test description',
                locations=['City 1, ST', 'City 2, ST', 'City 3, ST']
            )
            
            assert result['name'] == 'Test Set'
            assert result['location_count'] == 3
            assert mock_upload.called
            assert mock_insert.called
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_create_location_set_validates_name_length(self):
        """Test that create_location_set validates name length."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        # Test name too short
        with pytest.raises(ValueError, match="name must be between 3 and 100 characters"):
            await client.create_location_set(
                name='AB',
                description='Test',
                locations=['City 1, ST']
            )
        
        # Test name too long
        with pytest.raises(ValueError, match="name must be between 3 and 100 characters"):
            await client.create_location_set(
                name='A' * 101,
                description='Test',
                locations=['City 1, ST']
            )
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_create_location_set_validates_description_length(self):
        """Test that create_location_set validates description length."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        # Test description too long
        with pytest.raises(ValueError, match="description must not exceed 500 characters"):
            await client.create_location_set(
                name='Test Set',
                description='A' * 501,
                locations=['City 1, ST']
            )
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_create_location_set_validates_empty_locations(self):
        """Test that create_location_set rejects empty locations array."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        # Test empty array
        with pytest.raises(ValueError, match="must contain at least one location"):
            await client.create_location_set(
                name='Test Set',
                description='Test',
                locations=[]
            )
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_create_location_set_trims_whitespace(self):
        """Test that create_location_set trims whitespace from locations."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with patch.object(client, '_upload_location_file', new_callable=AsyncMock) as mock_upload, \
             patch.object(client, '_insert_location_set_metadata', new_callable=AsyncMock) as mock_insert:
            
            mock_upload.return_value = True
            mock_insert.return_value = {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'some-uuid.json',
                'location_count': 2,
                'created_at': '2025-01-15T10:00:00Z'
            }
            
            await client.create_location_set(
                name='Test Set',
                description='Test',
                locations=['  City 1, ST  ', '  City 2, ST  ']
            )
            
            # Verify upload was called with trimmed locations
            upload_call_args = mock_upload.call_args
            uploaded_content = upload_call_args[0][1]  # Second positional arg is content
            assert uploaded_content['locais'] == ['City 1, ST', 'City 2, ST']
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_create_location_set_handles_duplicate_name(self):
        """Test that create_location_set handles duplicate name errors."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with patch.object(client, '_upload_location_file', new_callable=AsyncMock) as mock_upload, \
             patch.object(client, '_insert_location_set_metadata', new_callable=AsyncMock) as mock_insert, \
             patch.object(client, '_delete_location_file', new_callable=AsyncMock) as mock_delete:
            
            mock_upload.return_value = True
            mock_insert.side_effect = ValueError("Location set with name 'Test Set' already exists")
            mock_delete.return_value = True
            
            with pytest.raises(ValueError, match="already exists"):
                await client.create_location_set(
                    name='Test Set',
                    description='Test',
                    locations=['City 1, ST']
                )
            
            # Verify cleanup was attempted
            assert mock_delete.called
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True)
    async def test_create_location_set_fails_when_unavailable(self):
        """Test that create_location_set fails when Supabase is unavailable."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with pytest.raises(Exception, match="Supabase integration is disabled"):
            await client.create_location_set(
                name='Test Set',
                description='Test',
                locations=['City 1, ST']
            )

    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_get_all_location_sets_success(self):
        """Test successful retrieval of all location sets."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 'uuid-1',
                'name': 'Set 1',
                'description': 'Description 1',
                'file_path': 'uuid-1.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            },
            {
                'id': 'uuid-2',
                'name': 'Set 2',
                'description': 'Description 2',
                'file_path': 'uuid-2.json',
                'location_count': 5,
                'created_at': '2025-01-14T10:00:00Z'
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await client.get_all_location_sets()
            
            assert len(result) == 2
            assert result[0]['name'] == 'Set 1'
            assert result[1]['name'] == 'Set 2'
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_get_all_location_sets_empty_result(self):
        """Test that empty results return empty list."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await client.get_all_location_sets()
            
            assert result == []
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True)
    async def test_get_all_location_sets_fails_when_unavailable(self):
        """Test that get_all_location_sets fails when Supabase is unavailable."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with pytest.raises(Exception, match="Supabase integration is disabled"):
            await client.get_all_location_sets()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_get_all_location_sets_authentication_error(self):
        """Test that authentication errors disable the client."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception, match="Authentication error"):
                await client.get_all_location_sets()
            
            assert client.is_available() is False
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_get_all_location_sets_rate_limiting_with_retry(self):
        """Test that rate limiting triggers retry with exponential backoff."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        # First two attempts return 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = [
            {
                'id': 'uuid-1',
                'name': 'Set 1',
                'description': 'Description 1',
                'file_path': 'uuid-1.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_response_429, mock_response_429, mock_response_success])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await client.get_all_location_sets()
                
                assert len(result) == 1
                assert mock_get.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_get_all_location_sets_network_error_with_retry(self):
        """Test that network errors trigger retry with exponential backoff."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            # First two attempts raise network error, third succeeds
            mock_get = AsyncMock(side_effect=[
                httpx.ConnectError('Connection failed'),
                httpx.TimeoutException('Timeout'),
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await client.get_all_location_sets()
                
                assert result == []
                assert mock_get.call_count == 3
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    async def test_get_all_location_sets_correct_query_params(self):
        """Test that correct query parameters are sent."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            await client.get_all_location_sets()
            
            # Verify the call was made with correct parameters
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://test.supabase.co/rest/v1/location_sets'
            assert call_args[1]['params']['select'] == '*'
            assert call_args[1]['params']['order'] == 'created_at.desc'
            assert call_args[1]['headers']['apikey'] == 'test-key'
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-key'


class TestGetLocationSetPreview:
    """Test suite for get_location_set_preview method."""
    
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
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_success(self, mock_client):
        """Test successful preview retrieval with 10 locations."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test description',
                'file_path': 'test-uuid.json',
                'location_count': 15,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test description',
            'locais': [f'City {i}, ST' for i in range(15)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_location_set_preview('test-uuid')
            
            assert result['id'] == 'test-uuid'
            assert result['name'] == 'Test Set'
            assert len(result['preview']) == 10
            assert result['total_count'] == 15
            assert result['showing'] == 10
            assert result['preview'][0] == 'City 0, ST'
            assert result['preview'][9] == 'City 9, ST'
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_fewer_than_limit(self, mock_client):
        """Test preview with fewer locations than limit."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Small Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 5,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Small Set',
            'descricao': 'Test',
            'locais': ['City 1, ST', 'City 2, ST', 'City 3, ST', 'City 4, ST', 'City 5, ST']
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_location_set_preview('test-uuid')
            
            assert len(result['preview']) == 5
            assert result['total_count'] == 5
            assert result['showing'] == 5
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_custom_limit(self, mock_client):
        """Test preview with custom limit."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 20,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test',
            'locais': [f'City {i}, ST' for i in range(20)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_location_set_preview('test-uuid', limit=5)
            
            assert len(result['preview']) == 5
            assert result['total_count'] == 20
            assert result['showing'] == 5
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_not_found(self, mock_client):
        """Test preview when location set not found."""
        # Mock metadata response - empty result
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Location set not found"):
                await mock_client.get_location_set_preview('nonexistent-uuid')
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_file_not_found(self, mock_client):
        """Test preview when file not found in storage."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response - 404
        mock_file_response = MagicMock()
        mock_file_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Location file not found"):
                await mock_client.get_location_set_preview('test-uuid')
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_invalid_json(self, mock_client):
        """Test preview when file has invalid JSON structure."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response - missing 'locais' field
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test'
            # Missing 'locais' field
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Failed to parse location file"):
                await mock_client.get_location_set_preview('test-uuid')
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True)
    async def test_get_location_set_preview_fails_when_unavailable(self):
        """Test that preview fails when Supabase is unavailable."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with pytest.raises(Exception, match="Supabase integration is disabled"):
            await client.get_location_set_preview('test-uuid')
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response - 401
        mock_file_response = MagicMock()
        mock_file_response.status_code = 401
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Authentication error"):
                await mock_client.get_location_set_preview('test-uuid')
            
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_rate_limiting_with_retry(self, mock_client):
        """Test that rate limiting triggers retry with exponential backoff."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # First two file download attempts return 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test',
            'locais': [f'City {i}, ST' for i in range(10)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[
                mock_metadata_response,
                mock_response_429,
                mock_response_429,
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.get_location_set_preview('test-uuid')
                
                assert len(result['preview']) == 10
                assert mock_get.call_count == 4  # 1 metadata + 3 file attempts
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_get_location_set_preview_network_error_with_retry(self, mock_client):
        """Test that network errors trigger retry with exponential backoff."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test',
            'locais': [f'City {i}, ST' for i in range(10)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            # First two file download attempts raise network error, third succeeds
            mock_get = AsyncMock(side_effect=[
                mock_metadata_response,
                httpx.ConnectError('Connection failed'),
                httpx.TimeoutException('Timeout'),
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.get_location_set_preview('test-uuid')
                
                assert len(result['preview']) == 10
                assert mock_get.call_count == 4  # 1 metadata + 3 file attempts
                assert mock_sleep.call_count == 2  # Two retries



class TestGetLocationSetFull:
    """Test suite for get_location_set_full method."""
    
    @pytest.fixture
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    def mock_client(self):
        """Create a mock SupabaseClient for testing."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        return SupabaseClient()
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_success(self, mock_client):
        """Test successful full location set retrieval."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 50,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response with 50 locations
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test',
            'locais': [f'City {i}, ST' for i in range(50)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_location_set_full('test-uuid')
            
            assert result['id'] == 'test-uuid'
            assert result['name'] == 'Test Set'
            assert len(result['locations']) == 50
            assert result['total_count'] == 50
            assert result['locations'][0] == 'City 0, ST'
            assert result['locations'][49] == 'City 49, ST'
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_small_set(self, mock_client):
        """Test full retrieval with small location set."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Small Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 3,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response with 3 locations
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Small Set',
            'descricao': 'Test',
            'locais': ['São Paulo, SP', 'Rio de Janeiro, RJ', 'Belo Horizonte, MG']
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_location_set_full('test-uuid')
            
            assert len(result['locations']) == 3
            assert result['total_count'] == 3
            assert result['locations'] == ['São Paulo, SP', 'Rio de Janeiro, RJ', 'Belo Horizonte, MG']
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_not_found(self, mock_client):
        """Test full retrieval when location set not found."""
        # Mock metadata response - empty result
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Location set not found"):
                await mock_client.get_location_set_full('nonexistent-uuid')
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_file_not_found(self, mock_client):
        """Test full retrieval when file not found in storage."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response - 404
        mock_file_response = MagicMock()
        mock_file_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Location file not found"):
                await mock_client.get_location_set_full('test-uuid')
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_invalid_json(self, mock_client):
        """Test full retrieval when file has invalid JSON structure."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response - missing 'locais' field
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test'
            # Missing 'locais' field
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Failed to parse location file"):
                await mock_client.get_location_set_full('test-uuid')
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True)
    async def test_get_location_set_full_fails_when_unavailable(self):
        """Test that full retrieval fails when Supabase is unavailable."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with pytest.raises(Exception, match="Supabase integration is disabled"):
            await client.get_location_set_full('test-uuid')
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file download response - 401
        mock_file_response = MagicMock()
        mock_file_response.status_code = 401
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[mock_metadata_response, mock_file_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Authentication error"):
                await mock_client.get_location_set_full('test-uuid')
            
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_rate_limiting_with_retry(self, mock_client):
        """Test that rate limiting triggers retry with exponential backoff."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # First two file download attempts return 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test',
            'locais': [f'City {i}, ST' for i in range(10)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(side_effect=[
                mock_metadata_response,
                mock_response_429,
                mock_response_429,
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.get_location_set_full('test-uuid')
                
                assert len(result['locations']) == 10
                assert mock_get.call_count == 4  # 1 metadata + 3 file attempts
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_get_location_set_full_network_error_with_retry(self, mock_client):
        """Test that network errors trigger retry with exponential backoff."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'nome': 'Test Set',
            'descricao': 'Test',
            'locais': [f'City {i}, ST' for i in range(10)]
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            # First two file download attempts raise network error, third succeeds
            mock_get = AsyncMock(side_effect=[
                mock_metadata_response,
                httpx.ConnectError('Connection failed'),
                httpx.TimeoutException('Timeout'),
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.get_location_set_full('test-uuid')
                
                assert len(result['locations']) == 10
                assert mock_get.call_count == 4  # 1 metadata + 3 file attempts
                assert mock_sleep.call_count == 2  # Two retries



class TestDeleteLocationSet:
    """Test suite for delete_location_set method."""
    
    @pytest.fixture
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'})
    def mock_client(self):
        """Create a mock SupabaseClient for testing."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        return SupabaseClient()
    
    @pytest.mark.asyncio
    async def test_delete_location_set_success(self, mock_client):
        """Test successful location set deletion."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock delete responses
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_delete = AsyncMock(return_value=mock_delete_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            mock_http.return_value.__aenter__.return_value.delete = mock_delete
            
            result = await mock_client.delete_location_set('test-uuid')
            
            assert result is True
            assert mock_get.call_count == 1  # Metadata fetch
            assert mock_delete.call_count == 2  # File delete + DB delete
    
    @pytest.mark.asyncio
    async def test_delete_location_set_file_deletion_fails_gracefully(self, mock_client):
        """Test that database deletion proceeds even if file deletion fails."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file delete failure, DB delete success
        mock_file_delete_response = MagicMock()
        mock_file_delete_response.status_code = 500
        
        mock_db_delete_response = MagicMock()
        mock_db_delete_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_delete = AsyncMock(side_effect=[mock_file_delete_response, mock_db_delete_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            mock_http.return_value.__aenter__.return_value.delete = mock_delete
            
            result = await mock_client.delete_location_set('test-uuid')
            
            assert result is True
            assert mock_delete.call_count == 2  # File delete (failed) + DB delete (succeeded)
    
    @pytest.mark.asyncio
    async def test_delete_location_set_not_found(self, mock_client):
        """Test deletion when location set not found."""
        # Mock metadata response - empty result
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(Exception, match="Location set not found"):
                await mock_client.delete_location_set('test-uuid')
    
    @pytest.mark.asyncio
    async def test_delete_location_set_database_deletion_fails(self, mock_client):
        """Test that database deletion failure raises exception."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file delete success, DB delete failure
        mock_file_delete_response = MagicMock()
        mock_file_delete_response.status_code = 204
        
        mock_db_delete_response = MagicMock()
        mock_db_delete_response.status_code = 500
        mock_db_delete_response.text = 'Internal server error'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_delete = AsyncMock(side_effect=[mock_file_delete_response, mock_db_delete_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            mock_http.return_value.__aenter__.return_value.delete = mock_delete
            
            with pytest.raises(Exception, match="HTTP error 500"):
                await mock_client.delete_location_set('test-uuid')
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True)
    async def test_delete_location_set_fails_when_unavailable(self):
        """Test that deletion fails when Supabase is unavailable."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        client = SupabaseClient()
        
        with pytest.raises(Exception, match="Supabase integration is disabled"):
            await client.delete_location_set('test-uuid')
    
    @pytest.mark.asyncio
    async def test_delete_location_set_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file delete success, DB delete auth error
        mock_file_delete_response = MagicMock()
        mock_file_delete_response.status_code = 204
        
        mock_db_delete_response = MagicMock()
        mock_db_delete_response.status_code = 401
        mock_db_delete_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_delete = AsyncMock(side_effect=[mock_file_delete_response, mock_db_delete_response])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            mock_http.return_value.__aenter__.return_value.delete = mock_delete
            
            with pytest.raises(Exception, match="Authentication error"):
                await mock_client.delete_location_set('test-uuid')
            
            assert not mock_client.is_available()
    
    @pytest.mark.asyncio
    async def test_delete_location_set_rate_limiting_with_retry(self, mock_client):
        """Test that rate limiting triggers retry with exponential backoff."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file delete success
        mock_file_delete_response = MagicMock()
        mock_file_delete_response.status_code = 204
        
        # Mock DB delete with rate limiting then success
        mock_rate_limit_response = MagicMock()
        mock_rate_limit_response.status_code = 429
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_delete = AsyncMock(side_effect=[
                mock_file_delete_response,
                mock_rate_limit_response,
                mock_rate_limit_response,
                mock_success_response
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            mock_http.return_value.__aenter__.return_value.delete = mock_delete
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.delete_location_set('test-uuid')
                
                assert result is True
                assert mock_delete.call_count == 4  # File + 3 DB attempts
                assert mock_sleep.call_count == 2  # Two retries
    
    @pytest.mark.asyncio
    async def test_delete_location_set_network_error_with_retry(self, mock_client):
        """Test that network errors trigger retry with exponential backoff."""
        # Mock metadata response
        mock_metadata_response = MagicMock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = [
            {
                'id': 'test-uuid',
                'name': 'Test Set',
                'description': 'Test',
                'file_path': 'test-uuid.json',
                'location_count': 10,
                'created_at': '2025-01-15T10:00:00Z'
            }
        ]
        
        # Mock file delete success
        mock_file_delete_response = MagicMock()
        mock_file_delete_response.status_code = 204
        
        # Mock DB delete with network errors then success
        mock_success_response = MagicMock()
        mock_success_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_metadata_response)
            mock_delete = AsyncMock(side_effect=[
                mock_file_delete_response,
                httpx.ConnectError('Connection failed'),
                httpx.TimeoutException('Timeout'),
                mock_success_response
            ])
            mock_http.return_value.__aenter__.return_value.get = mock_get
            mock_http.return_value.__aenter__.return_value.delete = mock_delete
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.delete_location_set('test-uuid')
                
                assert result is True
                assert mock_delete.call_count == 4  # File + 3 DB attempts
                assert mock_sleep.call_count == 2  # Two retries
