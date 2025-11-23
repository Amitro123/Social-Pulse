from pydantic import BaseModel, HttpUrl, Field
from pydantic import field_validator, model_validator
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
    entity_mentioned: List[str] = Field(
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
    Enhanced analysis result for a single mention.

    Backward compatible with previous field-level schema by accepting legacy fields
    (e.g., item_id, overall_sentiment, field_sentiments, raw_text). New fields
    support downstream actions and campaign workflows.
    """

    # Original data (from RawItem)
    id: Optional[str] = Field(None, description="RawItem.id; auto-filled from item_id if missing")
    text: Optional[str] = Field(None, description="RawItem.text")
    url: Optional[HttpUrl] = Field(None, description="RawItem.url")
    timestamp: Optional[datetime] = Field(None, description="RawItem.timestamp")
    platform: Optional[str] = Field(None, description="RawItem.platform")
    entity_mentioned: Optional[List[str]] = Field(default=None, description="Entities mentioned in the text")
    author: Optional[str] = Field(None, description="RawItem.author")

    # LLM Analysis Results
    sentiment: Optional[Literal["positive", "neutral", "negative"]] = Field(
        default=None, description="Primary sentiment classification"
    )
    sentiment_score: Optional[float] = Field(
        default=None, ge=-1.0, le=1.0, description="Normalized sentiment score (-1 to +1)"
    )
    rating: Optional[int] = Field(
        default=None, ge=1, le=5, description="Star rating (1-5) if extractable"
    )
    topics: List[str] = Field(default_factory=list, description="Detected topics (e.g., pricing, ad_quality)")
    category: Optional[Literal["complaint", "review", "question", "praise", "feature_request"]] = Field(
        default=None, description="Content category"
    )
    key_insight: Optional[str] = Field(default=None, description="One-sentence core issue/praise")
    summary: Optional[str] = Field(default=None, description="10–15 word professional summary")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="LLM confidence")
    actionable: bool = Field(default=False, description="Whether action/response is required")

    # Action Tracking
    response_status: Literal["pending", "replied", "in_campaign", "ignored"] = Field(
        default="pending", description="Response workflow status"
    )
    response_draft: Optional[str] = Field(default=None, description="AI-generated response draft")
    assigned_to: Optional[str] = Field(default=None, description="Assignee (user/team)")

    # ---- Backward compatibility fields (legacy schema) ----
    item_id: Optional[str] = Field(default=None, description="Legacy: References RawItem.id")
    entity: Optional[Literal["Taboola", "Realize"]] = Field(default=None, description="Legacy: primary entity")
    overall_sentiment: Optional[Literal["positive", "negative", "neutral", "mixed"]] = Field(
        default=None, description="Legacy: overall sentiment classification"
    )
    field_sentiments: Optional[List["FieldSentiment"]] = Field(
        default=None, description="Legacy: field-level sentiment breakdown"
    )
    raw_text: Optional[str] = Field(default=None, description="Legacy: original text for reference")

    @model_validator(mode="after")
    def _fill_id_from_legacy(self) -> "AnalyzedItem":
        """Populate `id` from `item_id` if not provided to preserve legacy behavior."""
        if not self.id and self.item_id:
            object.__setattr__(self, "id", self.item_id)
        return self

    @field_validator("summary")
    @classmethod
    def _limit_summary(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Soft clamp: keep as-is; enforcement left to analyzer prompt
        return v.strip()

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


class AggregatedStats(BaseModel):
    """
    Aggregated metrics over a time range for monitoring and reporting.
    Designed for dashboards and campaign planning.
    """
    total_mentions: int = Field(..., ge=0, description="Total number of mentions")
    date_range: dict = Field(
        ..., description="Date range dict: {'start_date': ISO8601, 'end_date': ISO8601}"
    )
    sentiment_breakdown: dict = Field(
        default_factory=dict, description="Counts per sentiment: {positive, neutral, negative}"
    )
    average_sentiment_score: float = Field(
        ..., ge=-1.0, le=1.0, description="Average sentiment score (-1..+1)"
    )
    average_rating: Optional[float] = Field(
        default=None, ge=1, le=5, description="Average star rating (1-5) if available"
    )
    sentiment_trend: List[dict] = Field(
        default_factory=list, description="Time series: [{'date': ISO8601, 'score': float}]"
    )
    hot_topics: List[dict] = Field(
        default_factory=list, description="Top topics: [{'topic': str, 'count': int, 'avg_sentiment': float}]"
    )
    action_required_count: int = Field(
        0, ge=0, description="Number of items marked actionable"
    )
    response_stats: dict = Field(
        default_factory=dict, description="Response status counts: {'replied': int, 'pending': int, 'in_campaign': int}"
    )


class Campaign(BaseModel):
    """
    Campaign definition for orchestrating coordinated responses and messaging.
    """
    id: str = Field(..., description="Unique campaign ID")
    name: str = Field(..., description="Human-friendly campaign name")
    created_at: datetime = Field(..., description="Creation timestamp (ISO8601)")
    theme: str = Field(..., description="Primary theme/issue being addressed")
    target_audience: str = Field(..., description="Intended audience for the campaign")
    message: str = Field(..., description="Suggested messaging content")
    channels: List[str] = Field(
        default_factory=list, description='Distribution channels, e.g. ["email", "reddit", "linkedin"]'
    )
    related_items: List[str] = Field(
        default_factory=list, description="IDs of related AnalyzedItems"
    )
    status: Literal["draft", "active", "completed"] = Field(
        default="draft", description="Lifecycle status of the campaign"
    )
