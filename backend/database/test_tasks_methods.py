"""
Unit tests for Supabase client task methods.
"""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from database.supabase_client import SupabaseClient
import httpx


class TestInsertTask:
    """Test suite for insert_task method."""
    
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
    def sample_task(self):
        """Sample task data for testing."""
        return {
            'id': 'task-123',
            'module': 'gmap',
            'status': 'running',
            'config': {'location': 'São Paulo'},
            'stats': {'leads_found': 10},
            'progress': 25.5
        }
    
    @pytest.mark.asyncio
    async def test_insert_task_success(self, mock_client, sample_task):
        """Test successful task insertion."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mock_client.insert_task(sample_task)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_insert_task_when_disabled(self, sample_task):
        """Test that insert_task returns False when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.insert_task(sample_task)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_task_missing_id(self, mock_client):
        """Test that insert_task fails when 'id' field is missing."""
        task_without_id = {
            'module': 'gmap',
            'status': 'running'
        }
        
        result = await mock_client.insert_task(task_without_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_task_missing_module(self, mock_client):
        """Test that insert_task fails when 'module' field is missing."""
        task_without_module = {
            'id': 'task-123',
            'status': 'running'
        }
        
        result = await mock_client.insert_task(task_without_module)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_insert_task_with_defaults(self, mock_client):
        """Test that insert_task applies default values correctly."""
        minimal_task = {
            'id': 'task-123',
            'module': 'gmap'
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            result = await mock_client.insert_task(minimal_task)
            
            assert result is True
            
            # Verify defaults were applied
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['status'] == 'running'
            assert payload['config'] == {}
            assert payload['stats'] == {}
            assert payload['progress'] == 0.0
    
    @pytest.mark.asyncio
    async def test_insert_task_authentication_error(self, mock_client, sample_task):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await mock_client.insert_task(sample_task)
            
            assert result is False
            assert mock_client.is_available() is False
    
    @pytest.mark.asyncio
    async def test_insert_task_rate_limiting_with_retry(self, mock_client, sample_task):
        """Test that rate limiting triggers retry with exponential backoff."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(side_effect=[mock_response_429, mock_response_success])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.insert_task(sample_task)
                
                assert result is True
                assert mock_post.call_count == 2
                assert mock_sleep.call_count == 1
    
    @pytest.mark.asyncio
    async def test_insert_task_network_error_with_retry(self, mock_client, sample_task):
        """Test that network errors trigger retry with exponential backoff."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 201
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_post = AsyncMock(side_effect=[
                httpx.ConnectError('Connection failed'),
                mock_response_success
            ])
            mock_http.return_value.__aenter__.return_value.post = mock_post
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await mock_client.insert_task(sample_task)
                
                assert result is True
                assert mock_post.call_count == 2
                assert mock_sleep.call_count == 1


class TestUpdateTask:
    """Test suite for update_task method."""
    
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
    async def test_update_task_success(self, mock_client):
        """Test successful task update."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
            
            result = await mock_client.update_task('task-123', {'status': 'completed'})
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_task_when_disabled(self):
        """Test that update_task returns False when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.update_task('task-123', {'status': 'completed'})
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_update_task_missing_task_id(self, mock_client):
        """Test that update_task fails when task_id is missing."""
        result = await mock_client.update_task('', {'status': 'completed'})
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_task_empty_updates(self, mock_client):
        """Test that update_task returns True when no updates provided."""
        result = await mock_client.update_task('task-123', {})
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_task_filters_invalid_fields(self, mock_client):
        """Test that update_task only updates allowed fields."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_patch = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.patch = mock_patch
            
            # Try to update with invalid fields
            updates = {
                'status': 'completed',
                'progress': 100.0,
                'invalid_field': 'should be filtered',
                'id': 'should not change'
            }
            
            result = await mock_client.update_task('task-123', updates)
            
            assert result is True
            
            # Verify only allowed fields were sent
            call_args = mock_patch.call_args
            payload = call_args[1]['json']
            assert 'status' in payload
            assert 'progress' in payload
            assert 'updated_at' in payload
            assert 'invalid_field' not in payload
            assert 'id' not in payload
    
    @pytest.mark.asyncio
    async def test_update_task_adds_updated_at(self, mock_client):
        """Test that update_task automatically adds updated_at timestamp."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_patch = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.patch = mock_patch
            
            result = await mock_client.update_task('task-123', {'status': 'completed'})
            
            assert result is True
            
            # Verify updated_at was added
            call_args = mock_patch.call_args
            payload = call_args[1]['json']
            assert 'updated_at' in payload
    
    @pytest.mark.asyncio
    async def test_update_task_authentication_error(self, mock_client):
        """Test that authentication errors disable the client."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
            
            result = await mock_client.update_task('task-123', {'status': 'completed'})
            
            assert result is False
            assert mock_client.is_available() is False


class TestGetTask:
    """Test suite for get_task method."""
    
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
    async def test_get_task_success(self, mock_client):
        """Test successful task retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'id': 'task-123',
            'module': 'gmap',
            'status': 'running',
            'config': {},
            'stats': {},
            'progress': 0.0
        }]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_task('task-123')
            
            assert result is not None
            assert result['id'] == 'task-123'
            assert result['module'] == 'gmap'
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_client):
        """Test that get_task returns None when task doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_task('nonexistent-task')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_task_when_disabled(self):
        """Test that get_task returns None when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.get_task('task-123')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_task_missing_task_id(self, mock_client):
        """Test that get_task fails when task_id is missing."""
        result = await mock_client.get_task('')
        
        assert result is None


