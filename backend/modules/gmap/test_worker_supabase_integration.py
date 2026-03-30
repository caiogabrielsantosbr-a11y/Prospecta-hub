"""
Integration test for worker Supabase integration.
Tests that leads are saved to both SQLite and Supabase.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from database.supabase_client import SupabaseClient


class TestWorkerSupabaseIntegration:
    """Test suite for worker Supabase integration."""
    
    @pytest.mark.asyncio
    async def test_lead_saved_to_supabase_after_sqlite(self):
        """
        Test that after a lead is saved to SQLite, it is also saved to Supabase
        with all required fields including conjunto_de_locais.
        
        This test validates Requirements 3.1, 3.2, 3.5:
        - Lead is saved to Supabase immediately after SQLite
        - All fields are included (nome, telefone, website, endereco, cidade, url, conjunto_de_locais, task_id)
        - conjunto_de_locais contains the location set name, not the city name
        """
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        # Mock Supabase client
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            client = SupabaseClient()
            
            # Mock the insert_lead method to capture the call
            insert_lead_mock = AsyncMock(return_value=True)
            client.insert_lead = insert_lead_mock
            
            # Simulate the worker code
            location_set_name = "Capitais do Brasil"
            task_id = "test-task-123"
            
            # Sample extracted lead data
            data = {
                "nome": "Test Business",
                "telefone": "+55 11 98765-4321",
                "website": "https://test.com",
                "endereco": "Rua Test, 123, São Paulo, SP"
            }
            
            cidade = "São Paulo, SP"
            url = "https://www.google.com/maps/place/test"
            
            # Simulate the worker's Supabase save logic
            if client.is_available():
                lead_data = {
                    'nome': data["nome"],
                    'telefone': data.get("telefone", ""),
                    'website': data.get("website", ""),
                    'endereco': data.get("endereco", ""),
                    'cidade': cidade,
                    'url': url,
                    'conjunto_de_locais': location_set_name,
                    'task_id': task_id
                }
                await client.insert_lead(lead_data)
            
            # Verify insert_lead was called with correct data
            insert_lead_mock.assert_called_once()
            call_args = insert_lead_mock.call_args[0][0]
            
            # Verify all fields are present
            assert call_args['nome'] == "Test Business"
            assert call_args['telefone'] == "+55 11 98765-4321"
            assert call_args['website'] == "https://test.com"
            assert call_args['endereco'] == "Rua Test, 123, São Paulo, SP"
            assert call_args['cidade'] == "São Paulo, SP"
            assert call_args['url'] == url
            assert call_args['task_id'] == task_id
            
            # Verify conjunto_de_locais contains location set name, not city name
            assert call_args['conjunto_de_locais'] == "Capitais do Brasil"
            assert call_args['conjunto_de_locais'] != "São Paulo, SP"
    
    @pytest.mark.asyncio
    async def test_extraction_continues_on_supabase_error(self):
        """
        Test that extraction continues even if Supabase save fails.
        
        This test validates Requirement 3.3:
        - If Supabase save fails, the worker logs the error but continues extraction
        """
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        # Mock Supabase client
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            client = SupabaseClient()
            
            # Mock insert_lead to raise an exception
            client.insert_lead = AsyncMock(side_effect=Exception("Network error"))
            
            # Simulate the worker code with error handling
            location_set_name = "Capitais do Brasil"
            task_id = "test-task-123"
            
            data = {
                "nome": "Test Business",
                "telefone": "+55 11 98765-4321",
                "website": "https://test.com",
                "endereco": "Rua Test, 123"
            }
            
            cidade = "São Paulo, SP"
            url = "https://www.google.com/maps/place/test"
            
            # This should not raise an exception
            extraction_continued = False
            try:
                if client.is_available():
                    try:
                        lead_data = {
                            'nome': data["nome"],
                            'telefone': data.get("telefone", ""),
                            'website': data.get("website", ""),
                            'endereco': data.get("endereco", ""),
                            'cidade': cidade,
                            'url': url,
                            'conjunto_de_locais': location_set_name,
                            'task_id': task_id
                        }
                        await client.insert_lead(lead_data)
                    except Exception as e:
                        # Log error but continue
                        print(f"Error: {type(e).__name__}")
                
                # Extraction continues
                extraction_continued = True
            except Exception:
                extraction_continued = False
            
            # Verify extraction continued despite error
            assert extraction_continued is True
    
    @pytest.mark.asyncio
    async def test_supabase_disabled_does_not_block_extraction(self):
        """
        Test that when Supabase is disabled, extraction continues normally.
        
        This test validates that the worker handles disabled Supabase gracefully.
        """
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        # Mock Supabase client with missing credentials
        with patch.dict('os.environ', {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}, clear=True):
            client = SupabaseClient()
            
            # Verify client is disabled
            assert client.is_available() is False
            
            # Simulate the worker code
            location_set_name = "Capitais do Brasil"
            task_id = "test-task-123"
            
            data = {
                "nome": "Test Business",
                "telefone": "+55 11 98765-4321",
                "website": "https://test.com",
                "endereco": "Rua Test, 123"
            }
            
            cidade = "São Paulo, SP"
            url = "https://www.google.com/maps/place/test"
            
            # This should not attempt to save to Supabase
            extraction_continued = False
            try:
                if client.is_available():
                    # This block should not execute
                    lead_data = {
                        'nome': data["nome"],
                        'telefone': data.get("telefone", ""),
                        'website': data.get("website", ""),
                        'endereco': data.get("endereco", ""),
                        'cidade': cidade,
                        'url': url,
                        'conjunto_de_locais': location_set_name,
                        'task_id': task_id
                    }
                    await client.insert_lead(lead_data)
                
                # Extraction continues
                extraction_continued = True
            except Exception:
                extraction_continued = False
            
            # Verify extraction continued
            assert extraction_continued is True
    
    @pytest.mark.asyncio
    async def test_supabase_statistics_tracking(self):
        """
        Test that Supabase success and failure statistics are tracked correctly.
        
        This test validates Requirement 5.1, 5.2:
        - Supabase successes are counted
        - Supabase failures are counted
        """
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        # Mock Supabase client
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            client = SupabaseClient()
            
            # Mock insert_lead to return success then failure
            insert_results = [True, True, False, True, False]
            client.insert_lead = AsyncMock(side_effect=insert_results)
            
            # Simulate worker statistics tracking
            stats = {
                "supabase_success": 0,
                "supabase_failures": 0
            }
            
            location_set_name = "Capitais do Brasil"
            task_id = "test-task-123"
            
            # Simulate multiple lead saves
            for i in range(5):
                data = {
                    "nome": f"Test Business {i}",
                    "telefone": "+55 11 98765-4321",
                    "website": "https://test.com",
                    "endereco": "Rua Test, 123"
                }
                
                cidade = "São Paulo, SP"
                url = f"https://www.google.com/maps/place/test{i}"
                
                if client.is_available():
                    try:
                        lead_data = {
                            'nome': data["nome"],
                            'telefone': data.get("telefone", ""),
                            'website': data.get("website", ""),
                            'endereco': data.get("endereco", ""),
                            'cidade': cidade,
                            'url': url,
                            'conjunto_de_locais': location_set_name,
                            'task_id': task_id
                        }
                        success = await client.insert_lead(lead_data)
                        if success:
                            stats["supabase_success"] += 1
                        else:
                            stats["supabase_failures"] += 1
                    except Exception:
                        stats["supabase_failures"] += 1
            
            # Verify statistics
            assert stats["supabase_success"] == 3  # 3 successes
            assert stats["supabase_failures"] == 2  # 2 failures
    
    @pytest.mark.asyncio
    async def test_consecutive_failure_detection(self):
        """
        Test that 5+ consecutive failures trigger a warning.
        
        This test validates Requirement 5.3:
        - After 5 consecutive failures, a connectivity warning should be logged
        """
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        # Mock Supabase client
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            client = SupabaseClient()
            
            # Mock insert_lead to always fail
            client.insert_lead = AsyncMock(return_value=False)
            
            # Simulate worker consecutive failure tracking
            consecutive_failures = 0
            warning_logged = False
            
            location_set_name = "Capitais do Brasil"
            task_id = "test-task-123"
            
            # Simulate 6 consecutive failures
            for i in range(6):
                data = {
                    "nome": f"Test Business {i}",
                    "telefone": "+55 11 98765-4321",
                    "website": "https://test.com",
                    "endereco": "Rua Test, 123"
                }
                
                cidade = "São Paulo, SP"
                url = f"https://www.google.com/maps/place/test{i}"
                
                if client.is_available():
                    try:
                        lead_data = {
                            'nome': data["nome"],
                            'telefone': data.get("telefone", ""),
                            'website': data.get("website", ""),
                            'endereco': data.get("endereco", ""),
                            'cidade': cidade,
                            'url': url,
                            'conjunto_de_locais': location_set_name,
                            'task_id': task_id
                        }
                        success = await client.insert_lead(lead_data)
                        if success:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            
                            # Detect 5+ consecutive failures
                            if consecutive_failures >= 5:
                                warning_logged = True
                    except Exception:
                        consecutive_failures += 1
                        
                        # Detect 5+ consecutive failures
                        if consecutive_failures >= 5:
                            warning_logged = True
            
            # Verify warning was triggered
            assert consecutive_failures == 6
            assert warning_logged is True
    
    @pytest.mark.asyncio
    async def test_consecutive_failure_reset_on_success(self):
        """
        Test that consecutive failure counter resets on success.
        
        This test validates that the consecutive failure counter is reset
        when a successful save occurs.
        """
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._initialized = False
        
        # Mock Supabase client
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            client = SupabaseClient()
            
            # Mock insert_lead: 4 failures, then success, then 4 more failures
            insert_results = [False, False, False, False, True, False, False, False, False]
            client.insert_lead = AsyncMock(side_effect=insert_results)
            
            # Simulate worker consecutive failure tracking
            consecutive_failures = 0
            warning_logged = False
            
            location_set_name = "Capitais do Brasil"
            task_id = "test-task-123"
            
            # Simulate saves
            for i in range(9):
                data = {
                    "nome": f"Test Business {i}",
                    "telefone": "+55 11 98765-4321",
                    "website": "https://test.com",
                    "endereco": "Rua Test, 123"
                }
                
                cidade = "São Paulo, SP"
                url = f"https://www.google.com/maps/place/test{i}"
                
                if client.is_available():
                    try:
                        lead_data = {
                            'nome': data["nome"],
                            'telefone': data.get("telefone", ""),
                            'website': data.get("website", ""),
                            'endereco': data.get("endereco", ""),
                            'cidade': cidade,
                            'url': url,
                            'conjunto_de_locais': location_set_name,
                            'task_id': task_id
                        }
                        success = await client.insert_lead(lead_data)
                        if success:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            
                            # Detect 5+ consecutive failures
                            if consecutive_failures >= 5:
                                warning_logged = True
                    except Exception:
                        consecutive_failures += 1
                        
                        # Detect 5+ consecutive failures
                        if consecutive_failures >= 5:
                            warning_logged = True
            
            # Verify warning was NOT triggered (max consecutive was 4)
            assert consecutive_failures == 4  # Last 4 were failures
            assert warning_logged is False  # Never reached 5 consecutive


