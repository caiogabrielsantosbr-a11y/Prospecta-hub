"""
Supabase client module for GMap Supabase Integration.

This module provides a singleton Supabase client for interacting with the
Supabase database. It handles credential validation, connection management,
and provides methods for CRUD operations on the gmap_leads table.
"""
import os
import logging
import asyncio
import random
import uuid
import json
from typing import Optional
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Singleton Supabase client for managing cloud database operations.
    
    This client handles:
    - Credential validation and initialization
    - Connection management
    - CRUD operations on gmap_leads table
    - Error handling and logging
    """
    
    _instance: Optional['SupabaseClient'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize the Supabase client with credentials from environment.
        
        Validates that SUPABASE_URL and SUPABASE_KEY are present.
        If credentials are missing, logs a warning and disables integration.
        """
        # Only initialize once
        if self._initialized:
            return
            
        self._initialized = True
        self._available = False
        self._url: Optional[str] = None
        self._key: Optional[str] = None
        self._service_key: Optional[str] = None

        # Read credentials from environment
        self._url = os.getenv('SUPABASE_URL', '').strip()
        self._key = os.getenv('SUPABASE_KEY', '').strip()
        # Service role key bypasses RLS for server-side writes; falls back to anon key
        self._service_key = os.getenv('SUPABASE_SERVICE_KEY', '').strip() or self._key

        # Validate credentials
        if not self._url or not self._key:
            missing = []
            if not self._url:
                missing.append('SUPABASE_URL')
            if not self._key:
                missing.append('SUPABASE_KEY')
            
            logger.warning(
                f"Supabase credentials missing: {', '.join(missing)}. "
                "Supabase integration is disabled. "
                "Please set these environment variables in .env file to enable cloud sync."
            )
            return
        
        # Mark as available if credentials are present
        self._available = True
        logger.info("Supabase client initialized successfully")
    
    def is_available(self) -> bool:
        """
        Check if Supabase integration is available.
        
        Returns:
            bool: True if credentials are valid and client is ready, False otherwise
        """
        return self._available
    
    def get_url(self) -> Optional[str]:
        """
        Get the Supabase URL.
        
        Returns:
            Optional[str]: The Supabase URL if available, None otherwise
        """
        return self._url if self._available else None
    
    def get_key(self) -> Optional[str]:
        """
        Get the Supabase API key.
        
        Returns:
            Optional[str]: The Supabase API key if available, None otherwise
        """
        return self._key if self._available else None
    
    def disable(self):
        """
        Disable Supabase integration.
        
        Called when authentication errors occur to prevent further attempts.
        """
        self._available = False
        logger.error(
            "Supabase integration has been disabled due to authentication errors. "
            "Please verify your SUPABASE_URL and SUPABASE_KEY credentials."
        )
    
    def reload_credentials(self):
        """
        Reload credentials from environment variables.
        
        Useful when credentials are added after the client was first initialized.
        """
        # Reload environment variables
        load_dotenv(override=True)

        # Read credentials from environment
        self._url = os.getenv('SUPABASE_URL', '').strip()
        self._key = os.getenv('SUPABASE_KEY', '').strip()
        self._service_key = os.getenv('SUPABASE_SERVICE_KEY', '').strip() or self._key

        # Validate credentials
        if not self._url or not self._key:
            missing = []
            if not self._url:
                missing.append('SUPABASE_URL')
            if not self._key:
                missing.append('SUPABASE_KEY')
            
            logger.warning(
                f"Supabase credentials still missing: {', '.join(missing)}. "
                "Supabase integration remains disabled."
            )
            self._available = False
            return False
        
        # Mark as available if credentials are present
        self._available = True
        logger.info("Supabase credentials reloaded successfully")
        return True
    
    async def insert_lead(self, lead_data: dict, max_retries: int = 3) -> bool:
        """
        Insert a single lead into Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            lead_data: Dictionary containing lead fields (nome, telefone, website, 
                      endereco, cidade, url, conjunto_de_locais, task_id)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if insert succeeded, False if all retries failed
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping insert")
            return False
        
        # Validate required fields
        if not lead_data.get('nome'):
            logger.error(
                "Cannot insert lead: 'nome' field is required",
                extra={'lead_data': lead_data}
            )
            return False
        
        # Prepare the insert payload
        payload = {
            'nome': lead_data.get('nome'),
            'telefone': lead_data.get('telefone'),
            'website': lead_data.get('website'),
            'email': lead_data.get('email') or '',
            'endereco': lead_data.get('endereco'),
            'cidade': lead_data.get('cidade'),
            'url': lead_data.get('url'),
            'conjunto_de_locais': lead_data.get('conjunto_de_locais'),
            'task_id': lead_data.get('task_id'),
            'user_id': lead_data.get('user_id'),
        }
        # user_id is NOT NULL — skip insert if missing
        if not payload['user_id']:
            logger.error("Cannot insert lead: 'user_id' is required (check JWT auth)")
            return False
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/gmap_leads",
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully inserted lead to Supabase: {lead_data.get('nome')}",
                            extra={
                                'lead_nome': lead_data.get('nome'),
                                'task_id': lead_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting lead to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'lead_nome': lead_data.get('nome'),
                                'task_id': lead_data.get('task_id')
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'lead_nome': lead_data.get('nome'),
                                    'task_id': lead_data.get('task_id')
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'lead_nome': lead_data.get('nome'),
                                    'task_id': lead_data.get('task_id'),
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting lead to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'lead_nome': lead_data.get('nome'),
                                'task_id': lead_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting lead to Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'lead_nome': lead_data.get('nome'),
                            'task_id': lead_data.get('task_id')
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting lead to Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'lead_nome': lead_data.get('nome'),
                            'task_id': lead_data.get('task_id'),
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting lead to Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'lead_nome': lead_data.get('nome'),
                        'task_id': lead_data.get('task_id'),
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def insert_leads_batch(self, leads: list[dict], max_retries: int = 3) -> tuple[int, int]:
        """
        Insert multiple leads into Supabase in a single batch operation.
        
        This method attempts to insert all leads in one batch request for optimal
        performance. If the batch insert fails, it falls back to inserting leads
        individually to identify which specific leads caused errors.
        
        Args:
            leads: List of lead dictionaries, each containing lead fields
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            tuple[int, int]: A tuple of (successful_inserts, failed_inserts)
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping batch insert")
            return (0, len(leads))
        
        if not leads:
            logger.debug("No leads provided for batch insert")
            return (0, 0)
        
        # Validate and prepare payloads
        valid_leads = []
        invalid_count = 0
        
        for lead_data in leads:
            if not lead_data.get('nome'):
                logger.error(
                    "Cannot insert lead in batch: 'nome' field is required",
                    extra={'lead_data': lead_data}
                )
                invalid_count += 1
                continue
            
            payload = {
                'nome': lead_data.get('nome'),
                'telefone': lead_data.get('telefone'),
                'website': lead_data.get('website'),
                'endereco': lead_data.get('endereco'),
                'cidade': lead_data.get('cidade'),
                'url': lead_data.get('url'),
                'conjunto_de_locais': lead_data.get('conjunto_de_locais'),
                'task_id': lead_data.get('task_id')
            }
            valid_leads.append(payload)
        
        if not valid_leads:
            logger.warning("No valid leads to insert in batch")
            return (0, invalid_count)
        
        # Try batch insert first
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/gmap_leads",
                        json=valid_leads,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.info(
                            f"Successfully inserted {len(valid_leads)} leads to Supabase in batch",
                            extra={
                                'batch_size': len(valid_leads),
                                'attempt': attempt + 1
                            }
                        )
                        return (len(valid_leads), invalid_count)
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error in batch insert: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_leads)
                            }
                        )
                        self.disable()
                        return (0, len(leads))
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429) on batch insert, retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'batch_size': len(valid_leads)
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts on batch insert",
                                extra={
                                    'batch_size': len(valid_leads),
                                    'max_retries': max_retries
                                }
                            )
                            # Fall back to individual inserts
                            break
                    
                    # Other HTTP errors - fall back to individual inserts
                    else:
                        logger.warning(
                            f"Batch insert failed with status {response.status_code}, falling back to individual inserts",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_leads),
                                'attempt': attempt + 1
                            }
                        )
                        # Fall back to individual inserts
                        break
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error in batch insert, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'batch_size': len(valid_leads)
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.warning(
                        f"Network error in batch insert after {max_retries} attempts, falling back to individual inserts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'batch_size': len(valid_leads),
                            'max_retries': max_retries
                        }
                    )
                    # Fall back to individual inserts
                    break
            
            except Exception as e:
                # Unexpected errors - fall back to individual inserts
                logger.warning(
                    f"Unexpected error in batch insert, falling back to individual inserts: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'batch_size': len(valid_leads),
                        'attempt': attempt + 1
                    }
                )
                # Fall back to individual inserts
                break
        
        # Fall back to individual inserts to identify problematic leads
        logger.info(
            f"Falling back to individual inserts for {len(leads)} leads",
            extra={'batch_size': len(leads)}
        )
        
        success_count = 0
        failure_count = invalid_count
        
        for lead_data in leads:
            # Skip already identified invalid leads
            if not lead_data.get('nome'):
                continue
            
            # Try to insert individual lead
            result = await self.insert_lead(lead_data, max_retries=max_retries)
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(
            f"Batch insert completed: {success_count} successes, {failure_count} failures",
            extra={
                'success_count': success_count,
                'failure_count': failure_count,
                'total': len(leads)
            }
        )
        
        return (success_count, failure_count)
    
    async def check_duplicate(self, nome: str, cidade: str, url: str) -> bool:
        """
        Check if a lead with the same (nome, cidade, url) already exists in Supabase.
        
        This method is used by the migration script to avoid inserting duplicate leads.
        A lead is considered a duplicate if all three fields match exactly.
        
        Args:
            nome: Business name to check
            cidade: City to check
            url: Google Maps URL to check
        
        Returns:
            bool: True if a matching lead exists, False otherwise
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot check duplicates")
            return False
        
        # Validate required fields
        if not nome or not cidade or not url:
            logger.error(
                "Cannot check duplicate: all fields (nome, cidade, url) are required",
                extra={'nome': nome, 'cidade': cidade, 'url': url}
            )
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters for exact match on all three fields
                # Using PostgREST query syntax: ?field=eq.value
                params = {
                    'nome': f'eq.{nome}',
                    'cidade': f'eq.{cidade}',
                    'url': f'eq.{url}',
                    'select': 'id',  # Only select id to minimize data transfer
                    'limit': '1'     # We only need to know if at least one exists
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case - check if any results returned
                if response.status_code == 200:
                    results = response.json()
                    exists = len(results) > 0
                    
                    if exists:
                        logger.debug(
                            f"Duplicate lead found: {nome} in {cidade}",
                            extra={'nome': nome, 'cidade': cidade, 'url': url}
                        )
                    
                    return exists
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error checking duplicate: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'nome': nome,
                            'cidade': cidade
                        }
                    )
                    self.disable()
                    return False
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error checking duplicate: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'nome': nome,
                            'cidade': cidade
                        }
                    )
                    return False
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error checking duplicate: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'nome': nome,
                    'cidade': cidade
                }
            )
            return False
        
        except Exception as e:
            logger.error(
                f"Unexpected error checking duplicate: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'nome': nome,
                    'cidade': cidade
                }
            )
            return False
    
    async def get_leads_by_task(self, task_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Query leads by task_id with pagination support.
        
        This method retrieves all leads associated with a specific extraction task,
        ordered by creation date (newest first). Supports pagination for large result sets.
        
        Args:
            task_id: The task ID to filter leads by
            limit: Maximum number of leads to return (default: 100)
            offset: Number of leads to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of lead dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query leads")
            return []
        
        # Validate parameters
        if not task_id:
            logger.error("Cannot query leads: task_id is required")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'task_id': f'eq.{task_id}',
                    'select': '*',  # Select all fields
                    'order': 'created_at.desc',  # Newest first
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} leads for task {task_id}",
                        extra={
                            'task_id': task_id,
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying leads by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying leads by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying leads by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying leads by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
    
    async def get_leads_by_location_set(self, location_set: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Query leads by conjunto_de_locais (location set name) with pagination support.
        
        This method retrieves all leads associated with a specific location set
        (e.g., "Capitais do Brasil"), ordered by creation date (newest first).
        Supports pagination for large result sets.
        
        Args:
            location_set: The location set name to filter leads by
            limit: Maximum number of leads to return (default: 100)
            offset: Number of leads to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of lead dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query leads")
            return []
        
        # Validate parameters
        if not location_set:
            logger.error("Cannot query leads: location_set is required")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'conjunto_de_locais': f'eq.{location_set}',
                    'select': '*',  # Select all fields
                    'order': 'created_at.desc',  # Newest first
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} leads for location set '{location_set}'",
                        extra={
                            'location_set': location_set,
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying leads by location set: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'location_set': location_set
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying leads by location set: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'location_set': location_set
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying leads by location set: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'location_set': location_set
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying leads by location set: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'location_set': location_set
                }
            )
            return []
    
    # ========== Facebook Ads Leads Methods ==========
    
    async def insert_facebook_lead(self, lead_data: dict, max_retries: int = 3) -> bool:
        """
        Insert a single Facebook Ads lead into Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            lead_data: Dictionary containing lead fields (name, page_url, ad_url, 
                      page_id, emails, phones, instagram, stage, task_id)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if insert succeeded, False if all retries failed
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping insert")
            return False
        
        # Validate required fields
        if not lead_data.get('name'):
            logger.error(
                "Cannot insert Facebook lead: 'name' field is required",
                extra={'lead_data': lead_data}
            )
            return False
        
        # Prepare the insert payload
        payload = {
            'name': lead_data.get('name'),
            'page_url': lead_data.get('page_url'),
            'ad_url': lead_data.get('ad_url'),
            'page_id': lead_data.get('page_id'),
            'emails': lead_data.get('emails'),
            'phones': lead_data.get('phones'),
            'instagram': lead_data.get('instagram'),
            'stage': lead_data.get('stage', 'feed'),
            'task_id': lead_data.get('task_id')
        }
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/facebook_ads_leads",
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully inserted Facebook lead to Supabase: {lead_data.get('name')}",
                            extra={
                                'lead_name': lead_data.get('name'),
                                'task_id': lead_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting Facebook lead to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'lead_name': lead_data.get('name'),
                                'task_id': lead_data.get('task_id')
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'lead_name': lead_data.get('name'),
                                    'task_id': lead_data.get('task_id')
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'lead_name': lead_data.get('name'),
                                    'task_id': lead_data.get('task_id'),
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting Facebook lead to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'lead_name': lead_data.get('name'),
                                'task_id': lead_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting Facebook lead to Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'lead_name': lead_data.get('name'),
                            'task_id': lead_data.get('task_id')
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting Facebook lead to Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'lead_name': lead_data.get('name'),
                            'task_id': lead_data.get('task_id'),
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting Facebook lead to Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'lead_name': lead_data.get('name'),
                        'task_id': lead_data.get('task_id'),
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def insert_facebook_leads_batch(self, leads: list[dict], max_retries: int = 3) -> tuple[int, int]:
        """
        Insert multiple Facebook Ads leads into Supabase in a single batch operation.
        
        This method attempts to insert all leads in one batch request for optimal
        performance. If the batch insert fails, it falls back to inserting leads
        individually to identify which specific leads caused errors.
        
        Args:
            leads: List of lead dictionaries, each containing lead fields
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            tuple[int, int]: A tuple of (successful_inserts, failed_inserts)
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping batch insert")
            return (0, len(leads))
        
        if not leads:
            logger.debug("No Facebook leads provided for batch insert")
            return (0, 0)
        
        # Validate and prepare payloads
        valid_leads = []
        invalid_count = 0
        
        for lead_data in leads:
            if not lead_data.get('name'):
                logger.error(
                    "Cannot insert Facebook lead in batch: 'name' field is required",
                    extra={'lead_data': lead_data}
                )
                invalid_count += 1
                continue
            
            payload = {
                'name': lead_data.get('name'),
                'page_url': lead_data.get('page_url'),
                'ad_url': lead_data.get('ad_url'),
                'page_id': lead_data.get('page_id'),
                'emails': lead_data.get('emails'),
                'phones': lead_data.get('phones'),
                'instagram': lead_data.get('instagram'),
                'stage': lead_data.get('stage', 'feed'),
                'task_id': lead_data.get('task_id')
            }
            valid_leads.append(payload)
        
        if not valid_leads:
            logger.warning("No valid Facebook leads to insert in batch")
            return (0, invalid_count)
        
        # Try batch insert first
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/facebook_ads_leads",
                        json=valid_leads,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.info(
                            f"Successfully inserted {len(valid_leads)} Facebook leads to Supabase in batch",
                            extra={
                                'batch_size': len(valid_leads),
                                'attempt': attempt + 1
                            }
                        )
                        return (len(valid_leads), invalid_count)
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error in Facebook batch insert: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_leads)
                            }
                        )
                        self.disable()
                        return (0, len(leads))
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429) on Facebook batch insert, retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'batch_size': len(valid_leads)
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts on Facebook batch insert",
                                extra={
                                    'batch_size': len(valid_leads),
                                    'max_retries': max_retries
                                }
                            )
                            # Fall back to individual inserts
                            break
                    
                    # Other HTTP errors - fall back to individual inserts
                    else:
                        logger.warning(
                            f"Facebook batch insert failed with status {response.status_code}, falling back to individual inserts",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_leads),
                                'attempt': attempt + 1
                            }
                        )
                        # Fall back to individual inserts
                        break
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error in Facebook batch insert, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'batch_size': len(valid_leads)
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.warning(
                        f"Network error in Facebook batch insert after {max_retries} attempts, falling back to individual inserts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'batch_size': len(valid_leads),
                            'max_retries': max_retries
                        }
                    )
                    # Fall back to individual inserts
                    break
            
            except Exception as e:
                # Unexpected errors - fall back to individual inserts
                logger.warning(
                    f"Unexpected error in Facebook batch insert, falling back to individual inserts: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'batch_size': len(valid_leads),
                        'attempt': attempt + 1
                    }
                )
                # Fall back to individual inserts
                break
        
        # Fall back to individual inserts to identify problematic leads
        logger.info(
            f"Falling back to individual inserts for {len(leads)} Facebook leads",
            extra={'batch_size': len(leads)}
        )
        
        success_count = 0
        failure_count = invalid_count
        
        for lead_data in leads:
            # Skip already identified invalid leads
            if not lead_data.get('name'):
                continue
            
            # Try to insert individual lead
            result = await self.insert_facebook_lead(lead_data, max_retries=max_retries)
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(
            f"Facebook batch insert completed: {success_count} successes, {failure_count} failures",
            extra={
                'success_count': success_count,
                'failure_count': failure_count,
                'total': len(leads)
            }
        )
        
        return (success_count, failure_count)
    
    async def get_facebook_leads_by_task(self, task_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Query Facebook Ads leads by task_id with pagination support.
        
        This method retrieves all Facebook leads associated with a specific extraction task,
        ordered by creation date (newest first). Supports pagination for large result sets.
        
        Args:
            task_id: The task ID to filter leads by
            limit: Maximum number of leads to return (default: 100)
            offset: Number of leads to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of lead dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query Facebook leads")
            return []
        
        # Validate parameters
        if not task_id:
            logger.error("Cannot query Facebook leads: task_id is required")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'task_id': f'eq.{task_id}',
                    'select': '*',  # Select all fields
                    'order': 'created_at.desc',  # Newest first
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/facebook_ads_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} Facebook leads for task {task_id}",
                        extra={
                            'task_id': task_id,
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying Facebook leads by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying Facebook leads by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying Facebook leads by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying Facebook leads by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
    
    async def update_facebook_lead_contacts(self, id: int, emails: str = None, phones: str = None, instagram: str = None) -> bool:
        """
        Update contact information for a Facebook Ads lead.
        
        This method updates the emails, phones, and/or instagram fields for an existing
        Facebook lead. Only provided fields will be updated (partial update).
        
        Args:
            id: The lead ID to update
            emails: New emails value (optional)
            phones: New phones value (optional)
            instagram: New instagram value (optional)
        
        Returns:
            bool: True if update succeeded, False otherwise
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping update")
            return False
        
        # Validate parameters
        if not id:
            logger.error("Cannot update Facebook lead: id is required")
            return False
        
        # Build update payload with only provided fields
        updates = {}
        if emails is not None:
            updates['emails'] = emails
        if phones is not None:
            updates['phones'] = phones
        if instagram is not None:
            updates['instagram'] = instagram
        
        if not updates:
            logger.warning(
                f"No fields to update for Facebook lead {id}",
                extra={'lead_id': id}
            )
            return True  # Nothing to update is not an error
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self._url}/rest/v1/facebook_ads_leads",
                    params={'id': f'eq.{id}'},
                    json=updates,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    }
                )
                
                # Success case
                if response.status_code in (200, 204):
                    logger.debug(
                        f"Successfully updated Facebook lead {id} contacts",
                        extra={
                            'lead_id': id,
                            'updated_fields': list(updates.keys())
                        }
                    )
                    return True
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error updating Facebook lead: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'lead_id': id
                        }
                    )
                    self.disable()
                    return False
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error updating Facebook lead: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'lead_id': id
                        }
                    )
                    return False
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error updating Facebook lead: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'lead_id': id
                }
            )
            return False
        
        except Exception as e:
            logger.error(
                f"Unexpected error updating Facebook lead: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'lead_id': id
                }
            )
            return False
    
    # ========== Email Results Methods ==========
    
    async def insert_email_result(self, result_data: dict, max_retries: int = 3) -> bool:
        """
        Insert a single email result into Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            result_data: Dictionary containing result fields (domain, email, source, task_id)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if insert succeeded, False if all retries failed
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping insert")
            return False
        
        # Validate required fields
        if not result_data.get('domain'):
            logger.error(
                "Cannot insert email result: 'domain' field is required",
                extra={'result_data': result_data}
            )
            return False
        
        # Prepare the insert payload
        payload = {
            'domain': result_data.get('domain'),
            'email': result_data.get('email'),
            'source': result_data.get('source'),
            'task_id': result_data.get('task_id')
        }
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/email_results",
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully inserted email result to Supabase: {result_data.get('domain')}",
                            extra={
                                'domain': result_data.get('domain'),
                                'task_id': result_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting email result to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'domain': result_data.get('domain'),
                                'task_id': result_data.get('task_id')
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'domain': result_data.get('domain'),
                                    'task_id': result_data.get('task_id')
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'domain': result_data.get('domain'),
                                    'task_id': result_data.get('task_id'),
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting email result to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'domain': result_data.get('domain'),
                                'task_id': result_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting email result to Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'domain': result_data.get('domain'),
                            'task_id': result_data.get('task_id')
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting email result to Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'domain': result_data.get('domain'),
                            'task_id': result_data.get('task_id'),
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting email result to Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'domain': result_data.get('domain'),
                        'task_id': result_data.get('task_id'),
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def insert_email_results_batch(self, results: list[dict], max_retries: int = 3) -> tuple[int, int]:
        """
        Insert multiple email results into Supabase in a single batch operation.
        
        This method attempts to insert all results in one batch request for optimal
        performance. If the batch insert fails, it falls back to inserting results
        individually to identify which specific results caused errors.
        
        Args:
            results: List of result dictionaries, each containing result fields
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            tuple[int, int]: A tuple of (successful_inserts, failed_inserts)
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping batch insert")
            return (0, len(results))
        
        if not results:
            logger.debug("No email results provided for batch insert")
            return (0, 0)
        
        # Validate and prepare payloads
        valid_results = []
        invalid_count = 0
        
        for result_data in results:
            if not result_data.get('domain'):
                logger.error(
                    "Cannot insert email result in batch: 'domain' field is required",
                    extra={'result_data': result_data}
                )
                invalid_count += 1
                continue
            
            payload = {
                'domain': result_data.get('domain'),
                'email': result_data.get('email'),
                'source': result_data.get('source'),
                'task_id': result_data.get('task_id')
            }
            valid_results.append(payload)
        
        if not valid_results:
            logger.warning("No valid email results to insert in batch")
            return (0, invalid_count)
        
        # Try batch insert first
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/email_results",
                        json=valid_results,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.info(
                            f"Successfully inserted {len(valid_results)} email results to Supabase in batch",
                            extra={
                                'batch_size': len(valid_results),
                                'attempt': attempt + 1
                            }
                        )
                        return (len(valid_results), invalid_count)
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error in email results batch insert: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_results)
                            }
                        )
                        self.disable()
                        return (0, len(results))
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429) on email results batch insert, retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'batch_size': len(valid_results)
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts on email results batch insert",
                                extra={
                                    'batch_size': len(valid_results),
                                    'max_retries': max_retries
                                }
                            )
                            # Fall back to individual inserts
                            break
                    
                    # Other HTTP errors - fall back to individual inserts
                    else:
                        logger.warning(
                            f"Email results batch insert failed with status {response.status_code}, falling back to individual inserts",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_results),
                                'attempt': attempt + 1
                            }
                        )
                        # Fall back to individual inserts
                        break
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error in email results batch insert, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'batch_size': len(valid_results)
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.warning(
                        f"Network error in email results batch insert after {max_retries} attempts, falling back to individual inserts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'batch_size': len(valid_results),
                            'max_retries': max_retries
                        }
                    )
                    # Fall back to individual inserts
                    break
            
            except Exception as e:
                # Unexpected errors - fall back to individual inserts
                logger.warning(
                    f"Unexpected error in email results batch insert, falling back to individual inserts: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'batch_size': len(valid_results),
                        'attempt': attempt + 1
                    }
                )
                # Fall back to individual inserts
                break
        
        # Fall back to individual inserts to identify problematic results
        logger.info(
            f"Falling back to individual inserts for {len(results)} email results",
            extra={'batch_size': len(results)}
        )
        
        success_count = 0
        failure_count = invalid_count
        
        for result_data in results:
            # Skip already identified invalid results
            if not result_data.get('domain'):
                continue
            
            # Try to insert individual result
            result = await self.insert_email_result(result_data, max_retries=max_retries)
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(
            f"Email results batch insert completed: {success_count} successes, {failure_count} failures",
            extra={
                'success_count': success_count,
                'failure_count': failure_count,
                'total': len(results)
            }
        )
        
        return (success_count, failure_count)
    
    async def get_email_results_by_task(self, task_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Query email results by task_id with pagination support.
        
        This method retrieves all email results associated with a specific extraction task,
        ordered by creation date (newest first). Supports pagination for large result sets.
        
        Args:
            task_id: The task ID to filter results by
            limit: Maximum number of results to return (default: 100)
            offset: Number of results to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of result dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query email results")
            return []
        
        # Validate parameters
        if not task_id:
            logger.error("Cannot query email results: task_id is required")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'task_id': f'eq.{task_id}',
                    'select': '*',  # Select all fields
                    'order': 'created_at.desc',  # Newest first
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/email_results",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} email results for task {task_id}",
                        extra={
                            'task_id': task_id,
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying email results by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying email results by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying email results by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying email results by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
    
    # ========== Tasks Methods ==========
    
    async def insert_task(self, task_data: dict, max_retries: int = 3) -> bool:
        """
        Insert a task into Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            task_data: Dictionary containing task fields (id, module, status, 
                      config, stats, progress)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if insert succeeded, False if all retries failed
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping insert")
            return False
        
        # Validate required fields
        if not task_data.get('id'):
            logger.error(
                "Cannot insert task: 'id' field is required",
                extra={'task_data': task_data}
            )
            return False
        
        if not task_data.get('module'):
            logger.error(
                "Cannot insert task: 'module' field is required",
                extra={'task_data': task_data}
            )
            return False
        
        # Prepare the insert payload
        payload = {
            'id': task_data.get('id'),
            'module': task_data.get('module'),
            'status': task_data.get('status', 'running'),
            'config': task_data.get('config', {}),
            'stats': task_data.get('stats', {}),
            'progress': task_data.get('progress', 0.0)
        }
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/tasks",
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully inserted task to Supabase: {task_data.get('id')}",
                            extra={
                                'task_id': task_data.get('id'),
                                'module': task_data.get('module'),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting task to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'task_id': task_data.get('id')
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'task_id': task_data.get('id')
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'task_id': task_data.get('id'),
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting task to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'task_id': task_data.get('id'),
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting task to Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'task_id': task_data.get('id')
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting task to Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'task_id': task_data.get('id'),
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting task to Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'task_id': task_data.get('id'),
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def update_task(self, task_id: str, updates: dict, max_retries: int = 3) -> bool:
        """
        Update a task in Supabase with retry logic.
        
        This method updates specific fields of an existing task. The updated_at
        timestamp is automatically updated by the database.
        
        Args:
            task_id: The task ID to update
            updates: Dictionary containing fields to update (status, config, stats, progress)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if update succeeded, False otherwise
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping update")
            return False
        
        # Validate parameters
        if not task_id:
            logger.error("Cannot update task: task_id is required")
            return False
        
        if not updates:
            logger.warning(
                f"No fields to update for task {task_id}",
                extra={'task_id': task_id}
            )
            return True  # Nothing to update is not an error
        
        # Build update payload with only allowed fields
        allowed_fields = {'status', 'config', 'stats', 'progress'}
        payload = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not payload:
            logger.warning(
                f"No valid fields to update for task {task_id}",
                extra={'task_id': task_id, 'updates': updates}
            )
            return True
        
        # Add updated_at timestamp
        from datetime import datetime, timezone
        payload['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.patch(
                        f"{self._url}/rest/v1/tasks",
                        params={'id': f'eq.{task_id}'},
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 204):
                        logger.debug(
                            f"Successfully updated task in Supabase: {task_id}",
                            extra={
                                'task_id': task_id,
                                'updates': list(payload.keys()),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error updating task in Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'task_id': task_id
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'task_id': task_id
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'task_id': task_id,
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error updating task in Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'task_id': task_id,
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error updating task in Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'task_id': task_id
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error updating task in Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'task_id': task_id,
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error updating task in Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'task_id': task_id,
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def get_task(self, task_id: str) -> Optional[dict]:
        """
        Get a single task by ID from Supabase.
        
        Args:
            task_id: The task ID to retrieve
        
        Returns:
            Optional[dict]: Task dictionary with all fields, or None if not found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query task")
            return None
        
        # Validate parameters
        if not task_id:
            logger.error("Cannot query task: task_id is required")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'id': f'eq.{task_id}',
                    'select': '*',
                    'limit': '1'
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/tasks",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        logger.debug(
                            f"Retrieved task from Supabase: {task_id}",
                            extra={'task_id': task_id}
                        )
                        return results[0]
                    else:
                        logger.debug(
                            f"Task not found in Supabase: {task_id}",
                            extra={'task_id': task_id}
                        )
                        return None
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    self.disable()
                    return None
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    return None
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return None
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return None
    
    async def get_all_tasks(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Get all tasks from Supabase with pagination support.
        
        Tasks are ordered by creation date (newest first).
        
        Args:
            limit: Maximum number of tasks to return (default: 100)
            offset: Number of tasks to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of task dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query tasks")
            return []
        
        # Validate parameters
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'select': '*',
                    'order': 'created_at.desc',
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/tasks",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} tasks from Supabase",
                        extra={
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying all tasks: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying all tasks: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying all tasks: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying all tasks: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            return []
    
    async def get_tasks_by_module(self, module: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Query tasks by module with pagination support.
        
        This method retrieves all tasks for a specific module (e.g., 'gmap', 'facebook'),
        ordered by creation date (newest first). Supports pagination for large result sets.
        
        Args:
            module: The module name to filter tasks by
            limit: Maximum number of tasks to return (default: 100)
            offset: Number of tasks to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of task dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query tasks")
            return []
        
        # Validate parameters
        if not module:
            logger.error("Cannot query tasks: module is required")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'module': f'eq.{module}',
                    'select': '*',
                    'order': 'created_at.desc',
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/tasks",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} tasks for module '{module}' from Supabase",
                        extra={
                            'module': module,
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying tasks by module: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'module': module
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying tasks by module: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'module': module
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying tasks by module: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'module': module
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying tasks by module: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'module': module
                }
            )
            return []
    
    # ========== Email Dispatches Methods ==========
    
    async def insert_email_dispatch(self, dispatch_data: dict, max_retries: int = 3) -> bool:
        """
        Insert a single email dispatch into Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            dispatch_data: Dictionary containing dispatch fields (recipient, subject, 
                          status, error_detail, task_id, sent_at)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if insert succeeded, False if all retries failed
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping insert")
            return False
        
        # Validate required fields
        if not dispatch_data.get('recipient'):
            logger.error(
                "Cannot insert email dispatch: 'recipient' field is required",
                extra={'dispatch_data': dispatch_data}
            )
            return False
        
        # Prepare the insert payload
        payload = {
            'recipient': dispatch_data.get('recipient'),
            'subject': dispatch_data.get('subject'),
            'status': dispatch_data.get('status', 'pending'),
            'error_detail': dispatch_data.get('error_detail'),
            'task_id': dispatch_data.get('task_id'),
            'sent_at': dispatch_data.get('sent_at')
        }
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/email_dispatches",
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully inserted email dispatch to Supabase: {dispatch_data.get('recipient')}",
                            extra={
                                'recipient': dispatch_data.get('recipient'),
                                'task_id': dispatch_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting email dispatch to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'recipient': dispatch_data.get('recipient'),
                                'task_id': dispatch_data.get('task_id')
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'recipient': dispatch_data.get('recipient'),
                                    'task_id': dispatch_data.get('task_id')
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'recipient': dispatch_data.get('recipient'),
                                    'task_id': dispatch_data.get('task_id'),
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting email dispatch to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'recipient': dispatch_data.get('recipient'),
                                'task_id': dispatch_data.get('task_id'),
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting email dispatch to Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'recipient': dispatch_data.get('recipient'),
                            'task_id': dispatch_data.get('task_id')
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting email dispatch to Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'recipient': dispatch_data.get('recipient'),
                            'task_id': dispatch_data.get('task_id'),
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting email dispatch to Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'recipient': dispatch_data.get('recipient'),
                        'task_id': dispatch_data.get('task_id'),
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def insert_email_dispatches_batch(self, dispatches: list[dict], max_retries: int = 3) -> tuple[int, int]:
        """
        Insert multiple email dispatches into Supabase in a single batch operation.
        
        This method attempts to insert all dispatches in one batch request for optimal
        performance. If the batch insert fails, it falls back to inserting dispatches
        individually to identify which specific dispatches caused errors.
        
        Args:
            dispatches: List of dispatch dictionaries, each containing dispatch fields
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            tuple[int, int]: A tuple of (successful_inserts, failed_inserts)
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping batch insert")
            return (0, len(dispatches))
        
        if not dispatches:
            logger.debug("No email dispatches provided for batch insert")
            return (0, 0)
        
        # Validate and prepare payloads
        valid_dispatches = []
        invalid_count = 0
        
        for dispatch_data in dispatches:
            if not dispatch_data.get('recipient'):
                logger.error(
                    "Cannot insert email dispatch in batch: 'recipient' field is required",
                    extra={'dispatch_data': dispatch_data}
                )
                invalid_count += 1
                continue
            
            payload = {
                'recipient': dispatch_data.get('recipient'),
                'subject': dispatch_data.get('subject'),
                'status': dispatch_data.get('status', 'pending'),
                'error_detail': dispatch_data.get('error_detail'),
                'task_id': dispatch_data.get('task_id'),
                'sent_at': dispatch_data.get('sent_at')
            }
            valid_dispatches.append(payload)
        
        if not valid_dispatches:
            logger.warning("No valid email dispatches to insert in batch")
            return (0, invalid_count)
        
        # Try batch insert first
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/email_dispatches",
                        json=valid_dispatches,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.info(
                            f"Successfully inserted {len(valid_dispatches)} email dispatches to Supabase in batch",
                            extra={
                                'batch_size': len(valid_dispatches),
                                'attempt': attempt + 1
                            }
                        )
                        return (len(valid_dispatches), invalid_count)
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error in email dispatches batch insert: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_dispatches)
                            }
                        )
                        self.disable()
                        return (0, len(dispatches))
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429) on email dispatches batch insert, retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'batch_size': len(valid_dispatches)
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts on email dispatches batch insert",
                                extra={
                                    'batch_size': len(valid_dispatches),
                                    'max_retries': max_retries
                                }
                            )
                            # Fall back to individual inserts
                            break
                    
                    # Other HTTP errors - fall back to individual inserts
                    else:
                        logger.warning(
                            f"Email dispatches batch insert failed with status {response.status_code}, falling back to individual inserts",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'batch_size': len(valid_dispatches),
                                'attempt': attempt + 1
                            }
                        )
                        # Fall back to individual inserts
                        break
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error in email dispatches batch insert, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'batch_size': len(valid_dispatches)
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.warning(
                        f"Network error in email dispatches batch insert after {max_retries} attempts, falling back to individual inserts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'batch_size': len(valid_dispatches),
                            'max_retries': max_retries
                        }
                    )
                    # Fall back to individual inserts
                    break
            
            except Exception as e:
                # Unexpected errors - fall back to individual inserts
                logger.warning(
                    f"Unexpected error in email dispatches batch insert, falling back to individual inserts: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'batch_size': len(valid_dispatches),
                        'attempt': attempt + 1
                    }
                )
                # Fall back to individual inserts
                break
        
        # Fall back to individual inserts to identify problematic dispatches
        logger.info(
            f"Falling back to individual inserts for {len(dispatches)} email dispatches",
            extra={'batch_size': len(dispatches)}
        )
        
        success_count = 0
        failure_count = invalid_count
        
        for dispatch_data in dispatches:
            # Skip already identified invalid dispatches
            if not dispatch_data.get('recipient'):
                continue
            
            # Try to insert individual dispatch
            result = await self.insert_email_dispatch(dispatch_data, max_retries=max_retries)
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(
            f"Email dispatches batch insert completed: {success_count} successes, {failure_count} failures",
            extra={
                'success_count': success_count,
                'failure_count': failure_count,
                'total': len(dispatches)
            }
        )
        
        return (success_count, failure_count)
    
    async def get_email_dispatches_by_task(self, task_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Query email dispatches by task_id with pagination support.
        
        This method retrieves all email dispatches associated with a specific task,
        ordered by creation date (newest first). Supports pagination for large result sets.
        
        Args:
            task_id: The task ID to filter dispatches by
            limit: Maximum number of dispatches to return (default: 100)
            offset: Number of dispatches to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of dispatch dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query email dispatches")
            return []
        
        # Validate parameters
        if not task_id:
            logger.error("Cannot query email dispatches: task_id is required")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'task_id': f'eq.{task_id}',
                    'select': '*',  # Select all fields
                    'order': 'created_at.desc',  # Newest first
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/email_dispatches",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} email dispatches for task {task_id}",
                        extra={
                            'task_id': task_id,
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying email dispatches by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying email dispatches by task: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'task_id': task_id
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying email dispatches by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying email dispatches by task: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'task_id': task_id
                }
            )
            return []
    
    async def update_email_dispatch_sent(self, id: int, sent_at: str) -> bool:
        """
        Update the sent_at timestamp for an email dispatch.
        
        This method updates the sent_at field when an email is successfully sent.
        
        Args:
            id: The dispatch ID to update
            sent_at: ISO 8601 timestamp string (e.g., "2024-01-15T10:30:00Z")
        
        Returns:
            bool: True if update succeeded, False otherwise
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping update")
            return False
        
        # Validate parameters
        if not id:
            logger.error("Cannot update email dispatch: id is required")
            return False
        
        if not sent_at:
            logger.error("Cannot update email dispatch: sent_at is required")
            return False
        
        # Build update payload
        updates = {
            'sent_at': sent_at,
            'status': 'sent'  # Also update status to 'sent'
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self._url}/rest/v1/email_dispatches",
                    params={'id': f'eq.{id}'},
                    json=updates,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    }
                )
                
                # Success case
                if response.status_code in (200, 204):
                    logger.debug(
                        f"Successfully updated email dispatch {id} sent_at",
                        extra={
                            'dispatch_id': id,
                            'sent_at': sent_at
                        }
                    )
                    return True
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error updating email dispatch: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'dispatch_id': id
                        }
                    )
                    self.disable()
                    return False
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error updating email dispatch: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'dispatch_id': id
                        }
                    )
                    return False
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error updating email dispatch: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'dispatch_id': id
                }
            )
            return False
        
        except Exception as e:
            logger.error(
                f"Unexpected error updating email dispatch: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'dispatch_id': id
                }
            )
            return False
    
    # ========== DM Templates Methods ==========
    
    async def insert_dm_template(self, template_data: dict, max_retries: int = 3) -> bool:
        """
        Insert a DM template into Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            template_data: Dictionary containing template fields (name, messages, audios,
                          send_mode, delay_dm_min, delay_dm_max, delay_lead_min, delay_lead_max)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if insert succeeded, False if all retries failed
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping insert")
            return False
        
        # Validate required fields
        if not template_data.get('name'):
            logger.error(
                "Cannot insert DM template: 'name' field is required",
                extra={'template_data': template_data}
            )
            return False
        
        # Prepare the insert payload
        payload = {
            'name': template_data.get('name'),
            'messages': template_data.get('messages', []),
            'audios': template_data.get('audios', []),
            'send_mode': template_data.get('send_mode', 'sequential'),
            'delay_dm_min': template_data.get('delay_dm_min', 10),
            'delay_dm_max': template_data.get('delay_dm_max', 20),
            'delay_lead_min': template_data.get('delay_lead_min', 30),
            'delay_lead_max': template_data.get('delay_lead_max', 60)
        }
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/dm_templates",
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully inserted DM template to Supabase: {template_data.get('name')}",
                            extra={
                                'template_name': template_data.get('name'),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting DM template to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'template_name': template_data.get('name')
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'template_name': template_data.get('name')
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'template_name': template_data.get('name'),
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting DM template to Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'template_name': template_data.get('name'),
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting DM template to Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'template_name': template_data.get('name')
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting DM template to Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'template_name': template_data.get('name'),
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting DM template to Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'template_name': template_data.get('name'),
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def update_dm_template(self, id: int, updates: dict, max_retries: int = 3) -> bool:
        """
        Update a DM template in Supabase with retry logic.
        
        This method updates specific fields of an existing DM template.
        
        Args:
            id: The template ID to update
            updates: Dictionary containing fields to update (name, messages, audios,
                    send_mode, delay_dm_min, delay_dm_max, delay_lead_min, delay_lead_max)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if update succeeded, False otherwise
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping update")
            return False
        
        # Validate parameters
        if not id:
            logger.error("Cannot update DM template: id is required")
            return False
        
        if not updates:
            logger.warning(
                f"No fields to update for DM template {id}",
                extra={'template_id': id}
            )
            return True  # Nothing to update is not an error
        
        # Build update payload with only allowed fields
        allowed_fields = {
            'name', 'messages', 'audios', 'send_mode',
            'delay_dm_min', 'delay_dm_max', 'delay_lead_min', 'delay_lead_max'
        }
        payload = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not payload:
            logger.warning(
                f"No valid fields to update for DM template {id}",
                extra={'template_id': id, 'updates': updates}
            )
            return True
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.patch(
                        f"{self._url}/rest/v1/dm_templates",
                        params={'id': f'eq.{id}'},
                        json=payload,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 204):
                        logger.debug(
                            f"Successfully updated DM template in Supabase: {id}",
                            extra={
                                'template_id': id,
                                'updates': list(payload.keys()),
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error updating DM template in Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'template_id': id
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'template_id': id
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'template_id': id,
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error updating DM template in Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'template_id': id,
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error updating DM template in Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'template_id': id
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error updating DM template in Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'template_id': id,
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error updating DM template in Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'template_id': id,
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def delete_dm_template(self, id: int, max_retries: int = 3) -> bool:
        """
        Delete a DM template from Supabase with retry logic.
        
        Implements exponential backoff retry strategy for transient failures:
        - Network errors: Retry with exponential backoff
        - Authentication errors: Disable integration and fail immediately
        - Rate limiting: Retry with exponential backoff + jitter
        
        Args:
            id: The template ID to delete
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if delete succeeded, False otherwise
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, skipping delete")
            return False
        
        # Validate parameters
        if not id:
            logger.error("Cannot delete DM template: id is required")
            return False
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.delete(
                        f"{self._url}/rest/v1/dm_templates",
                        params={'id': f'eq.{id}'},
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 204):
                        logger.debug(
                            f"Successfully deleted DM template from Supabase: {id}",
                            extra={
                                'template_id': id,
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error deleting DM template from Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'template_id': id
                            }
                        )
                        self.disable()
                        return False
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'template_id': id
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'template_id': id,
                                    'max_retries': max_retries
                                }
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error deleting DM template from Supabase: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'template_id': id,
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error deleting DM template from Supabase, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'template_id': id
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error deleting DM template from Supabase after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'template_id': id,
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error deleting DM template from Supabase: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'template_id': id,
                        'attempt': attempt + 1
                    }
                )
                return False
        
        # Should not reach here, but just in case
        return False
    
    async def get_dm_template(self, id: int) -> Optional[dict]:
        """
        Get a single DM template by ID from Supabase.
        
        Args:
            id: The template ID to retrieve
        
        Returns:
            Optional[dict]: Template dictionary with all fields, or None if not found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query DM template")
            return None
        
        # Validate parameters
        if not id:
            logger.error("Cannot query DM template: id is required")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'id': f'eq.{id}',
                    'select': '*',
                    'limit': '1'
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/dm_templates",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        logger.debug(
                            f"Retrieved DM template from Supabase: {id}",
                            extra={'template_id': id}
                        )
                        return results[0]
                    else:
                        logger.debug(
                            f"DM template not found in Supabase: {id}",
                            extra={'template_id': id}
                        )
                        return None
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying DM template: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'template_id': id
                        }
                    )
                    self.disable()
                    return None
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying DM template: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text,
                            'template_id': id
                        }
                    )
                    return None
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying DM template: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'template_id': id
                }
            )
            return None
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying DM template: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'template_id': id
                }
            )
            return None
    
    async def get_all_dm_templates(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        Get all DM templates from Supabase with pagination support.
        
        Templates are ordered by creation date (newest first).
        
        Args:
            limit: Maximum number of templates to return (default: 100)
            offset: Number of templates to skip for pagination (default: 0)
        
        Returns:
            list[dict]: List of template dictionaries with all fields, or empty list if none found
        """
        if not self._available:
            logger.debug("Supabase integration is disabled, cannot query DM templates")
            return []
        
        # Validate parameters
        if limit < 1:
            logger.warning(f"Invalid limit value {limit}, using default 100")
            limit = 100
        
        if offset < 0:
            logger.warning(f"Invalid offset value {offset}, using default 0")
            offset = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build query parameters using PostgREST syntax
                params = {
                    'select': '*',
                    'order': 'created_at.desc',
                    'limit': str(limit),
                    'offset': str(offset)
                }
                
                response = await client.get(
                    f"{self._url}/rest/v1/dm_templates",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # Success case
                if response.status_code == 200:
                    results = response.json()
                    logger.debug(
                        f"Retrieved {len(results)} DM templates from Supabase",
                        extra={
                            'count': len(results),
                            'limit': limit,
                            'offset': offset
                        }
                    )
                    return results
                
                # Authentication error - disable integration
                elif response.status_code in (401, 403):
                    logger.error(
                        f"Authentication error querying all DM templates: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text
                        }
                    )
                    self.disable()
                    return []
                
                # Other HTTP errors
                else:
                    logger.error(
                        f"HTTP error querying all DM templates: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'response_text': response.text
                        }
                    )
                    return []
        
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(
                f"Network error querying all DM templates: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error querying all DM templates: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            return []

    # ========== Location Sets Methods ==========
    
    async def create_location_set(self, name: str, description: str, locations: list[str], max_retries: int = 3) -> dict:
        """
        Create a new location set by uploading JSON to Supabase Storage and inserting metadata.
        
        This method:
        1. Generates a unique UUID for the file_path
        2. Uploads the Location_JSON to Supabase Storage at "location-files/{uuid}.json"
        3. Inserts metadata record into location_sets table
        4. Handles duplicate name errors with specific error messages
        
        Args:
            name: Unique name for the location set (3-100 characters)
            description: Description of the location set (max 500 characters)
            locations: List of location strings (min 1 item)
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            dict: Created location set metadata with fields:
                - id: UUID of the created record
                - name: Location set name
                - description: Location set description
                - file_path: Storage path ({uuid}.json)
                - location_count: Number of locations
                - created_at: Timestamp of creation
        
        Raises:
            ValueError: If validation fails (empty locations, invalid lengths)
            Exception: If upload or database insert fails
        """
        if not self._available:
            logger.error("Supabase integration is disabled, cannot create location set")
            raise Exception("Supabase integration is disabled")
        
        # Validate inputs
        if not name or len(name) < 3 or len(name) > 100:
            raise ValueError("Location set name must be between 3 and 100 characters")
        
        if not description or len(description) > 500:
            raise ValueError("Location set description must not exceed 500 characters")
        
        if not locations or len(locations) == 0:
            raise ValueError("Location set must contain at least one location")
        
        # Trim whitespace from location strings
        trimmed_locations = [loc.strip() for loc in locations if isinstance(loc, str) and loc.strip()]
        
        if len(trimmed_locations) == 0:
            raise ValueError("Location set must contain at least one non-empty location")
        
        # Validate all locations are strings
        if not all(isinstance(loc, str) for loc in locations):
            raise ValueError("All locations must be strings")
        
        # Generate UUID for file_path
        file_uuid = str(uuid.uuid4())
        file_path = f"{file_uuid}.json"
        
        # Prepare Location_JSON content
        location_json = {
            "nome": name,
            "descricao": description,
            "locais": trimmed_locations
        }
        
        # Upload JSON to Supabase Storage
        logger.info(
            f"Uploading location set '{name}' to Supabase Storage",
            extra={
                'location_set_name': name,
                'file_path': file_path,
                'location_count': len(trimmed_locations)
            }
        )
        
        upload_success = await self._upload_location_file(file_path, location_json, max_retries)
        
        if not upload_success:
            raise Exception(f"Failed to upload location file to storage: {file_path}")
        
        # Insert metadata record into location_sets table
        metadata = {
            'name': name,
            'description': description,
            'file_path': file_path,
            'location_count': len(trimmed_locations),
            'locations': trimmed_locations
        }
        
        logger.info(
            f"Inserting location set metadata for '{name}'",
            extra={'location_set_name': name, 'file_path': file_path}
        )
        
        try:
            created_record = await self._insert_location_set_metadata(metadata, max_retries)
            
            logger.info(
                f"Successfully created location set '{name}'",
                extra={
                    'id': created_record.get('id'),
                    'name': name,
                    'location_count': len(trimmed_locations)
                }
            )
            
            return created_record
            
        except Exception as e:
            # If metadata insert fails, attempt to clean up the uploaded file
            logger.error(
                f"Failed to insert location set metadata, attempting cleanup: {e}",
                extra={'location_set_name': name, 'file_path': file_path}
            )
            
            try:
                await self._delete_location_file(file_path)
                logger.info(f"Cleaned up orphaned file: {file_path}")
            except Exception as cleanup_error:
                logger.error(
                    f"Failed to clean up orphaned file {file_path}: {cleanup_error}",
                    extra={'file_path': file_path}
                )
            
            # Re-raise the original error
            raise
    
    async def _upload_location_file(self, file_path: str, content: dict, max_retries: int = 3) -> bool:
        """
        Upload Location_JSON to Supabase Storage.
        
        Args:
            file_path: Storage path in format "{uuid}.json"
            content: Location_JSON dictionary
            max_retries: Maximum number of retry attempts
        
        Returns:
            bool: True if upload succeeded, False otherwise
        """
        # Convert content to JSON bytes
        json_bytes = json.dumps(content, ensure_ascii=False, indent=2).encode('utf-8')
        
        # Check file size (10MB limit)
        if len(json_bytes) > 10 * 1024 * 1024:
            logger.error(
                f"Location file exceeds 10MB size limit: {len(json_bytes)} bytes",
                extra={'file_path': file_path, 'size_bytes': len(json_bytes)}
            )
            raise ValueError("Location file exceeds 10MB size limit")
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self._url}/storage/v1/object/location-files/{file_path}",
                        content=json_bytes,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        logger.debug(
                            f"Successfully uploaded location file: {file_path}",
                            extra={'file_path': file_path, 'attempt': attempt + 1}
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error uploading location file: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'file_path': file_path
                            }
                        )
                        self.disable()
                        return False
                    
                    # File too large
                    elif response.status_code == 413:
                        logger.error(
                            f"Location file too large: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'file_path': file_path,
                                'size_bytes': len(json_bytes)
                            }
                        )
                        raise ValueError("Location file exceeds size limit")
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'file_path': file_path
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={'file_path': file_path, 'max_retries': max_retries}
                            )
                            return False
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error uploading location file: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'file_path': file_path,
                                'attempt': attempt + 1
                            }
                        )
                        return False
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error uploading location file, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'file_path': file_path
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error uploading location file after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'file_path': file_path,
                            'max_retries': max_retries
                        }
                    )
                    return False
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error uploading location file: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'file_path': file_path,
                        'attempt': attempt + 1
                    }
                )
                return False
        
        return False
    
    async def _insert_location_set_metadata(self, metadata: dict, max_retries: int = 3) -> dict:
        """
        Insert location set metadata into the location_sets table.
        
        Args:
            metadata: Dictionary with name, description, file_path, location_count
            max_retries: Maximum number of retry attempts
        
        Returns:
            dict: Created record with id, name, description, file_path, location_count, created_at
        
        Raises:
            Exception: If insert fails or duplicate name exists
        """
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._url}/rest/v1/location_sets",
                        json=metadata,
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=representation'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 201):
                        result = response.json()
                        logger.debug(
                            f"Successfully inserted location set metadata: {metadata['name']}",
                            extra={'location_set_name': metadata['name'], 'attempt': attempt + 1}
                        )
                        return result[0] if isinstance(result, list) else result
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error inserting location set metadata: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'location_set_name': metadata['name']
                            }
                        )
                        self.disable()
                        raise Exception("Authentication error")
                    
                    # Duplicate name constraint violation
                    elif response.status_code == 409:
                        error_text = response.text.lower()
                        if 'unique' in error_text or 'duplicate' in error_text:
                            logger.warning(
                                f"Duplicate location set name: {metadata['name']}",
                                extra={'location_set_name': metadata['name']}
                            )
                            raise ValueError(f"Location set with name '{metadata['name']}' already exists")
                        else:
                            raise Exception(f"Conflict error: {response.text}")
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'location_set_name': metadata['name']
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={'location_set_name': metadata['name'], 'max_retries': max_retries}
                            )
                            raise Exception("Rate limited after multiple retries")
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error inserting location set metadata: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'location_set_name': metadata['name'],
                                'attempt': attempt + 1
                            }
                        )
                        raise Exception(f"HTTP error {response.status_code}: {response.text}")
            
            except ValueError:
                # Re-raise validation errors (duplicate name) without retry
                raise
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error inserting location set metadata, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'location_set_name': metadata['name']
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error inserting location set metadata after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'location_set_name': metadata['name'],
                            'max_retries': max_retries
                        }
                    )
                    raise Exception(f"Network error after {max_retries} attempts: {e}")
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error inserting location set metadata: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'location_set_name': metadata['name'],
                        'attempt': attempt + 1
                    }
                )
                raise
        
        raise Exception("Failed to insert location set metadata after all retries")
    
    async def _delete_location_file(self, file_path: str) -> bool:
        """
        Delete a location file from Supabase Storage.
        
        Args:
            file_path: Storage path in format "{uuid}.json"
        
        Returns:
            bool: True if deletion succeeded, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self._url}/storage/v1/object/location-files/{file_path}",
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code in (200, 204):
                    logger.debug(f"Successfully deleted location file: {file_path}")
                    return True
                else:
                    logger.warning(
                        f"Failed to delete location file: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'file_path': file_path
                        }
                    )
                    return False
        
        except Exception as e:
            logger.error(
                f"Error deleting location file: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'file_path': file_path
                }
            )
            return False
    
    async def get_all_location_sets(self, max_retries: int = 3) -> list[dict]:
        """
        Query all location sets from the location_sets table.
        
        This method:
        1. Queries all records from location_sets table
        2. Sorts by created_at descending (newest first)
        3. Returns list of location set metadata
        
        Args:
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            list[dict]: List of location set metadata records with fields:
                - id: UUID of the record
                - name: Location set name
                - description: Location set description
                - file_path: Storage path ({uuid}.json)
                - location_count: Number of locations
                - created_at: Timestamp of creation
        
        Raises:
            Exception: If query fails after all retries
        """
        if not self._available:
            logger.error("Supabase integration is disabled, cannot get location sets")
            raise Exception("Supabase integration is disabled")
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{self._url}/rest/v1/location_sets",
                        params={
                            'select': '*',
                            'order': 'created_at.desc'
                        },
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}'
                        }
                    )
                    
                    # Success case
                    if response.status_code == 200:
                        result = response.json()
                        logger.debug(
                            f"Successfully retrieved {len(result)} location sets",
                            extra={'count': len(result), 'attempt': attempt + 1}
                        )
                        return result
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error retrieving location sets: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text
                            }
                        )
                        self.disable()
                        raise Exception("Authentication error")
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={'max_retries': max_retries}
                            )
                            raise Exception("Rate limited after multiple retries")
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error retrieving location sets: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'attempt': attempt + 1
                            }
                        )
                        raise Exception(f"HTTP error {response.status_code}: {response.text}")
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error retrieving location sets, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error retrieving location sets after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'max_retries': max_retries
                        }
                    )
                    raise Exception(f"Network error after {max_retries} attempts: {e}")
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error retrieving location sets: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'attempt': attempt + 1
                    }
                )
                raise
        
        raise Exception("Failed to retrieve location sets after all retries")
    
    async def get_location_set_preview(self, location_set_id: str, limit: int = 10, max_retries: int = 3) -> dict:
        """
        Get a preview of the first N locations from a location set.
        
        This method:
        1. Downloads the Location_JSON file from Supabase Storage
        2. Parses the JSON and extracts the first N locations
        3. Handles files with fewer than N locations
        
        Args:
            location_set_id: UUID of the location set
            limit: Maximum number of locations to return (default: 10)
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            dict: Preview data with fields:
                - id: UUID of the location set
                - name: Location set name
                - preview: List of first N location strings
                - total_count: Total number of locations in the set
                - showing: Number of locations in the preview
        
        Raises:
            Exception: If location set not found or download fails
        """
        if not self._available:
            logger.error("Supabase integration is disabled, cannot get location set preview")
            raise Exception("Supabase integration is disabled")
        
        # First, get the location set metadata to retrieve file_path
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/location_sets",
                    params={
                        'select': '*',
                        'id': f'eq.{location_set_id}'
                    },
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result or len(result) == 0:
                        raise Exception(f"Location set not found: {location_set_id}")
                    
                    location_set = result[0]
                    file_path = location_set['file_path']
                    name = location_set['name']
                    location_count = location_set['location_count']
                else:
                    logger.error(
                        f"Failed to retrieve location set metadata: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'location_set_id': location_set_id
                        }
                    )
                    raise Exception(f"Failed to retrieve location set: {response.status_code}")
        
        except Exception as e:
            logger.error(
                f"Error retrieving location set metadata: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'location_set_id': location_set_id
                }
            )
            raise
        
        # Download the Location_JSON file from Supabase Storage
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(
                        f"{self._url}/storage/v1/object/public/location-files/{file_path}",
                        headers={
                            'apikey': self._key
                        }
                    )
                    
                    # Success case
                    if response.status_code == 200:
                        try:
                            location_json = response.json()
                            
                            # Extract locations array
                            if 'locais' not in location_json:
                                raise ValueError("Location JSON missing 'locais' field")
                            
                            all_locations = location_json['locais']
                            
                            # Extract first N locations (or all if fewer than N)
                            preview_locations = all_locations[:limit]
                            
                            logger.debug(
                                f"Successfully retrieved preview for location set '{name}'",
                                extra={
                                    'location_set_id': location_set_id,
                                    'total_count': len(all_locations),
                                    'showing': len(preview_locations),
                                    'attempt': attempt + 1
                                }
                            )
                            
                            return {
                                'id': location_set_id,
                                'name': name,
                                'preview': preview_locations,
                                'total_count': len(all_locations),
                                'showing': len(preview_locations)
                            }
                        
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(
                                f"Failed to parse location JSON: {type(e).__name__}",
                                extra={
                                    'error_type': type(e).__name__,
                                    'error_message': str(e),
                                    'file_path': file_path,
                                    'location_set_id': location_set_id
                                }
                            )
                            raise Exception(f"Failed to parse location file: {e}")
                    
                    # File not found
                    elif response.status_code == 404:
                        logger.error(
                            f"Location file not found in storage: {file_path}",
                            extra={
                                'file_path': file_path,
                                'location_set_id': location_set_id
                            }
                        )
                        raise Exception(f"Location file not found: {file_path}")
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error downloading location file: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'file_path': file_path,
                                'location_set_id': location_set_id
                            }
                        )
                        self.disable()
                        raise Exception("Authentication error")
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'file_path': file_path,
                                    'location_set_id': location_set_id
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'file_path': file_path,
                                    'location_set_id': location_set_id,
                                    'max_retries': max_retries
                                }
                            )
                            raise Exception("Rate limited after multiple retries")
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error downloading location file: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'file_path': file_path,
                                'location_set_id': location_set_id,
                                'attempt': attempt + 1
                            }
                        )
                        raise Exception(f"HTTP error {response.status_code}: {response.text}")
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error downloading location file, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'file_path': file_path,
                            'location_set_id': location_set_id
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error downloading location file after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'file_path': file_path,
                            'location_set_id': location_set_id,
                            'max_retries': max_retries
                        }
                    )
                    raise Exception(f"Network error after {max_retries} attempts: {e}")
            
            except Exception as e:
                # Unexpected errors - log and fail
                if "Failed to parse location file" in str(e) or "Location file not found" in str(e):
                    # Re-raise parsing and not found errors without retry
                    raise
                
                logger.error(
                    f"Unexpected error downloading location file: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'file_path': file_path,
                        'location_set_id': location_set_id,
                        'attempt': attempt + 1
                    }
                )
                raise
        
        raise Exception("Failed to download location file after all retries")

    async def get_location_set_full(self, location_set_id: str, max_retries: int = 3) -> dict:
        """
        Get the complete location array from a location set.
        
        This method:
        1. Downloads the Location_JSON file from Supabase Storage
        2. Parses the JSON and returns all locations
        3. Returns the full location array for use in the GMap extractor
        
        Args:
            location_set_id: UUID of the location set
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            dict: Full location data with fields:
                - id: UUID of the location set
                - name: Location set name
                - locations: Complete list of all location strings
                - total_count: Total number of locations in the set
        
        Raises:
            Exception: If location set not found or download fails
        """
        if not self._available:
            logger.error("Supabase integration is disabled, cannot get location set full")
            raise Exception("Supabase integration is disabled")
        
        # First, get the location set metadata to retrieve file_path
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/location_sets",
                    params={
                        'select': '*',
                        'id': f'eq.{location_set_id}'
                    },
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result or len(result) == 0:
                        raise Exception(f"Location set not found: {location_set_id}")
                    
                    location_set = result[0]
                    file_path = location_set['file_path']
                    name = location_set['name']
                    location_count = location_set['location_count']
                else:
                    logger.error(
                        f"Failed to retrieve location set metadata: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'location_set_id': location_set_id
                        }
                    )
                    raise Exception(f"Failed to retrieve location set: {response.status_code}")
        
        except Exception as e:
            logger.error(
                f"Error retrieving location set metadata: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'location_set_id': location_set_id
                }
            )
            raise
        
        # Download the Location_JSON file from Supabase Storage
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(
                        f"{self._url}/storage/v1/object/public/location-files/{file_path}",
                        headers={
                            'apikey': self._key
                        }
                    )
                    
                    # Success case
                    if response.status_code == 200:
                        try:
                            location_json = response.json()
                            
                            # Extract locations array
                            if 'locais' not in location_json:
                                raise ValueError("Location JSON missing 'locais' field")
                            
                            all_locations = location_json['locais']
                            
                            logger.debug(
                                f"Successfully retrieved full location set '{name}'",
                                extra={
                                    'location_set_id': location_set_id,
                                    'total_count': len(all_locations),
                                    'attempt': attempt + 1
                                }
                            )
                            
                            return {
                                'id': location_set_id,
                                'name': name,
                                'locations': all_locations,
                                'total_count': len(all_locations)
                            }
                        
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(
                                f"Failed to parse location JSON: {type(e).__name__}",
                                extra={
                                    'error_type': type(e).__name__,
                                    'error_message': str(e),
                                    'file_path': file_path,
                                    'location_set_id': location_set_id
                                }
                            )
                            raise Exception(f"Failed to parse location file: {e}")
                    
                    # File not found
                    elif response.status_code == 404:
                        logger.error(
                            f"Location file not found in storage: {file_path}",
                            extra={
                                'file_path': file_path,
                                'location_set_id': location_set_id
                            }
                        )
                        raise Exception(f"Location file not found: {file_path}")
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error downloading location file: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'file_path': file_path,
                                'location_set_id': location_set_id
                            }
                        )
                        self.disable()
                        raise Exception("Authentication error")
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'file_path': file_path,
                                    'location_set_id': location_set_id
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'file_path': file_path,
                                    'location_set_id': location_set_id,
                                    'max_retries': max_retries
                                }
                            )
                            raise Exception("Rate limited after multiple retries")
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error downloading location file: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'file_path': file_path,
                                'location_set_id': location_set_id,
                                'attempt': attempt + 1
                            }
                        )
                        raise Exception(f"HTTP error {response.status_code}: {response.text}")
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error downloading location file, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'file_path': file_path,
                            'location_set_id': location_set_id
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error downloading location file after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'file_path': file_path,
                            'location_set_id': location_set_id,
                            'max_retries': max_retries
                        }
                    )
                    raise Exception(f"Network error after {max_retries} attempts: {e}")
            
            except Exception as e:
                # Unexpected errors - log and fail
                if "Failed to parse location file" in str(e) or "Location file not found" in str(e):
                    # Re-raise parsing and not found errors without retry
                    raise
                
                logger.error(
                    f"Unexpected error downloading location file: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'file_path': file_path,
                        'location_set_id': location_set_id,
                        'attempt': attempt + 1
                    }
                )
                raise
        
        raise Exception("Failed to download location file after all retries")

    async def delete_location_set(self, location_set_id: str, max_retries: int = 3) -> bool:
        """
        Delete a location set by removing both the JSON file from Supabase Storage and the metadata record.
        
        This method:
        1. Retrieves the location set metadata to get the file_path
        2. Attempts to delete the JSON file from Supabase Storage
        3. Deletes the metadata record from location_sets table
        4. Handles file deletion failures gracefully (logs error but continues with database deletion)
        
        Args:
            location_set_id: UUID of the location set to delete
            max_retries: Maximum number of retry attempts for network errors (default: 3)
        
        Returns:
            bool: True if deletion succeeded, False otherwise
        
        Raises:
            Exception: If location set not found or database deletion fails
        """
        if not self._available:
            logger.error("Supabase integration is disabled, cannot delete location set")
            raise Exception("Supabase integration is disabled")
        
        # First, get the location set metadata to retrieve file_path
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/location_sets",
                    params={
                        'select': '*',
                        'id': f'eq.{location_set_id}'
                    },
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result or len(result) == 0:
                        raise Exception(f"Location set not found: {location_set_id}")
                    
                    location_set = result[0]
                    file_path = location_set['file_path']
                    name = location_set['name']
                else:
                    logger.error(
                        f"Failed to retrieve location set metadata: {response.status_code}",
                        extra={
                            'status_code': response.status_code,
                            'location_set_id': location_set_id
                        }
                    )
                    raise Exception(f"Failed to retrieve location set: {response.status_code}")
        
        except Exception as e:
            logger.error(
                f"Error retrieving location set metadata for deletion: {type(e).__name__}",
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'location_set_id': location_set_id
                }
            )
            raise
        
        # Attempt to delete the file from Supabase Storage
        # Handle failures gracefully - log error but continue with database deletion
        file_deleted = await self._delete_location_file(file_path)
        
        if not file_deleted:
            logger.warning(
                f"Failed to delete location file from storage, continuing with database deletion",
                extra={
                    'file_path': file_path,
                    'location_set_id': location_set_id,
                    'location_set_name': name
                }
            )
        else:
            logger.info(
                f"Successfully deleted location file from storage: {file_path}",
                extra={
                    'file_path': file_path,
                    'location_set_id': location_set_id,
                    'location_set_name': name
                }
            )
        
        # Delete the metadata record from location_sets table
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.delete(
                        f"{self._url}/rest/v1/location_sets",
                        params={
                            'id': f'eq.{location_set_id}'
                        },
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}'
                        }
                    )
                    
                    # Success case
                    if response.status_code in (200, 204):
                        logger.info(
                            f"Successfully deleted location set '{name}'",
                            extra={
                                'location_set_id': location_set_id,
                                'location_set_name': name,
                                'file_deleted': file_deleted,
                                'attempt': attempt + 1
                            }
                        )
                        return True
                    
                    # Authentication error - disable integration
                    elif response.status_code in (401, 403):
                        logger.error(
                            f"Authentication error deleting location set: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'location_set_id': location_set_id,
                                'location_set_name': name
                            }
                        )
                        self.disable()
                        raise Exception("Authentication error")
                    
                    # Rate limiting - retry with backoff
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"Rate limited by Supabase (429), retrying in {wait_time:.2f}s",
                                extra={
                                    'attempt': attempt + 1,
                                    'max_retries': max_retries,
                                    'wait_time': wait_time,
                                    'location_set_id': location_set_id,
                                    'location_set_name': name
                                }
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(
                                f"Rate limited by Supabase after {max_retries} attempts",
                                extra={
                                    'location_set_id': location_set_id,
                                    'location_set_name': name,
                                    'max_retries': max_retries
                                }
                            )
                            raise Exception("Rate limited after multiple retries")
                    
                    # Other HTTP errors
                    else:
                        logger.error(
                            f"HTTP error deleting location set: {response.status_code}",
                            extra={
                                'status_code': response.status_code,
                                'response_text': response.text,
                                'location_set_id': location_set_id,
                                'location_set_name': name,
                                'attempt': attempt + 1
                            }
                        )
                        raise Exception(f"HTTP error {response.status_code}: {response.text}")
            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # Network errors - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Network error deleting location set, retrying in {wait_time:.2f}s: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time,
                            'location_set_id': location_set_id,
                            'location_set_name': name
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Network error deleting location set after {max_retries} attempts: {type(e).__name__}",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'location_set_id': location_set_id,
                            'location_set_name': name,
                            'max_retries': max_retries
                        }
                    )
                    raise Exception(f"Network error after {max_retries} attempts: {e}")
            
            except Exception as e:
                # Unexpected errors - log and fail
                logger.error(
                    f"Unexpected error deleting location set: {type(e).__name__}",
                    extra={
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'location_set_id': location_set_id,
                        'location_set_name': name,
                        'attempt': attempt + 1
                    }
                )
                raise
        
        raise Exception("Failed to delete location set after all retries")

    # ========== Leads Management Methods ==========
    
    async def get_leads_filtered(
        self,
        limit: int = 100,
        offset: int = 0,
        conjunto: str = None,
        cidade: str = None,
        search: str = None
    ) -> list[dict]:
        """
        Get leads with filtering and pagination.
        
        Args:
            limit: Maximum number of leads to return
            offset: Number of leads to skip
            conjunto: Filter by conjunto_de_locais
            cidade: Filter by cidade
            search: Search term for nome, telefone, website
        
        Returns:
            list[dict]: List of lead dictionaries
        """
        if not self._available:
            logger.debug("Supabase integration is disabled")
            return []
        
        try:
            # Build query parameters
            params = {
                'select': '*',
                'order': 'created_at.desc',
                'limit': str(limit),
                'offset': str(offset)
            }
            
            # Add filters
            if conjunto:
                params['conjunto_de_locais'] = f'eq.{conjunto}'
            if cidade:
                params['cidade'] = f'eq.{cidade}'
            if search:
                params['or'] = f'(nome.ilike.*{search}*,telefone.ilike.*{search}*,website.ilike.*{search}*)'
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error fetching leads: {response.status_code}")
                    return []
        
        except Exception as e:
            logger.error(f"Error in get_leads_filtered: {type(e).__name__}")
            return []
    
    async def count_leads(
        self,
        conjunto: str = None,
        cidade: str = None,
        search: str = None
    ) -> int:
        """Count total leads matching filters."""
        if not self._available:
            return 0
        
        try:
            params = {'select': 'id'}
            
            if conjunto:
                params['conjunto_de_locais'] = f'eq.{conjunto}'
            if cidade:
                params['cidade'] = f'eq.{cidade}'
            if search:
                params['or'] = f'(nome.ilike.*{search}*,telefone.ilike.*{search}*,website.ilike.*{search}*)'
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return len(data)
                return 0
        
        except Exception as e:
            logger.error(f"Error in count_leads: {type(e).__name__}: {str(e)}")
            return 0
    
    async def get_leads_stats(self) -> dict:
        """Get statistics about leads."""
        if not self._available:
            return {}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get all leads to count
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params={'select': 'telefone,website,email'},
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total = len(data)
                    with_phone = sum(1 for item in data if item.get('telefone') and item['telefone'] != 'Sem Telefone')
                    with_website = sum(1 for item in data if item.get('website') and item['website'] != 'Sem Website')
                    with_email = sum(1 for item in data if item.get('email') and item['email'])
                    
                    return {
                        'total': total,
                        'with_phone': with_phone,
                        'with_website': with_website,
                        'with_email': with_email,
                        'without_phone': total - with_phone,
                        'without_website': total - with_website
                    }
                return {}
        
        except Exception as e:
            logger.error(f"Error in get_leads_stats: {type(e).__name__}: {str(e)}")
            return {}
    
    async def get_distinct_conjuntos(self) -> list[str]:
        """Get list of distinct conjunto_de_locais values."""
        if not self._available:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params={'select': 'conjunto_de_locais'},
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    conjuntos = list(set(item['conjunto_de_locais'] for item in data if item.get('conjunto_de_locais')))
                    return sorted(conjuntos)
                return []

        except Exception as e:
            logger.error(f"Error in get_distinct_conjuntos: {type(e).__name__}")
            return []

    async def get_distinct_cidades(self, conjunto: str = None) -> list[str]:
        """Get list of distinct cidades, optionally filtered by conjunto."""
        if not self._available:
            return []

        try:
            params = {'select': 'cidade'}
            if conjunto:
                params['conjunto_de_locais'] = f'eq.{conjunto}'

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/gmap_leads",
                    params=params,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    cidades = list(set(item['cidade'] for item in data if item.get('cidade')))
                    return sorted(cidades)
                return []

        except Exception as e:
            logger.error(f"Error in get_distinct_cidades: {type(e).__name__}")
            return []

    async def delete_lead(self, lead_id: int) -> bool:
        """Delete a lead by ID."""
        if not self._available:
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self._url}/rest/v1/gmap_leads",
                    params={'id': f'eq.{lead_id}'},
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )

                return response.status_code in (200, 204)

        except Exception as e:
            logger.error(f"Error in delete_lead: {type(e).__name__}")
            return False

    async def update_lead(self, lead_id: int, lead_data: dict) -> bool:
        """Update a lead by ID."""
        if not self._available:
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self._url}/rest/v1/gmap_leads",
                    params={'id': f'eq.{lead_id}'},
                    json=lead_data,
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )

                return response.status_code in (200, 204)

        except Exception as e:
            logger.error(f"Error in update_lead: {type(e).__name__}")
            return False


    async def get_app_setting(self, user_id: str, key: str) -> Optional[dict]:
        """Get an application setting for a specific user."""
        if not self._available or not user_id:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/app_settings",
                    params={
                        'user_id': f'eq.{user_id}',
                        'key': f'eq.{key}',
                        'select': 'value',
                        'limit': '1'
                    },
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        val = data[0].get('value')
                        # Value might be stringified JSON or plain text
                        try:
                            return json.loads(val) if val else None
                        except:
                            return val
                return None
                
        except Exception as e:
            logger.error(f"Error in get_app_setting: {type(e).__name__}")
            return None

    async def set_app_setting(self, user_id: str, key: str, value: any) -> bool:
        """Set or update an application setting for a user."""
        if not self._available or not user_id:
            return False

        # Convert dict to JSON string if needed, app_settings.value is text
        value_str = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Upsert is achieved by checking if exists first, then POST or PATCH
                # For PostgREST, we can use ON CONFLICT if we had unique constraints,
                # but let's do a simple GET then POST/PATCH
                
                get_resp = await client.get(
                    f"{self._url}/rest/v1/app_settings",
                    params={'user_id': f'eq.{user_id}', 'key': f'eq.{key}', 'select': 'id'},
                    headers={'apikey': self._key, 'Authorization': f'Bearer {self._service_key}'}
                )
                
                existing = get_resp.json() if get_resp.status_code == 200 else []
                
                if existing and len(existing) > 0:
                    # Update
                    patch_resp = await client.patch(
                        f"{self._url}/rest/v1/app_settings",
                        params={'id': f"eq.{existing[0]['id']}"},
                        json={'value': value_str},
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json'
                        }
                    )
                    return patch_resp.status_code in (200, 204)
                else:
                    # Insert
                    post_resp = await client.post(
                        f"{self._url}/rest/v1/app_settings",
                        json={'user_id': user_id, 'key': key, 'value': value_str},
                        headers={
                            'apikey': self._key,
                            'Authorization': f'Bearer {self._service_key}',
                            'Content-Type': 'application/json'
                        }
                    )
                    return post_resp.status_code in (200, 201)
                    
        except Exception as e:
            logger.error(f"Error in set_app_setting: {type(e).__name__}")
            return False

    async def get_active_webhooks(self, user_id: str) -> list[dict]:
        """
        Get all active Google Sheets webhooks for a user.
        
        Args:
            user_id: The user ID to filter webhooks by
            
        Returns:
            list[dict]: List of active webhook dictionaries with fields:
                - id: webhook ID
                - name: webhook name
                - webhook_url: the webhook URL
                - daily_limit: daily limit for this webhook (default: 80)
                - active: whether webhook is active
        """
        if not self._available or not user_id:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._url}/rest/v1/gsheets_webhooks",
                    params={
                        'user_id': f'eq.{user_id}',
                        'active': 'eq.true',
                        'select': 'id,name,webhook_url,daily_limit,active'
                    },
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    webhooks = response.json()
                    logger.debug(f"Found {len(webhooks)} active webhooks for user {user_id}")
                    return webhooks
                else:
                    logger.error(f"Error fetching webhooks: HTTP {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error in get_active_webhooks: {type(e).__name__} - {str(e)}")
            return []
    
    async def mark_leads_synced(self, lead_ids: list[int]) -> bool:
        """
        Mark leads as synced to Google Sheets.
        
        Args:
            lead_ids: List of lead IDs to mark as synced
            
        Returns:
            bool: True if update succeeded, False otherwise
        """
        if not self._available or not lead_ids:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Build filter for multiple IDs: id=in.(1,2,3)
                ids_str = ','.join(str(id) for id in lead_ids)
                
                response = await client.patch(
                    f"{self._url}/rest/v1/gmap_leads",
                    params={'id': f'in.({ids_str})'},
                    json={'synced_to_sheets': True},
                    headers={
                        'apikey': self._key,
                        'Authorization': f'Bearer {self._service_key}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    }
                )
                
                if response.status_code in (200, 204):
                    logger.debug(f"Marked {len(lead_ids)} leads as synced")
                    return True
                else:
                    logger.error(f"Error marking leads as synced: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error in mark_leads_synced: {type(e).__name__} - {str(e)}")
            return False


# Global singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Get the singleton Supabase client instance.
    
    Returns:
        SupabaseClient: The singleton Supabase client instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

