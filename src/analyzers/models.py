from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import List, Literal, Optional
from enum import Enum

class Platform(str, Enum):
    GOOGLE_SEARCH = "google_search"
    HACKER_NEWS = "hacker_news"

class RawItem(BaseModel):
    """
    Raw data from any source before sentiment analysis.
    Normalized format for all platforms.
    """
    id: str = Field(..., description="Unique identifier: platform_id")
    platform: Literal["google_search", "linkedin", "twitter", "hackernews"] = Field(
        ..., description="Source platform"
    )
    entity_mentioned: List[Literal["Taboola", "Realize"]] = Field(
        ..., description="Which entities are mentioned"
    )
    text: str = Field(..., description="Full text content")
    author: str = Field(..., description="Username or author ID")
    timestamp: datetime = Field(..., description="When posted (ISO 8601)")
    url: HttpUrl = Field(..., description="Permalink to original content")
class FieldSentiment(BaseModel):
    """
    Sentiment for a specific aspect/field.
    """
    field: str = Field(..., description="Aspect being analyzed")
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ..., description="Sentiment classification"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    quote: str = Field(..., description="Exact text snippet supporting sentiment")
    reasoning: str | None = Field(None, description="LLM's reasoning (optional)")

class AnalyzedItem(BaseModel):
    """
    Item after sentiment analysis by LLM.
    """
    item_id: str = Field(..., description="References RawItem.id")
    entity: Literal["Taboola", "Realize"] = Field(..., description="Primary entity")
    overall_sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ..., description="Overall sentiment classification"
    )
    field_sentiments: List[FieldSentiment] = Field(
        ..., description="Field-level sentiment breakdown"
    )
    timestamp: datetime = Field(..., description="Original post timestamp")
    platform: str = Field(..., description="Source platform")
    raw_text: str = Field(..., description="Original text for reference")

class SentimentDistribution(BaseModel):
    """Statistical distribution of sentiments"""
    positive: int = Field(..., ge=0, description="Count of positive sentiments")
    neutral: int = Field(..., ge=0, description="Count of neutral sentiments")
    negative: int = Field(..., ge=0, description="Count of negative sentiments")
    mixed: int = Field(..., ge=0, description="Count of mixed sentiments")

    @property
    def total(self) -> int:
        return self.positive + self.neutral + self.negative + self.mixed

    def to_percentages(self) -> dict:
        if self.total == 0:
            return {"positive": 0, "neutral": 0, "negative": 0, "mixed": 0}
        return {
            "positive": round((self.positive / self.total) * 100, 1),
            "neutral": round((self.neutral / self.total) * 100, 1),
            "negative": round((self.negative / self.total) * 100, 1),
            "mixed": round((self.mixed / self.total) * 100, 1),
        }

class Theme(BaseModel):
    """Recurring theme identified in discussions"""
    theme: str = Field(..., description="Theme name/description")
    count: int = Field(..., ge=1, description="Number of mentions")
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        ..., description="Overall sentiment of theme"
    )
    sample_quotes: List[str] = Field(..., max_length=5, description="Representative quotes")
    related_fields: List[str] = Field(..., description="Related sentiment fields")

class AggregatedResults(BaseModel):
    """Final aggregated insights for an entity"""
    entity: Literal["Taboola", "Realize"] = Field(..., description="Entity analyzed")
    total_items: int = Field(..., ge=0, description="Total items analyzed")
    date_range: dict = Field(..., description="Start and end dates")
    sentiment_distribution: SentimentDistribution = Field(
        ..., description="Overall sentiment breakdown"
    )
    field_breakdown: dict[str, SentimentDistribution] = Field(
        ..., description="Sentiment distribution per field"
    )
    top_themes: List[Theme] = Field(
        ..., max_length=3, description="Top 3 recurring themes"
    )
    trends: dict | None = Field(None, description="Time-based trends if available")
