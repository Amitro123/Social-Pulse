from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from api.routes import stats as stats_routes
from api.routes import mentions as mentions_routes
from api.models.responses import HealthResponse, CollectRequest, CollectResponse
from api import config
from api.dependencies import rate_limit
from api.cache import cache_manager
from api.database import db
from src.collectors.google_search import GoogleSearchCollector
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.aggregators.stats_aggregator import StatsAggregator
from fastapi.concurrency import run_in_threadpool
import uuid

app = FastAPI(title="Social Pulse API", version=config.API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats_routes.router)
app.include_router(mentions_routes.router)

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version=config.API_VERSION)

@app.post("/api/collect", response_model=CollectResponse)
async def collect(req: CollectRequest, background_tasks: BackgroundTasks):
    """Trigger collection + analysis + aggregation. Returns results synchronously for demo, with optional background."""
    async def job(entity: str, days: int, limit: int):
        collector = GoogleSearchCollector(days_back=days)
        items = await run_in_threadpool(collector.collect, keywords=[entity], limit=limit)

        analyzer = LLMAnalyzer()
        analyzed = await run_in_threadpool(analyzer.analyze, items, delay=0.0)

        aggregator = StatsAggregator()
        stats = await run_in_threadpool(aggregator.aggregate, analyzed, days_back=days)
        return items, analyzed, stats

    job_id = str(uuid.uuid4())
    items, analyzed, stats = await job(req.entity, req.days, req.limit)
    # Cache stats for quick GET /api/stats responses
    cache_key = f"stats_{req.entity}_{req.days}_{req.limit}"
    cache_manager.set(cache_key, stats)
    # Persist analyzed items to the database
    await run_in_threadpool(db.save_items, analyzed, req.entity)

    return CollectResponse(status="completed", total_mentions=len(items), analyzed_count=len(analyzed), job_id=job_id)

@app.delete("/api/cache")
async def clear_cache(pattern: str | None = None):
    """Clear cache (all or by pattern)"""
    cache_manager.clear(pattern)
    return {"status": "cache cleared", "pattern": pattern}

@app.get("/api/cache/info")
async def cache_info():
    """Get cache statistics"""
    return {
        "cached_items": len(cache_manager.cache),
        "active_requests": len(cache_manager.active_requests),
        "ttl_minutes": cache_manager.default_ttl,
    }

@app.get("/api/db/stats")
async def database_stats():
    """Get database statistics"""
    with db.get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                COUNT(*) as total_items,
                COUNT(DISTINCT entity) as unique_entities,
                MIN(created_at) as oldest_item,
                MAX(created_at) as newest_item
            FROM analyzed_items
            """
        )
        return dict(cursor.fetchone())

@app.delete("/api/db/clear")
async def clear_database(entity: str | None = None):
    """Clear database (all or specific entity)"""
    with db.get_connection() as conn:
        if entity:
            conn.execute("DELETE FROM analyzed_items WHERE entity = ?", (entity,))
        else:
            conn.execute("DELETE FROM analyzed_items")
        conn.commit()
    return {"status": "database cleared", "entity": entity}
