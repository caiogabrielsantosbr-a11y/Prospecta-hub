"""
Google Maps Sync Configuration
Defines configuration for Google Sheets synchronization modes and validation.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class SyncMode(str, Enum):
    """Sync mode enumeration"""
    AO_CONCLUIR = "ao_concluir"
    POR_QUANTIDADE = "por_quantidade"
    POR_TEMPO = "por_tempo"


@dataclass
class SyncConfig:
    """
    Configuration for Google Sheets synchronization.
    
    Attributes:
        sync_mode: Synchronization mode (ao_concluir, por_quantidade, por_tempo)
        sync_quantity: Number of leads per batch (1-100, only for por_quantidade mode)
        sync_interval_seconds: Interval in seconds (10-300, only for por_tempo mode)
    """
    sync_mode: SyncMode = SyncMode.AO_CONCLUIR
    sync_quantity: Optional[int] = 10
    sync_interval_seconds: Optional[int] = 30
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Validate sync_quantity
        if self.sync_quantity is not None:
            if not isinstance(self.sync_quantity, int):
                raise ValueError(f"sync_quantity must be int, got {type(self.sync_quantity)}")
            if not (1 <= self.sync_quantity <= 100):
                raise ValueError(f"sync_quantity must be between 1 and 100, got {self.sync_quantity}")
        
        # Validate sync_interval_seconds
        if self.sync_interval_seconds is not None:
            if not isinstance(self.sync_interval_seconds, int):
                raise ValueError(f"sync_interval_seconds must be int, got {type(self.sync_interval_seconds)}")
            if not (10 <= self.sync_interval_seconds <= 300):
                raise ValueError(f"sync_interval_seconds must be between 10 and 300, got {self.sync_interval_seconds}")
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SyncConfig':
        """
        Parse SyncConfig from dictionary.
        
        Args:
            data: Dictionary with sync configuration
            
        Returns:
            SyncConfig instance
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")
        
        sync_mode = data.get('sync_mode', 'ao_concluir')
        if sync_mode not in [m.value for m in SyncMode]:
            raise ValueError(f"Invalid sync_mode: {sync_mode}. Must be one of: {[m.value for m in SyncMode]}")
        
        return cls(
            sync_mode=SyncMode(sync_mode),
            sync_quantity=data.get('sync_quantity', 10),
            sync_interval_seconds=data.get('sync_interval_seconds', 30)
        )
    
    def to_dict(self) -> dict:
        """
        Convert SyncConfig to dictionary (pretty printer).
        
        Returns:
            Dictionary representation
        """
        return {
            'sync_mode': self.sync_mode.value,
            'sync_quantity': self.sync_quantity,
            'sync_interval_seconds': self.sync_interval_seconds
        }
    
    @classmethod
    def default(cls) -> 'SyncConfig':
        """Return default configuration"""
        return cls(
            sync_mode=SyncMode.AO_CONCLUIR,
            sync_quantity=10,
            sync_interval_seconds=30
        )
