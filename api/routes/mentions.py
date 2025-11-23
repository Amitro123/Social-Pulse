from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.models.responses import AnalyzedItemModel
from api import config
from api.dependencies import cache, rate_limit
from api.database import db
from src.collectors.google_search import GoogleSearchCollector
from src.analyzers.llm_analyzer import LLMAnalyzer
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/api", tags=["mentions"])

@router.get("/mentions", response_model=List[AnalyzedItemModel])
async def list_mentions(
    entity: str = config.DEFAULT_ENTITY,
    sentiment: Optional[str] = Query(default=None, pattern="^(positive|neutral|negative)$"),
    category: Optional[str] = Query(default=None, pattern="^(complaint|review|question|praise)$"),
    days: int = config.DEFAULT_DAYS,
    limit: int = 50,
    use_db: bool = False,
):
    """List analyzed mentions filtered by sentiment/category."""
    await rate_limit()
    cache_key = ("mentions", entity, sentiment, category, days, limit)
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Try database first (opt-in)
    rows = db.get_items(entity, days, sentiment, category, limit) if use_db else []
    if use_db and rows:
        def row_to_api(r: dict) -> AnalyzedItemModel:
            return AnalyzedItemModel(
                id=r.get("id"),
                text=r.get("text"),
                url=str(r.get("url")) if r.get("url") is not None else None,
                timestamp=r.get("timestamp"),
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
                assigned_to=None,
            )
        response_items = [row_to_api(r) for r in rows]
        cache.set(cache_key, response_items)
        return response_items

    collector = GoogleSearchCollector(days_back=days)
    items = await run_in_threadpool(collector.collect, keywords=[entity], limit=limit)

    analyzer = LLMAnalyzer()
    analyzed = await run_in_threadpool(analyzer.analyze, items, delay=0.0)

    # Filter
    def ok(a):
        if sentiment and a.sentiment != sentiment:
            return False
        if category and a.category != category:
            return False
        return True

    filtered = [a for a in analyzed if ok(a)]

    # Persist to DB
    await run_in_threadpool(db.save_items, filtered, entity)

    # Convert to API response model explicitly to ensure primitives (str URL)
    def to_api(a):
        return AnalyzedItemModel(
            id=a.id,
            text=a.text,
            url=str(a.url) if a.url is not None else None,
            timestamp=a.timestamp,
            platform=a.platform,
            entity_mentioned=a.entity_mentioned,
            author=a.author,
            sentiment=a.sentiment,
            sentiment_score=a.sentiment_score,
            rating=a.rating,
            topics=a.topics or [],
            category=a.category,
            key_insight=a.key_insight,
            summary=a.summary,
            confidence=a.confidence,
            actionable=a.actionable,
            response_status=a.response_status,
            response_draft=a.response_draft,
            assigned_to=a.assigned_to,
        )

    response_items = [to_api(a) for a in filtered]
    cache.set(cache_key, response_items)
    return response_items

@router.get("/mentions/{item_id}", response_model=AnalyzedItemModel)
async def get_mention(item_id: str, days: int = config.DEFAULT_DAYS, entity: str = config.DEFAULT_ENTITY, use_db: bool = False):
    await rate_limit()

    # Try database first (opt-in) (fetch recent items and search by id)
    rows = db.get_items(entity, days, limit=200) if use_db else []
    for r in rows:
        if r.get("id") == item_id:
            return AnalyzedItemModel(
                id=r.get("id"),
                text=r.get("text"),
                url=str(r.get("url")) if r.get("url") is not None else None,
                timestamp=r.get("timestamp"),
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
                assigned_to=None,
            )

    collector = GoogleSearchCollector(days_back=days)
    items = await run_in_threadpool(collector.collect, keywords=[entity], limit=100)

    analyzer = LLMAnalyzer()
    analyzed = await run_in_threadpool(analyzer.analyze, items, delay=0.0)

    for a in analyzed:
        if a.id == item_id:
            # Save to DB for persistence
            await run_in_threadpool(db.save_items, [a], entity)
            return AnalyzedItemModel(
                id=a.id,
                text=a.text,
                url=str(a.url) if a.url is not None else None,
                timestamp=a.timestamp,
                platform=a.platform,
                entity_mentioned=a.entity_mentioned,
                author=a.author,
                sentiment=a.sentiment,
                sentiment_score=a.sentiment_score,
                rating=a.rating,
                topics=a.topics or [],
                category=a.category,
                key_insight=a.key_insight,
                summary=a.summary,
                confidence=a.confidence,
                actionable=a.actionable,
                response_status=a.response_status,
                response_draft=a.response_draft,
                assigned_to=a.assigned_to,
            )
    raise HTTPException(status_code=404, detail="Mention not found")
