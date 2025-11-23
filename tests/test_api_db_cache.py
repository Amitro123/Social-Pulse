import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database import db


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


def seed_db_with_analyzed(entity: str = "Taboola"):
    from datetime import datetime
    item = type("AI", (), {})()
    item.id = "db1"
    item.text = "from db"
    item.url = "https://example.com/db1"
    item.platform = "google_search"
    item.author = "u"
    item.sentiment = "neutral"
    item.sentiment_score = 0.0
    item.rating = None
    item.topics = ["general"]
    item.category = "review"
    item.key_insight = ""
    item.summary = ""
    item.confidence = 0.9
    item.actionable = False
    item.response_status = "ignored"
    item.response_draft = None
    item.timestamp = datetime.utcnow()
    db.save_items([item], entity)


def test_cache_endpoints(client):
    # Info
    r = client.get("/api/cache/info")
    assert r.status_code == 200
    body = r.json()
    assert "cached_items" in body and "active_requests" in body and "ttl_minutes" in body
    # Clear
    r2 = client.delete("/api/cache")
    assert r2.status_code == 200
    assert r2.json()["status"] == "cache cleared"


def test_db_endpoints_and_mentions_fastpath(monkeypatch, client):
    # Clear DB first
    r = client.delete("/api/db/clear")
    assert r.status_code == 200

    # Seed DB directly and ensure mentions reads from DB fast path
    seed_db_with_analyzed("Taboola")
    r2 = client.get("/api/mentions?entity=Taboola&days=30&limit=10&use_db=true")
    assert r2.status_code == 200
    items = r2.json()
    assert isinstance(items, list) and len(items) >= 1
    assert any(it["id"] == "db1" for it in items)

    # DB stats endpoint
    r3 = client.get("/api/db/stats")
    assert r3.status_code == 200
    assert "total_items" in r3.json()


def test_stats_uses_db_fastpath(monkeypatch, client):
    # Ensure DB has at least one item
    r = client.delete("/api/db/clear")
    assert r.status_code == 200
    seed_db_with_analyzed("Taboola")

    # Call stats with use_db=true (default) and ensure 200
    r2 = client.get("/api/stats?entity=Taboola&days=7&limit=10")
    assert r2.status_code == 200
    body = r2.json()
    assert "total_mentions" in body


def test_collect_persists_to_db(monkeypatch, client):
    # Mock external calls to avoid network
    from src.collectors.google_search import GoogleSearchCollector
    from src.analyzers.llm_analyzer import LLMAnalyzer
    from src.analyzers.models import RawItem, AnalyzedItem
    from datetime import datetime

    def fake_collect(self, keywords, limit=20):
        return [RawItem(id="c1", platform="google_search", entity_mentioned=keywords, text="ok", author="u", timestamp=datetime.utcnow(), url="https://x.com")] 

    def fake_analyze(self, items, delay=0.0):
        return [AnalyzedItem(id="c1", text="ok", url="https://x.com", timestamp=datetime.utcnow(), platform="google_search", entity_mentioned=["Taboola"], author="u", sentiment="neutral", sentiment_score=0.0, topics=["general"], category="review", actionable=False, response_status="ignored")]

    monkeypatch.setattr(GoogleSearchCollector, "collect", fake_collect)
    monkeypatch.setattr(LLMAnalyzer, "analyze", fake_analyze)

    # Clear DB and call collect
    r = client.delete("/api/db/clear")
    assert r.status_code == 200
    r2 = client.post("/api/collect", json={"entity": "Taboola", "days": 7, "limit": 5})
    assert r2.status_code == 200

    # Now mentions should find the item from DB
    r3 = client.get("/api/mentions?entity=Taboola&days=7&limit=10")
    assert r3.status_code == 200
    items = r3.json()
    assert any(it["id"] == "c1" for it in items)
