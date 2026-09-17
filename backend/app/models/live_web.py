from typing import List, Optional
from pydantic import BaseModel

class LiveNewsArticle(BaseModel):
    id: str
    title: str
    source: str
    link: str
    published_at: str
    category: str  # CRITICAL_ALERT, HIGHWAY_ADVISORY, BRO_PROJECT, INFRASTRUCTURE_UPDATE
    state: str     # assam, meghalaya, manipur, mizoram, tripura, nagaland, arunachal, sikkim, all
    summary: str
    is_live: bool = True

class LiveNewsResponse(BaseModel):
    status: str
    total_results: int
    articles: List[LiveNewsArticle]
    crawled_at: str
    source_engine: str = "Google News RSS Live Web Crawler"

class HubWeatherInfo(BaseModel):
    hub_name: str
    state: str
    latitude: float
    longitude: float
    temp_celsius: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int
    condition_category: str # CLEAR, HEAVY_RAIN, MONSOON_STORM
    condition_description: str
    updated_at: str

class LiveWeatherResponse(BaseModel):
    status: str
    hubs_weather: List[HubWeatherInfo]
    average_temp_celsius: float
    monsoon_active: bool

class LiveIncidentAlert(BaseModel):
    id: str
    title: str
    highway_name: str
    state: str
    severity: str # CRITICAL, HIGH, MODERATE
    incident_type: str # LANDSLIDE, FLOOD_BLOCKADE, BRIDGE_REPAIR, WEATHER_WARNING
    description: str
    source_url: Optional[str] = None
    reported_time: str
    is_live: bool = True
