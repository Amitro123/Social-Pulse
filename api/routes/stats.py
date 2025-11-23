from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from api.models.responses import StatsResponse
from api import config
from api.dependencies import rate_limit
from api.cache import cache_manager
from api.database import db
from src.collectors.google_search import GoogleSearchCollector
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.aggregators.stats_aggregator import StatsAggregator
from src.analyzers.models import AnalyzedItem
from datetime import datetime

router = APIRouter(prefix="/api", tags=["stats"])

@router.get("/stats", response_model=StatsResponse)
async def get_stats(entity: str = config.DEFAULT_ENTITY, days: int = config.DEFAULT_DAYS, limit: int = config.DEFAULT_LIMIT, force_refresh: bool = False, use_db: bool = True):
    """Return aggregated statistics for an entity over a time window with smart caching."""
    await rate_limit()

    cache_key = f"stats_{entity}_{days}_{limit}"

    # Optional: try database first for faster cold-start responses
    if use_db and not force_refresh:
        rows = db.get_items(entity, days=days, limit=limit)
        if rows:
            def row_to_item(r) -> AnalyzedItem:
                ts_raw = r.get("timestamp")
                ts: Optional[datetime]
                try:
                    ts = datetime.fromisoformat(ts_raw) if ts_raw else None
                except Exception:
                    ts = None
                return AnalyzedItem(
                    id=r.get("id"),
                    text=r.get("text"),
                    url=r.get("url"),
                    timestamp=ts,
                    platform=r.get("platform"),
                    entity_mentioned=[entity],
                    author=r.get("author"),
                    sentiment=r.get("sentiment"),
                    sentiment_score=r.get("sentiment_score") or 0.0,
                    rating=r.get("rating"),
                    topics=r.get("topics") or [],
                    category=r.get("category"),
                    key_insight=r.get("key_insight"),
                    summary=r.get("summary"),
                    confidence=r.get("confidence"),
                    actionable=bool(r.get("actionable")) if r.get("actionable") is not None else False,
                    response_status=r.get("response_status") or "pending",
                    response_draft=r.get("response_draft"),
                )
            items_from_db = [row_to_item(r) for r in rows]
            aggregator = StatsAggregator()
            stats = aggregator.aggregate(items_from_db, days_back=days)
            return stats

    async def compute_stats():
        collector = GoogleSearchCollector(days_back=days)
        items = collector.collect(keywords=[entity], limit=limit)

        analyzer = LLMAnalyzer()
        analyzed = analyzer.analyze(items, delay=0.0)

        # Persist analyzed items to DB
        db.save_items(analyzed, entity)

        aggregator = StatsAggregator()
        return aggregator.aggregate(analyzed, days_back=days)

    result = await cache_manager.get_or_compute(cache_key, compute_stats, force_refresh=force_refresh)
    return result["data"]
