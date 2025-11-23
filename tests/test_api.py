import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_stats_endpoint_mocks(monkeypatch, client):
    # Mock collector/analyzer/aggregator to avoid external calls
    from src.collectors.google_search import GoogleSearchCollector
    from src.analyzers.llm_analyzer import LLMAnalyzer
    from src.aggregators.stats_aggregator import StatsAggregator
    from src.analyzers.models import RawItem, AnalyzedItem
    from datetime import datetime

    def fake_collect(self, keywords, limit=20):
        return [RawItem(id="1", platform="google_search", entity_mentioned=["Taboola"], text="ok", author="u", timestamp=datetime.utcnow(), url="https://x.com")]

    def fake_analyze(self, items, delay=0.0):
        return [AnalyzedItem(id="1", text="ok", url="https://x.com", timestamp=datetime.utcnow(), platform="google_search", entity_mentioned=["Taboola"], author="u", sentiment="neutral", sentiment_score=0.0, topics=["general"], category="review", actionable=False, response_status="ignored")]

    def fake_agg(self, analyzed, days_back=30):
        return {
            "total_mentions": 1,
            "date_range": {"start_date": "2025-11-01T00:00:00Z", "end_date": "2025-11-07T00:00:00Z"},
            "sentiment_breakdown": {"positive": 0, "neutral": 1, "negative": 0},
            "sentiment_percentages": {"positive": 0.0, "neutral": 100.0, "negative": 0.0},
            "average_sentiment_score": 0.0,
            "average_rating": None,
            "sentiment_trend": [],
            "hot_topics": [],
            "action_required_count": 0,
            "action_required_items": [],
            "response_stats": {"pending": 0, "replied": 0, "in_campaign": 0, "ignored": 1},
            "category_breakdown": {"review": 1},
            "platform_breakdown": {"google_search": 1},
        }

    monkeypatch.setattr(GoogleSearchCollector, "collect", fake_collect)
    monkeypatch.setattr(LLMAnalyzer, "analyze", fake_analyze)
    monkeypatch.setattr(StatsAggregator, "aggregate", fake_agg)

    r = client.get("/api/stats?entity=Taboola&days=7&limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["total_mentions"] == 1


def test_mentions_list_and_get(monkeypatch, client):
    from src.collectors.google_search import GoogleSearchCollector
    from src.analyzers.llm_analyzer import LLMAnalyzer
    from src.analyzers.models import RawItem, AnalyzedItem
    from datetime import datetime

    def fake_collect(self, keywords, limit=20):
        return [RawItem(id="1", platform="google_search", entity_mentioned=["Taboola"], text="ok", author="u", timestamp=datetime.utcnow(), url="https://x.com")]

    def fake_analyze(self, items, delay=0.0):
        return [AnalyzedItem(id="1", text="ok", url="https://x.com", timestamp=datetime.utcnow(), platform="google_search", entity_mentioned=["Taboola"], author="u", sentiment="negative", sentiment_score=-0.2, topics=["ad_quality"], category="complaint", actionable=True, response_status="pending")]

    monkeypatch.setattr(GoogleSearchCollector, "collect", fake_collect)
    monkeypatch.setattr(LLMAnalyzer, "analyze", fake_analyze)

    r = client.get("/api/mentions?sentiment=negative&category=complaint")
    assert r.status_code == 200
    lst = r.json()
    assert isinstance(lst, list) and len(lst) == 1
    item_id = lst[0]["id"]

    r2 = client.get(f"/api/mentions/{item_id}")
    assert r2.status_code == 200

    r3 = client.get("/api/mentions/nonexistent")
    assert r3.status_code == 404


def test_collect_endpoint(monkeypatch, client):
    from src.collectors.google_search import GoogleSearchCollector
    from src.analyzers.llm_analyzer import LLMAnalyzer
    from src.aggregators.stats_aggregator import StatsAggregator
    from src.analyzers.models import RawItem, AnalyzedItem
    from datetime import datetime

    def fake_collect(self, keywords, limit=20):
        return [RawItem(id="1", platform="google_search", entity_mentioned=["Taboola"], text="ok", author="u", timestamp=datetime.utcnow(), url="https://x.com")]

    def fake_analyze(self, items, delay=0.0):
        return [AnalyzedItem(id="1", text="ok", url="https://x.com", timestamp=datetime.utcnow(), platform="google_search", entity_mentioned=["Taboola"], author="u", sentiment="neutral", sentiment_score=0.0, topics=["general"], category="review", actionable=False, response_status="ignored")]

    def fake_agg(self, analyzed, days_back=30):
        return {"total_mentions": 1}

    monkeypatch.setattr(GoogleSearchCollector, "collect", fake_collect)
    monkeypatch.setattr(LLMAnalyzer, "analyze", fake_analyze)
    monkeypatch.setattr(StatsAggregator, "aggregate", fake_agg)

    r = client.post("/api/collect", json={"entity": "Taboola", "days": 7, "limit": 5})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
