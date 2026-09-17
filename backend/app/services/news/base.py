from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NewsCategory(str, Enum):
    DISASTER = "DISASTER"
    WEATHER = "WEATHER"
    ROAD_TRANSPORT = "ROAD & TRANSPORT"
    FLOOD = "FLOOD"
    LANDSLIDE = "LANDSLIDE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    GOVERNMENT_ADVISORY = "GOVERNMENT ADVISORY"
    EMERGENCY_RESPONSE = "EMERGENCY RESPONSE"
    LOGISTICS = "LOGISTICS"
    GENERAL = "GENERAL"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NERISNewsArticle(BaseModel):
    id: str = Field(..., description="Stable article identifier hash")
    title: str = Field(..., description="Article headline")
    summary: str = Field(..., description="Short descriptive summary")
    category: str = Field(NewsCategory.GENERAL.value, description="NERIS news category")
    source: str = Field(..., description="News publisher / agency source name")
    source_url: str = Field(..., description="Direct original source publication URL")
    published_at: str = Field(..., description="Original publication timestamp (ISO 8601 or formatted)")
    published_timestamp: float = Field(0.0, description="Unix timestamp for accurate date sorting")
    retrieved_at: str = Field(..., description="Backend retrieval timestamp (ISO 8601 or formatted)")
    location: str = Field("ALL NER", description="State or location region across Northeast India")
    severity: str = Field(SeverityLevel.LOW.value, description="Operational severity rating (LOW, MODERATE, HIGH, CRITICAL)")
    image_url: Optional[str] = Field(None, description="Optional contextual image URL")
    relevance_score: float = Field(0.0, description="Explainable NERIS emergency logistics relevance score")
    relevance_breakdown: Dict[str, float] = Field(default_factory=dict, description="Detailed component breakdown of relevance score")
    is_demo: bool = Field(False, description="True if demo seed data, False if live external provider article")
    verification_status: str = Field("UNVERIFIED_EXTERNAL_ARTICLE", description="Article state: UNVERIFIED_EXTERNAL_ARTICLE, AI_SUMMARY_GENERATED, UNVERIFIED_EXTERNAL_REPORT, or VERIFIED_INCIDENT")
    is_unverified: bool = Field(True, description="Always True for external news feeds — external news is never an automatic verified incident")
    ai_summary: Optional[str] = Field(None, description="Optional Bedrock/AI-generated summary stored separately")
    ai_translation: Optional[str] = Field(None, description="Optional Bedrock/AI-generated translation stored separately")
    original_language: Optional[str] = Field("en", description="Primary language code of article")
    title_native: Optional[str] = Field(None, description="Native regional language headline text")
    summary_native: Optional[str] = Field(None, description="Native regional language summary text")
    original_content: Optional[str] = Field(None, description="Preserved original raw article text or summary reference")


class BaseNewsProvider(ABC):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    async def fetch_articles(
        self,
        location_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[NERISNewsArticle]:
        """
        Fetch news articles from the provider, normalize them into NERISNewsArticle, and filter.
        """
        pass
