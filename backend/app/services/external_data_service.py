import time
import logging
import asyncio
from typing import Optional, List, Dict, Any

from app.adapters.news_adapter import GoogleNewsRSSAdapter
from app.adapters.weather_adapter import OpenMeteoWeatherAdapter
from app.adapters.disaster_adapter import DisasterFeedAdapter
from app.adapters.govt_adapter import BROGovInfraAdapter
from app.adapters.road_adapter import RoadConditionAdapter

from app.models.external_record import (
    ExternalRecord,
    AdapterFetchResult,
    ExternalDataResponse,
    RecordCategory
)

logger = logging.getLogger("ner_logitrack.external_data_service")

class ExternalDataManager:
    def __init__(self):
        self.news_adapter = GoogleNewsRSSAdapter()
        self.weather_adapter = OpenMeteoWeatherAdapter()
        self.disaster_adapter = DisasterFeedAdapter()
        self.govt_adapter = BROGovInfraAdapter()
        self.road_adapter = RoadConditionAdapter()

        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl_seconds: float = 300.0  # 5 minutes cache

    async def fetch_category_records(
        self,
        category: RecordCategory,
        state_filter: Optional[str] = None,
        force_refresh: bool = False
    ) -> AdapterFetchResult:
        cache_key = f"{category.value}:{state_filter or 'all'}"
        now = time.time()

        if not force_refresh and cache_key in self._cache:
            last_time = self._cache_timestamps.get(cache_key, 0.0)
            if now - last_time < self._cache_ttl_seconds:
                return self._cache[cache_key]

        adapter = None
        if category == RecordCategory.NEWS:
            adapter = self.news_adapter
        elif category == RecordCategory.WEATHER:
            adapter = self.weather_adapter
        elif category == RecordCategory.DISASTER:
            adapter = self.disaster_adapter
        elif category == RecordCategory.GOVT_NOTICE:
            adapter = self.govt_adapter
        elif category == RecordCategory.ROAD_CONDITION:
            adapter = self.road_adapter

        if not adapter:
            return AdapterFetchResult(
                provider_name="Unknown",
                category=category,
                is_available=False,
                total_records=0,
                records=[],
                error_message=f"No provider adapter registered for category '{category.value}'",
                retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )

        result = await adapter.fetch(state_filter=state_filter)
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = now
        return result

    async def fetch_all_external_records(
        self,
        state_filter: Optional[str] = None,
        force_refresh: bool = False
    ) -> ExternalDataResponse:
        categories = [
            RecordCategory.NEWS,
            RecordCategory.WEATHER,
            RecordCategory.DISASTER,
            RecordCategory.GOVT_NOTICE,
            RecordCategory.ROAD_CONDITION
        ]

        tasks = [
            self.fetch_category_records(cat, state_filter=state_filter, force_refresh=force_refresh)
            for cat in categories
        ]

        results: List[AdapterFetchResult] = await asyncio.gather(*tasks)

        all_records: List[ExternalRecord] = []
        provider_summary: Dict[str, Any] = {}
        any_available = False

        for res in results:
            provider_summary[res.provider_name] = {
                "category": res.category.value,
                "is_available": res.is_available,
                "total_records": res.total_records,
                "error_message": res.error_message
            }
            if res.is_available:
                any_available = True
                all_records.extend(res.records)

        return ExternalDataResponse(
            status="SUCCESS" if any_available else "UNAVAILABLE",
            is_available=any_available,
            total_results=len(all_records),
            records=all_records,
            crawled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            provider_summary=provider_summary
        )

_external_data_manager_instance: Optional[ExternalDataManager] = None

def get_external_data_manager() -> ExternalDataManager:
    global _external_data_manager_instance
    if _external_data_manager_instance is None:
        _external_data_manager_instance = ExternalDataManager()
    return _external_data_manager_instance
