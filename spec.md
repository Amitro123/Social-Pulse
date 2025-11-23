# Technical Specification - Social Pulse

**Project:** social-pulse  
**Version:** 1.0.0  
**Last Updated:** 2025-11-23

│ │ ├── themes.py # Theme extraction
│ │ └── trends.py # Time-based analysis
│ ├── ui/
│ │ ├── backend/
│ │ │ ├── init.py
│ │ │ └── api.py # FastAPI backend
│ │ └── frontend/
│ │ ├── package.json
│ │ ├── src/
│ │ │ ├── App.jsx
│ │ │ ├── components/
│ │ │ └── utils/
│ │ └── public/
│ ├── utils/
│ │ ├── init.py
│ │ ├── logger.py
│ │ └── config.py
│ └── main.py # CLI entry point
├── tests/
│ ├── init.py
│ ├── test_collectors.py
│ ├── test_analyzers.py
│ ├── test_aggregators.py
│ └── test_models.py
├── outputs/
│ ├── items.json # Raw collected data
│ ├── analyzed.json # Sentiment analysis results
│ ├── aggregates.json # Computed insights
│ └── report.md # Text summary
├── docs/
│ ├── agents.md # Architecture planning
│ ├── spec.md # This file
│ └── design.md # 1-page design doc
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml # Poetry config (optional)
├── README.md
└── LICENSE

---

## 2. Data Models (Pydantic)

### 2.1 Raw Item Model

from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import List, Literal

class RawItem(BaseModel):
"""
Raw data from any source before sentiment analysis.
Normalized format for all platforms.
"""
id: str = Field(..., description="Unique identifier: platform_id")
platform: Literal["reddit", "linkedin", "twitter", "hackernews"] = Field(
..., description="Source platform"
)
entity_mentioned: List[Literal["Taboola", "Realize"]] = Field(
..., description="Which entities are mentioned"
)
text: str = Field(..., description="Full text content")
author: str = Field(..., description="Username or author ID")
timestamp: datetime = Field(..., description="When posted (ISO 8601)")
url: HttpUrl = Field(..., description="Permalink to original content")

text
class Config:
    json_schema_extra = {
        "example": {
            "id": "reddit_abc123",
            "platform": "reddit",
            "entity_mentioned": ["Taboola"],
            "text": "Taboola ads are everywhere but they pay well...",
            "author": "user123",
            "timestamp": "2025-11-23T10:00:00Z",
            "url": "https://reddit.com/r/webdev/comments/abc123"
        }
    }

### 2.2 Field Sentiment Model

class FieldSentiment(BaseModel):
"""
Sentiment for a specific aspect/field.
This is the key differentiator - not just overall positive/negative.
"""
field: str = Field(..., description="Aspect being analyzed")
sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
..., description="Sentiment classification"
)
confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
quote: str = Field(..., description="Exact text snippet supporting sentiment")
reasoning: str | None = Field(None, description="LLM's reasoning (optional)")


class Config:
    json_schema_extra = {
        "example": {
            "field": "ad_quality",
            "sentiment": "negative",
            "confidence": 0.85,
            "quote": "ads are everywhere",
            "reasoning": "User expresses frustration with ad prevalence"
        }
    }

### 2.3 Analyzed Item Model