class TestGetAllTasks:
    """Test suite for get_all_tasks method."""
    
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
    async def test_get_all_tasks_success(self, mock_client):
        """Test successful retrieval of all tasks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 'task-1', 'module': 'gmap', 'status': 'running'},
            {'id': 'task-2', 'module': 'facebook', 'status': 'completed'},
            {'id': 'task-3', 'module': 'email_dispatch', 'status': 'paused'}
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_all_tasks()
            
            assert len(result) == 3
            assert result[0]['id'] == 'task-1'
            assert result[1]['id'] == 'task-2'
            assert result[2]['id'] == 'task-3'
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_empty(self, mock_client):
        """Test that get_all_tasks returns empty list when no tasks exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_all_tasks()
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_when_disabled(self):
        """Test that get_all_tasks returns empty list when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.get_all_tasks()
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_with_pagination(self, mock_client):
        """Test that get_all_tasks supports pagination."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 'task-11', 'module': 'gmap', 'status': 'running'}
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_all_tasks(limit=10, offset=10)
            
            assert len(result) == 1
            
            # Verify pagination parameters were sent
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['limit'] == '10'
            assert params['offset'] == '10'


class TestGetTasksByModule:
    """Test suite for get_tasks_by_module method."""
    
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
    async def test_get_tasks_by_module_success(self, mock_client):
        """Test successful retrieval of tasks by module."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 'task-1', 'module': 'gmap', 'status': 'running'},
            {'id': 'task-2', 'module': 'gmap', 'status': 'completed'}
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_tasks_by_module('gmap')
            
            assert len(result) == 2
            assert all(task['module'] == 'gmap' for task in result)
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_module_empty(self, mock_client):
        """Test that get_tasks_by_module returns empty list when no tasks exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await mock_client.get_tasks_by_module('facebook')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_module_when_disabled(self):
        """Test that get_tasks_by_module returns empty list when client is disabled."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            result = await client.get_tasks_by_module('gmap')
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_module_missing_module(self, mock_client):
        """Test that get_tasks_by_module fails when module is missing."""
        result = await mock_client.get_tasks_by_module('')
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_module_with_pagination(self, mock_client):
        """Test that get_tasks_by_module supports pagination."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 'task-11', 'module': 'gmap', 'status': 'running'}
        ]
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_get = AsyncMock(return_value=mock_response)
            mock_http.return_value.__aenter__.return_value.get = mock_get
            
            result = await mock_client.get_tasks_by_module('gmap', limit=10, offset=10)
            
            assert len(result) == 1
            
            # Verify pagination parameters were sent
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['module'] == 'eq.gmap'
            assert params['limit'] == '10'
            assert params['offset'] == '10'
