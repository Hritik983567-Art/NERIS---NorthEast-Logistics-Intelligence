import time
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import asyncio
from typing import Optional, List, Dict, Any, Tuple

from app.adapters.base_adapter import BaseExternalAdapter
from app.models.external_record import (
    AdapterFetchResult,
    ExternalRecord,
    RecordCategory,
    SeverityLevel,
    LocationMetadata
)

logger = logging.getLogger("ner_logitrack.adapters.govt")

GOVT_TOPICS = [
    {"query": "Border Roads Organisation BRO North East highway", "default_state": "Arunachal Pradesh"},
    {"query": "NHIDCL North East highway road restoration", "default_state": "Nagaland"},
    {"query": "Assam PWD highway bridge clearance", "default_state": "Assam"}
]

class BROGovInfraAdapter(BaseExternalAdapter):
    def __init__(self):
        super().__init__(
            provider_name="BRO & NHIDCL Official Infrastructure Portal",
            category=RecordCategory.GOVT_NOTICE,
            timeout_seconds=4.0
        )

    def _fetch_topic_records(self, topic: Dict[str, str], retrieved_at: str) -> Tuple[List[ExternalRecord], bool]:
        query_str = topic["query"]
        encoded_query = urllib.parse.quote(query_str)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        topic_records: List[ExternalRecord] = []
        is_error = False

        try:
            req = urllib.request.Request(
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NERIS-GovtAdapter/2.4'}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)

                for item in root.findall('.//item')[:2]:
                    raw_title = item.findtext('title', 'BRO Official Advisory')
                    parts = raw_title.rsplit(' - ', 1)
                    clean_title = parts[0].strip()
                    publisher_name = parts[1].strip() if len(parts) > 1 else "BRO / NHIDCL Press Directorate"

                    link = item.findtext('link', rss_url)
                    pub_date = item.findtext('pubDate', retrieved_at)
                    description_raw = item.findtext('description', clean_title)
                    clean_summary = re.sub('<[^<]+?>', '', description_raw).strip()
                    if len(clean_summary) > 240:
                        clean_summary = clean_summary[:237] + "..."

                    topic_records.append(ExternalRecord(
                        id=f"govt-{abs(hash(clean_title))}",
                        category=RecordCategory.GOVT_NOTICE,
                        source=publisher_name,
                        source_url=link,
                        retrieved_at=retrieved_at,
                        published_at=pub_date,
                        title=clean_title,
                        content_summary=clean_summary if clean_summary else clean_title,
                        location=LocationMetadata(state=topic["default_state"]),
                        severity=SeverityLevel.MODERATE,
                        is_live=True,
                        extra_metadata={"agency": "BRO / NHIDCL / PWD"}
                    ))
        except Exception as err:
            is_error = True
            logger.warning(f"BROGovInfraAdapter query error for '{query_str}': {err}")

        return topic_records, is_error

    async def fetch(self, state_filter: Optional[str] = None) -> AdapterFetchResult:
        retrieved_at = self.get_iso_timestamp()
        records: List[ExternalRecord] = []
        seen_titles = set()

        tasks = [asyncio.to_thread(self._fetch_topic_records, topic, retrieved_at) for topic in GOVT_TOPICS]
        results = await asyncio.gather(*tasks)

        fetch_errors = 0
        for topic_records, is_err in results:
            if is_err:
                fetch_errors += 1
            for rec in topic_records:
                if rec.title not in seen_titles:
                    seen_titles.add(rec.title)
                    if not state_filter or state_filter.lower() == "all" or (rec.location and rec.location.state and rec.location.state.lower() == state_filter.lower()):
                        records.append(rec)

        if fetch_errors == len(GOVT_TOPICS) and len(records) == 0:
            return AdapterFetchResult(
                provider_name=self.provider_name,
                category=self.category,
                is_available=False,
                total_records=0,
                records=[],
                error_message="Government infrastructure feed unavailable",
                retrieved_at=retrieved_at
            )

        return AdapterFetchResult(
            provider_name=self.provider_name,
            category=self.category,
            is_available=True,
            total_records=len(records),
            records=records,
            error_message=None,
            retrieved_at=retrieved_at
        )
