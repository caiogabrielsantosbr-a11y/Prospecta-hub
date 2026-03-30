"""
Integration tests for task methods - requires actual Supabase connection.
Run these tests only when SUPABASE_URL and SUPABASE_KEY are configured.
"""
import os
import pytest
from database.supabase_client import SupabaseClient


@pytest.mark.skipif(
    not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'),
    reason="Supabase credentials not configured"
)
class TestTasksIntegration:
    """Integration tests for task CRUD operations."""
    
    @pytest.fixture
    def client(self):
        """Get Supabase client instance."""
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        return SupabaseClient()
    
    @pytest.mark.asyncio
    async def test_task_crud_lifecycle(self, client):
        """Test complete CRUD lifecycle for a task."""
        if not client.is_available():
            pytest.skip("Supabase client not available")
        
        # 1. Insert a task
        task_data = {
            'id': 'test-task-integration-001',
            'module': 'gmap',
            'status': 'running',
            'config': {'location': 'São Paulo', 'keywords': 'restaurante'},
            'stats': {'leads_found': 0, 'leads_saved': 0},
            'progress': 0.0
        }
        
        insert_result = await client.insert_task(task_data)
        assert insert_result is True, "Task insertion failed"
        
        # 2. Get the task
        retrieved_task = await client.get_task('test-task-integration-001')
        assert retrieved_task is not None, "Task retrieval failed"
        assert retrieved_task['id'] == 'test-task-integration-001'
        assert retrieved_task['module'] == 'gmap'
        assert retrieved_task['status'] == 'running'
        
        # 3. Update the task
        update_result = await client.update_task(
            'test-task-integration-001',
            {
                'status': 'completed',
                'progress': 100.0,
                'stats': {'leads_found': 50, 'leads_saved': 48}
            }
        )
        assert update_result is True, "Task update failed"
        
        # 4. Verify the update
        updated_task = await client.get_task('test-task-integration-001')
        assert updated_task is not None
        assert updated_task['status'] == 'completed'
        assert updated_task['progress'] == 100.0
        assert updated_task['stats']['leads_found'] == 50
        
        # 5. Get all tasks (should include our test task)
        all_tasks = await client.get_all_tasks()
        assert len(all_tasks) > 0
        assert any(task['id'] == 'test-task-integration-001' for task in all_tasks)
        
        # 6. Get tasks by module
        gmap_tasks = await client.get_tasks_by_module('gmap')
        assert len(gmap_tasks) > 0
        assert any(task['id'] == 'test-task-integration-001' for task in gmap_tasks)
        assert all(task['module'] == 'gmap' for task in gmap_tasks)
        
        print("✓ All task CRUD operations completed successfully")
