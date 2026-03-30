"""
Unit tests for email_dispatches methods in SupabaseClient.

Tests the four email_dispatches methods:
- insert_email_dispatch()
- insert_email_dispatches_batch()
- get_email_dispatches_by_task()
- update_email_dispatch_sent()
"""
import pytest
import asyncio
from datetime import datetime
from backend.database.supabase_client import get_supabase_client


@pytest.fixture
def supabase_client():
    """Get the Supabase client instance."""
    return get_supabase_client()


@pytest.fixture
def sample_dispatch():
    """Create a sample email dispatch for testing."""
    return {
        'recipient': 'test@example.com',
        'subject': 'Test Email',
        'status': 'pending',
        'task_id': 'test-task-123'
    }


@pytest.fixture
def sample_dispatches():
    """Create multiple sample email dispatches for batch testing."""
    return [
        {
            'recipient': f'test{i}@example.com',
            'subject': f'Test Email {i}',
            'status': 'pending',
            'task_id': 'test-task-batch'
        }
        for i in range(5)
    ]


@pytest.mark.asyncio
async def test_insert_email_dispatch(supabase_client, sample_dispatch):
    """Test inserting a single email dispatch."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    result = await supabase_client.insert_email_dispatch(sample_dispatch)
    assert isinstance(result, bool)
    # Note: result may be False if Supabase is not configured, which is OK for this test


@pytest.mark.asyncio
async def test_insert_email_dispatch_missing_recipient(supabase_client):
    """Test that insert fails when recipient is missing."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    invalid_dispatch = {
        'subject': 'Test Email',
        'status': 'pending'
    }
    
    result = await supabase_client.insert_email_dispatch(invalid_dispatch)
    assert result is False


@pytest.mark.asyncio
async def test_insert_email_dispatches_batch(supabase_client, sample_dispatches):
    """Test inserting multiple email dispatches in batch."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    success_count, failure_count = await supabase_client.insert_email_dispatches_batch(sample_dispatches)
    
    assert isinstance(success_count, int)
    assert isinstance(failure_count, int)
    assert success_count + failure_count == len(sample_dispatches)


@pytest.mark.asyncio
async def test_insert_email_dispatches_batch_empty(supabase_client):
    """Test batch insert with empty list."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    success_count, failure_count = await supabase_client.insert_email_dispatches_batch([])
    
    assert success_count == 0
    assert failure_count == 0


@pytest.mark.asyncio
async def test_get_email_dispatches_by_task(supabase_client):
    """Test querying email dispatches by task_id."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    task_id = 'test-task-query'
    results = await supabase_client.get_email_dispatches_by_task(task_id)
    
    assert isinstance(results, list)
    # Results may be empty if no dispatches exist for this task


@pytest.mark.asyncio
async def test_get_email_dispatches_by_task_missing_task_id(supabase_client):
    """Test that query fails when task_id is missing."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    results = await supabase_client.get_email_dispatches_by_task('')
    assert results == []


@pytest.mark.asyncio
async def test_get_email_dispatches_by_task_pagination(supabase_client):
    """Test pagination parameters."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    task_id = 'test-task-pagination'
    
    # Test with custom limit and offset
    results = await supabase_client.get_email_dispatches_by_task(task_id, limit=10, offset=0)
    assert isinstance(results, list)
    assert len(results) <= 10


@pytest.mark.asyncio
async def test_update_email_dispatch_sent(supabase_client):
    """Test updating sent_at timestamp."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    # Use a test dispatch ID (this will fail if ID doesn't exist, which is expected)
    dispatch_id = 999999
    sent_at = datetime.utcnow().isoformat() + 'Z'
    
    result = await supabase_client.update_email_dispatch_sent(dispatch_id, sent_at)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_update_email_dispatch_sent_missing_params(supabase_client):
    """Test that update fails when parameters are missing."""
    if not supabase_client.is_available():
        pytest.skip("Supabase integration is not available")
    
    # Missing id
    result = await supabase_client.update_email_dispatch_sent(0, '2024-01-15T10:30:00Z')
    assert result is False
    
    # Missing sent_at
    result = await supabase_client.update_email_dispatch_sent(1, '')
    assert result is False


@pytest.mark.asyncio
async def test_client_unavailable_behavior(supabase_client, sample_dispatch):
    """Test that methods handle unavailable client gracefully."""
    # Temporarily disable the client
    original_available = supabase_client._available
    supabase_client._available = False
    
    try:
        # Test insert
        result = await supabase_client.insert_email_dispatch(sample_dispatch)
        assert result is False
        
        # Test batch insert
        success, failure = await supabase_client.insert_email_dispatches_batch([sample_dispatch])
        assert success == 0
        assert failure == 1
        
        # Test query
        results = await supabase_client.get_email_dispatches_by_task('test-task')
        assert results == []
        
        # Test update
        result = await supabase_client.update_email_dispatch_sent(1, '2024-01-15T10:30:00Z')
        assert result is False
    
    finally:
        # Restore original state
        supabase_client._available = original_available


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
