"""
Google Maps Sync Manager
Manages synchronization of leads to Google Sheets with batch accumulation and retry logic.
Supports multiple webhooks with distribution strategies.
"""
import asyncio
import time
import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class SyncStats:
    """Statistics for synchronization operations"""
    synced_batches: int = 0
    synced_total: int = 0
    sync_failures: int = 0
    consecutive_failures: int = 0
    last_sync_time: float = field(default_factory=time.time)
    sync_disabled: bool = False


class SyncManager:
    """
    Manages synchronization of leads to Google Sheets.
    
    Handles:
    - Batch accumulation based on sync mode
    - Multiple webhooks with distribution strategies
    - Retry logic with exponential backoff
    - Circuit breaker after consecutive failures
    - Statistics tracking
    """
    
    def __init__(self, config: 'SyncConfig', user_id: Optional[str], supabase_client, info, tm):
        self.config = config
        self.user_id = user_id
        self.supabase_client = supabase_client
        self.info = info
        self.tm = tm
        self.stats = SyncStats()
        self.pending_leads: List[Dict] = []
        self.leads_since_last_sync = 0
        self.webhooks: List[Dict] = []
        
    async def initialize(self):
        """Load active webhooks from Supabase"""
        if self.user_id and self.supabase_client.is_available():
            self.webhooks = await self.supabase_client.get_active_webhooks(self.user_id)
            if self.webhooks:
                self.info.add_log(f"Carregadas {len(self.webhooks)} planilhas ativas para sincronização", "info")
            else:
                self.info.add_log("Nenhuma planilha ativa configurada - sincronização desabilitada", "warning")
        
    async def add_lead(self, lead: Dict) -> None:
        """
        Add a lead to the pending batch.
        
        Args:
            lead: Lead dictionary with all fields
        """
        self.pending_leads.append(lead)
        self.leads_since_last_sync += 1
        
        # Check if we should sync based on mode
        if self.config.sync_mode.value == 'por_quantidade':
            if self.leads_since_last_sync >= self.config.sync_quantity:
                await self.sync_batch()
        elif self.config.sync_mode.value == 'por_tempo':
            elapsed = time.time() - self.stats.last_sync_time
            if elapsed >= self.config.sync_interval_seconds:
                await self.sync_batch()
    
    def _distribute_leads(self, leads: List[Dict], distribution: str = 'equal') -> List[tuple]:
        """
        Distribute leads among webhooks based on strategy.
        
        Args:
            leads: List of leads to distribute
            distribution: Distribution strategy ('equal', 'all', 'daily_limit')
            
        Returns:
            List of (webhook, leads_batch) tuples
        """
        if not self.webhooks or not leads:
            return []
        
        assignments = []
        
        if distribution == 'all':
            # Send all leads to all webhooks
            for webhook in self.webhooks:
                assignments.append((webhook, leads))
                
        elif distribution == 'equal':
            # Distribute leads equally among webhooks
            chunk_size = len(leads) // len(self.webhooks)
            remainder = len(leads) % len(self.webhooks)
            
            start_idx = 0
            for i, webhook in enumerate(self.webhooks):
                # Add 1 extra lead to first 'remainder' webhooks
                current_chunk_size = chunk_size + (1 if i < remainder else 0)
                end_idx = start_idx + current_chunk_size
                assignments.append((webhook, leads[start_idx:end_idx]))
                start_idx = end_idx
                
        elif distribution == 'daily_limit':
            # Distribute based on daily_limit of each webhook
            remaining = leads.copy()
            for webhook in self.webhooks:
                limit = webhook.get('daily_limit', 80)
                chunk = remaining[:limit]
                if chunk:
                    assignments.append((webhook, chunk))
                    remaining = remaining[limit:]
                if not remaining:
                    break
        
        return assignments
    
    async def sync_batch(self, force: bool = False) -> bool:
        """
        Sync accumulated leads to Google Sheets.
        
        Args:
            force: Force sync even if circuit breaker is active
            
        Returns:
            True if sync succeeded, False otherwise
        """
        if not self.pending_leads:
            return True
        
        if self.stats.sync_disabled and not force:
            self.info.add_log("Sincronização desabilitada (circuit breaker ativo)", "warning")
            return False
        
        if not self.webhooks:
            self.info.add_log("Nenhuma planilha configurada, pulando sincronização", "warning")
            return False
        
        # Distribute leads among webhooks (using 'equal' strategy)
        assignments = self._distribute_leads(self.pending_leads, distribution='equal')
        
        total_sent = 0
        total_skipped = 0
        all_success = True
        synced_lead_ids = []
        
        # Send to each webhook with retry
        for webhook, batch in assignments:
            if not batch:
                continue
                
            success = await self._send_to_webhook(webhook, batch)
            if success:
                # Parse response to get actual counts
                total_sent += len(batch)
                # Collect IDs of successfully synced leads
                for lead in batch:
                    if 'id' in lead:
                        synced_lead_ids.append(lead['id'])
            else:
                all_success = False
        
        if all_success:
            # Update stats
            self.stats.synced_batches += 1
            self.stats.synced_total += total_sent
            self.stats.consecutive_failures = 0
            self.stats.last_sync_time = time.time()
            
            # Mark leads as synced in database
            if synced_lead_ids and self.supabase_client.is_available():
                await self.supabase_client.mark_leads_synced(synced_lead_ids)
            
            # Clear pending leads
            self.pending_leads.clear()
            self.leads_since_last_sync = 0
            
            # Log success
            msg = f"Sincronizados {total_sent} leads para {len(assignments)} planilha(s)"
            self.info.add_log(msg, "success")
            
            # Log next sync info
            if self.config.sync_mode.value == 'por_quantidade':
                remaining = self.config.sync_quantity
                self.info.add_log(f"Próxima sincronização em {remaining} leads", "info")
            elif self.config.sync_mode.value == 'por_tempo':
                self.info.add_log(f"Próxima sincronização em {self.config.sync_interval_seconds} segundos", "info")
            
            return True
        else:
            self.stats.sync_failures += 1
            self.stats.consecutive_failures += 1
            
            # Circuit breaker: disable after 3 consecutive failures
            if self.stats.consecutive_failures >= 3:
                self.stats.sync_disabled = True
                self.info.add_log("Sincronização automática desabilitada após múltiplas falhas", "error")
            
            return False
    
    async def _send_to_webhook(self, webhook: Dict, batch: List[Dict]) -> bool:
        """
        Send a batch of leads to a single webhook with retry logic.
        
        Args:
            webhook: Webhook dictionary with url and name
            batch: List of leads to send
            
        Returns:
            True if send succeeded, False otherwise
        """
        webhook_url = webhook.get('webhook_url')
        webhook_name = webhook.get('name', 'Unknown')
        
        if not webhook_url:
            self.info.add_log(f"Webhook {webhook_name} sem URL configurada", "error")
            return False
        
        # Retry with exponential backoff: 1s, 2s, 4s
        for attempt in range(3):
            try:
                payload = {
                    'action': 'add_leads',
                    'leads': [self._format_lead(lead) for lead in batch]
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(webhook_url, json=payload)
                    
                    if response.status_code in (200, 201):
                        result = response.json()
                        added = result.get('rows_added', 0)
                        skipped = result.get('skipped', 0)
                        
                        # Log success
                        msg = f"→ {webhook_name}: {added} leads"
                        if skipped > 0:
                            msg += f" ({skipped} duplicados)"
                        self.info.add_log(msg, "success")
                        
                        return True
                    else:
                        raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            except Exception as e:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                self.info.add_log(f"Erro em {webhook_name} (tentativa {attempt + 1}/3): {str(e)}", "error")
                
                if attempt < 2:
                    await asyncio.sleep(wait_time)
                else:
                    return False
        
        return False
    
    async def finalize(self) -> None:
        """
        Finalize synchronization (called when extraction completes).
        Sends any remaining pending leads.
        """
        if self.pending_leads:
            self.info.add_log(f"Finalizando: enviando {len(self.pending_leads)} leads pendentes", "info")
            await self.sync_batch(force=True)
        
        # Log final stats
        if self.stats.synced_total > 0:
            self.info.add_log(
                f"Sincronização concluída: {self.stats.synced_total} leads em {self.stats.synced_batches} batches",
                "success"
            )
        
        if self.stats.sync_failures > 0:
            unsync_count = len(self.pending_leads)
            if unsync_count > 0:
                self.info.add_log(f"{unsync_count} leads não foram sincronizados", "warning")
    
    def _format_lead(self, lead: Dict) -> Dict:
        """
        Format lead for AppScript payload.
        
        Args:
            lead: Lead dictionary from database
            
        Returns:
            Formatted lead with uppercase field names
        """
        return {
            'EMPRESA': lead.get('nome', ''),
            'EMAIL': lead.get('email', ''),
            'TELEFONE': lead.get('telefone', ''),
            'CIDADE': lead.get('cidade', ''),
            'WEBSITE': lead.get('website', '')
        }