class AnalyzedItem(BaseModel):
"""
Item after sentiment analysis by LLM.
Contains both overall sentiment and field-level breakdown.
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

class Config:
    json_schema_extra = {
        "example": {
            "item_id": "reddit_abc123",
            "entity": "Taboola",
            "overall_sentiment": "mixed",
            "field_sentiments": [
                {
                    "field": "ad_quality",
                    "sentiment": "negative",
                    "confidence": 0.85,
                    "quote": "ads are everywhere",
                    "reasoning": "Frustration with ad prevalence"
                },
                {
                    "field": "revenue_potential",
                    "sentiment": "positive",
                    "confidence": 0.90,
                    "quote": "they pay well",
                    "reasoning": "Good monetization for publishers"
                }
            ],
            "timestamp": "2025-11-23T10:00:00Z",
            "platform": "reddit",
            "raw_text": "Taboola ads are everywhere but they pay well..."
        }
    }

### 2.4 Sentiment Distribution Model

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
    """Convert counts to percentages"""
    if self.total == 0:
        return {"positive": 0, "neutral": 0, "negative": 0, "mixed": 0}
    
    return {
        "positive": round((self.positive / self.total) * 100, 1),
        "neutral": round((self.neutral / self.total) * 100, 1),
        "negative": round((self.negative / self.total) * 100, 1),
        "mixed": round((self.mixed / self.total) * 100, 1),
    }

### 2.5 Theme Model

class Theme(BaseModel):
"""Recurring theme identified in discussions"""
theme: str = Field(..., description="Theme name/description")
count: int = Field(..., ge=1, description="Number of mentions")
sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
..., description="Overall sentiment of theme"
)
sample_quotes: List[str] = Field(..., max_length=5, description="Representative quotes")
related_fields: List[str] = Field(..., description="Related sentiment fields")

class Config:
    json_schema_extra = {
        "example": {
            "theme": "Ad Intrusiveness",
            "count": 45,
            "sentiment": "negative",
            "sample_quotes": [
                "too many ads",
                "disruptive experience",
                "annoying popups"
            ],
            "related_fields": ["ad_quality", "user_experience"]
        }
    }

### 2.6 Aggregated Results Model

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

class Config:
    json_schema_extra = {
        "example": {
            "entity": "Taboola",
            "total_items": 150,
            "date_range": {
                "start": "2025-11-16T00:00:00Z",
                "end": "2025-11-23T00:00:00Z"
            },
            "sentiment_distribution": {
                "positive": 93,
                "neutral": 30,
                "negative": 27,
                "mixed": 0
            },
            "field_breakdown": {
                "ad_quality": {"positive": 30, "negative": 120, "neutral": 0, "mixed": 0},
                "revenue_potential": {"positive": 127, "negative": 23, "neutral": 0, "mixed": 0}
            },
            "top_themes": [
                {
                    "theme": "Ad Intrusiveness",
                    "count": 45,
                    "sentiment": "negative",
                    "sample_quotes": ["too many ads", "disruptive"],
                    "related_fields": ["ad_quality"]
                }
            ]
        }
    }

---

## 3. API Specifications

### 3.1 Reddit Collector (`collectors/reddit.py`)

**Class:** `RedditCollector(BaseCollector)`

**Initialization:**
def init(
self,
client_id: str,
client_secret: str,
user_agent: str
) -> None:
"""
Initialize Reddit API client using PRAW.

Args:
    client_id: Reddit API client ID
    client_secret: Reddit API client secret
    user_agent: User agent string (format: appname/version)

Raises:
    ValueError: If credentials are invalid
    ConnectionError: If Reddit API is unreachable
"""

**Methods:**
def collect(
self,
keywords: List[str],
subreddits: List[str] = ["all"],
limit: int = 100,
time_filter: Literal["day", "week", "month", "year", "all"] = "week"
) -> List[RawItem]:
"""
Collect posts and comments mentioning keywords.

Args:
    keywords: List of keywords to search for (e.g., ["Taboola", "Realize"])
    subreddits: Which subreddits to search (default: all)
    limit: Maximum items to fetch per keyword
    time_filter: Time window for search

Returns:
    List of RawItem objects

Raises:
    APIException: If Reddit API returns error
    RateLimitException: If rate limit exceeded

Example:
    collector = RedditCollector(client_id="...", ...)
    items = collector.collect(
        keywords=["Taboola"],
        subreddits=["webdev", "SEO", "marketing"],
        limit=50,
        time_filter="week"
    )
"""
def _normalize_submission(self, submission) -> RawItem:
"""Convert PRAW Submission to RawItem"""

def _normalize_comment(self, comment) -> RawItem:
"""Convert PRAW Comment to RawItem"""

def _deduplicate(self, items: List[RawItem]) -> List[RawItem]:
"""Remove duplicate items based on ID"""


**Configuration (`.env`):**
SERPAPI_KEY=your_client_id_here

---

### 3.2 LinkedIn Collector (`collectors/linkedin.py`)

**Class:** `LinkedInCollector(BaseCollector)`

**Note:** LinkedIn doesn't have a public API for posts. This uses web scraping.

**Initialization:**
def init(self, headers: dict | None = None) -> None:
"""
Initialize web scraper for LinkedIn public posts.

Args:
    headers: Custom HTTP headers (optional)

Note:
    Only scrapes publicly available posts (no authentication)
"""

**Methods:**
def collect(
self,
keywords: List[str],
max_scroll: int = 5
) -> List[RawItem]:
"""
Scrape LinkedIn public posts mentioning keywords.

Args:
    keywords: Keywords to search
    max_scroll: Maximum scrolls (each ~10 posts)

Returns:
    List of RawItem objects

Warning:
    Web scraping may violate LinkedIn ToS. Use responsibly.
    Consider manual CSV export as alternative.
"""
def _parse_post(self, html_element) -> RawItem:
"""Parse LinkedIn post HTML to RawItem"""


---

### 3.3 Sentiment Analyzer (`analyzers/sentiment.py`)

**Class:** `SentimentAnalyzer`

**Initialization:**
def init(
self,
api_key: str,
model: str = "claude-3-5-sonnet-20241022",
max_retries: int = 3
) -> None:
"""
Initialize LLM client for sentiment analysis.

Args:
    api_key: Anthropic API key
    model: Claude model to use
    max_retries: Max retry attempts on API failure
