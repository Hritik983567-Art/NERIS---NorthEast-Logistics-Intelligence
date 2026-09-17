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

logger = logging.getLogger("ner_logitrack.adapters.news")

SEARCH_TOPICS = [
    {"query": "North East India highway landslide", "default_state": "Assam"},
    {"query": "Meghalaya NH-06 blockade weather", "default_state": "Meghalaya"},
    {"query": "Assam BRO road clearance NH-27", "default_state": "Assam"},
    {"query": "Manipur Imphal NH-02 traffic advisory", "default_state": "Manipur"},
    {"query": "Mizoram NH-54 Aizawl weather alert", "default_state": "Mizoram"},
    {"query": "Tripura Agartala highway infrastructure", "default_state": "Tripura"},
    {"query": "Sikkim Teesta highway landslide", "default_state": "Sikkim"},
    {"query": "Arunachal Pradesh border road BRO", "default_state": "Arunachal Pradesh"}
]

STATE_KEYWORDS = {
    "Assam": ["assam", "guwahati", "silchar", "tezpur", "barak"],
    "Meghalaya": ["meghalaya", "shillong", "cherrapunji", "jowai", "khasi", "jaintia"],
    "Manipur": ["manipur", "imphal", "jiribam"],
    "Mizoram": ["mizoram", "aizawl", "kolasib"],
    "Tripura": ["tripura", "agartala", "dharmanagar"],
    "Nagaland": ["nagaland", "kohima", "dimapur"],
    "Arunachal Pradesh": ["arunachal", "itanagar", "pasighat", "tawang"],
    "Sikkim": ["sikkim", "gangtok", "namchi", "teesta"]
}

class GoogleNewsRSSAdapter(BaseExternalAdapter):
    def __init__(self):
        super().__init__(
            provider_name="Google News Regional RSS Engine",
            category=RecordCategory.NEWS,
            timeout_seconds=8.0
        )

    def _determine_state(self, text: str, default_state: str) -> str:
        text_lower = text.lower()
        for state_name, keywords in STATE_KEYWORDS.items():
            if any(k in text_lower for k in keywords):
                return state_name
        return default_state

    def _determine_severity(self, text: str) -> SeverityLevel:
        text_lower = text.lower()
        if any(w in text_lower for w in ["landslide", "blocked", "closed", "cloudburst", "floods", "critical", "killed", "warning"]):
            return SeverityLevel.CRITICAL
        elif any(w in text_lower for w in ["advisory", "traffic", "heavy rain", "delay", "reroute", "alert"]):
            return SeverityLevel.HIGH
        elif any(w in text_lower for w in ["bro", "repair", "construction", "maintenance"]):
            return SeverityLevel.MODERATE
        return SeverityLevel.INFO

    def _fetch_topic_records(self, topic: Dict[str, str], retrieved_at: str, state_filter: Optional[str]) -> Tuple[List[ExternalRecord], bool]:
        query_str = topic["query"]
        encoded_query = urllib.parse.quote(query_str)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        topic_records: List[ExternalRecord] = []
        is_error = False

        try:
            req = urllib.request.Request(
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NERIS-NewsAdapter/2.4'}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)

                for item in root.findall('.//item')[:3]:
                    raw_title = item.findtext('title', 'North East Logistics Update')
                    parts = raw_title.rsplit(' - ', 1)
                    clean_title = parts[0].strip()
                    source_node = item.find('source')
                    if source_node is not None and source_node.text and source_node.text.strip():
                        publisher_name = source_node.text.strip()

                    link = item.findtext('link') or rss_url
                    pub_date = item.findtext('pubDate', retrieved_at)
                    description_raw = item.findtext('description', clean_title)
                    clean_summary = re.sub('<[^<]+?>', '', description_raw).strip()
                    if len(clean_summary) > 240:
                        clean_summary = clean_summary[:237] + "..."

                    inferred_state = self._determine_state(clean_title + " " + clean_summary, topic["default_state"])
                    severity = self._determine_severity(clean_title + " " + clean_summary)

                    if state_filter and state_filter.lower() != "all" and inferred_state.lower() != state_filter.lower():
                        continue

                    topic_records.append(ExternalRecord(
                        id=f"news-{abs(hash(clean_title))}",
                        category=RecordCategory.NEWS,
                        source=publisher_name,
                        source_url=link,
                        retrieved_at=retrieved_at,
                        published_at=pub_date,
                        title=clean_title,
                        content_summary=clean_summary if clean_summary else clean_title,
                        location=LocationMetadata(state=inferred_state),
                        severity=severity,
                        is_live=True,
                        extra_metadata={"query_topic": query_str}
                    ))
        except Exception as err:
            is_error = True
            logger.warning(f"GoogleNewsRSSAdapter query error for '{query_str}': {err}")

        return topic_records, is_error

    async def fetch(self, state_filter: Optional[str] = None) -> AdapterFetchResult:
        retrieved_at = self.get_iso_timestamp()
        records: List[ExternalRecord] = []
        seen_titles = set()

        tasks = [asyncio.to_thread(self._fetch_topic_records, topic, retrieved_at, state_filter) for topic in SEARCH_TOPICS]
        results = await asyncio.gather(*tasks)

        fetch_errors = 0
        for topic_records, is_err in results:
            if is_err:
                fetch_errors += 1
            for rec in topic_records:
                if rec.title not in seen_titles:
                    seen_titles.add(rec.title)
                    records.append(rec)

        if fetch_errors == len(SEARCH_TOPICS) and len(records) == 0:
            return AdapterFetchResult(
                provider_name=self.provider_name,
                category=self.category,
                is_available=False,
                total_records=0,
                records=[],
                error_message="External news RSS feed unavailable or rate-limited",
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
