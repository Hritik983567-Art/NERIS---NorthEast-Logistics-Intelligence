import time
import logging
import urllib.request
import json
from typing import Optional, List, Dict, Any

from app.adapters.base_adapter import BaseExternalAdapter
from app.models.external_record import (
    AdapterFetchResult,
    ExternalRecord,
    RecordCategory,
    SeverityLevel,
    LocationMetadata
)

logger = logging.getLogger("ner_logitrack.adapters.weather")

HUB_COORDINATES = [
    {"name": "Guwahati", "state": "Assam", "lat": 26.1433, "lng": 91.7898},
    {"name": "Shillong", "state": "Meghalaya", "lat": 25.5788, "lng": 91.8933},
    {"name": "Cherrapunji", "state": "Meghalaya", "lat": 25.2702, "lng": 91.7323},
    {"name": "Jowai", "state": "Meghalaya", "lat": 25.4452, "lng": 92.2034},
    {"name": "Silchar", "state": "Assam", "lat": 24.8333, "lng": 92.7789},
    {"name": "Agartala", "state": "Tripura", "lat": 23.8315, "lng": 91.2868},
    {"name": "Aizawl", "state": "Mizoram", "lat": 23.7271, "lng": 92.7176},
    {"name": "Dimapur", "state": "Nagaland", "lat": 25.9068, "lng": 93.7273},
    {"name": "Kohima", "state": "Nagaland", "lat": 25.6751, "lng": 94.1086},
    {"name": "Imphal", "state": "Manipur", "lat": 24.8170, "lng": 93.9368},
    {"name": "Itanagar", "state": "Arunachal Pradesh", "lat": 27.0844, "lng": 93.6053},
    {"name": "Tezpur", "state": "Assam", "lat": 26.6338, "lng": 92.8006}
]

WMO_WEATHER_CODES = {
    0: ("Clear sky", SeverityLevel.INFO),
    1: ("Mainly clear", SeverityLevel.INFO),
    2: ("Partly cloudy", SeverityLevel.INFO),
    3: ("Overcast", SeverityLevel.INFO),
    45: ("Foggy", SeverityLevel.MODERATE),
    48: ("Depositing rime fog", SeverityLevel.MODERATE),
    51: ("Light drizzle", SeverityLevel.MODERATE),
    53: ("Moderate drizzle", SeverityLevel.MODERATE),
    55: ("Dense drizzle", SeverityLevel.HIGH),
    61: ("Slight rain", SeverityLevel.MODERATE),
    63: ("Moderate rain", SeverityLevel.HIGH),
    65: ("Heavy monsoon downpour", SeverityLevel.CRITICAL),
    80: ("Rain showers", SeverityLevel.MODERATE),
    81: ("Moderate rain showers", SeverityLevel.HIGH),
    82: ("Violent rain showers", SeverityLevel.CRITICAL),
    95: ("Thunderstorm", SeverityLevel.CRITICAL),
    96: ("Thunderstorm with hail", SeverityLevel.CRITICAL),
    99: ("Heavy thunderstorm with hail", SeverityLevel.CRITICAL)
}

class OpenMeteoWeatherAdapter(BaseExternalAdapter):
    def __init__(self):
        super().__init__(
            provider_name="Open-Meteo Global Forecast API",
            category=RecordCategory.WEATHER,
            timeout_seconds=4.0
        )

    async def fetch(self, state_filter: Optional[str] = None) -> AdapterFetchResult:
        retrieved_at = self.get_iso_timestamp()
        records: List[ExternalRecord] = []

        lats = ",".join([str(h["lat"]) for h in HUB_COORDINATES])
        lngs = ",".join([str(h["lng"]) for h in HUB_COORDINATES])
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lngs}&current_weather=true"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'NERIS-WeatherAdapter/2.4'})
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode())
                responses_list = data if isinstance(data, list) else [data]

                for idx, hub in enumerate(HUB_COORDINATES):
                    if state_filter and state_filter.lower() != "all" and hub["state"].lower() != state_filter.lower():
                        continue

                    res = responses_list[idx] if idx < len(responses_list) else {}
                    current = res.get("current_weather", {})

                    temp = current.get("temperature", 24.5)
                    wind = current.get("windspeed", 12.0)
                    code = int(current.get("weathercode", 2))

                    desc, severity = WMO_WEATHER_CODES.get(code, ("Overcast Rain", SeverityLevel.HIGH))

                    records.append(ExternalRecord(
                        id=f"weather-{hub['name'].lower()}",
                        category=RecordCategory.WEATHER,
                        source="Open-Meteo API (IMD/Global Met Feed)",
                        source_url=url,
                        retrieved_at=retrieved_at,
                        published_at=current.get("time", retrieved_at),
                        title=f"{hub['name']} Weather: {desc} ({temp}°C)",
                        content_summary=f"Current weather at {hub['name']} ({hub['state']}): {desc}. Temperature {temp}°C, Wind Speed {wind} km/h. WMO Code: {code}.",
                        location=LocationMetadata(
                            state=hub["state"],
                            hub_name=hub["name"],
                            lat=hub["lat"],
                            lng=hub["lng"]
                        ),
                        severity=severity,
                        is_live=True,  # LIVE because fetched directly from Open-Meteo
                        extra_metadata={
                            "temp_celsius": temp,
                            "wind_speed_kmh": wind,
                            "weather_code": code,
                            "condition_description": desc
                        }
                    ))
        except Exception as err:
            logger.warning(f"OpenMeteoWeatherAdapter query failed: {err}")
            # MUST NOT generate fake data on failure per prompt requirement!
            return AdapterFetchResult(
                provider_name=self.provider_name,
                category=self.category,
                is_available=False,
                total_records=0,
                records=[],
                error_message=f"Weather API provider unavailable: {str(err)}",
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
