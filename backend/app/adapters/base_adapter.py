import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.external_record import AdapterFetchResult, RecordCategory

logger = logging.getLogger("ner_logitrack.adapters")

class BaseExternalAdapter(ABC):
    def __init__(self, provider_name: str, category: RecordCategory, timeout_seconds: float = 4.0):
        self.provider_name = provider_name
        self.category = category
        self.timeout_seconds = timeout_seconds

    def get_iso_timestamp(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @abstractmethod
    async def fetch(self, state_filter: Optional[str] = None) -> AdapterFetchResult:
        """
        Executes external HTTP request / API stream and returns standard AdapterFetchResult.
        Must NOT generate fake mock data on failure. If provider API fails, return is_available=False.
        """
        pass
