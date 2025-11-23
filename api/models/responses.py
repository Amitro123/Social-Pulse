from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    version: str

class CollectRequest(BaseModel):
    entity: str = Field(default="Taboola")
    days: int = Field(default=30, ge=1, le=365)
    limit: int = Field(default=20, ge=1, le=200)

class CollectResponse(BaseModel):
    status: str
    total_mentions: int
    analyzed_count: int
    message: Optional[str] = None
    job_id: Optional[str] = None

# Pass-through models shaped like existing analyzer outputs
class AnalyzedItemModel(BaseModel):
    id: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[datetime] = None
    platform: Optional[str] = None
    entity_mentioned: Optional[List[str]] = None
    author: Optional[str] = None

    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    rating: Optional[int] = None
    topics: List[str] = []
    category: Optional[str] = None
    key_insight: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    actionable: Optional[bool] = None

    response_status: Optional[str] = None
    response_draft: Optional[str] = None
    assigned_to: Optional[str] = None

class StatsResponse(BaseModel):
    total_mentions: int
    date_range: Dict[str, Any]
    sentiment_breakdown: Dict[str, int]
    sentiment_percentages: Dict[str, float]
    average_sentiment_score: float
    average_rating: Optional[float]
    sentiment_trend: List[Dict[str, Any]]
    hot_topics: List[Dict[str, Any]]
    action_required_count: int
    action_required_items: List[Dict[str, Any]]
    response_stats: Dict[str, int]
    category_breakdown: Dict[str, int]
    platform_breakdown: Dict[str, int]
