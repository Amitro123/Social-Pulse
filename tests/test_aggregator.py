from src.aggregators.stats_aggregator import StatsAggregator
from src.analyzers.models import AnalyzedItem
from datetime import datetime

def test_stats_aggregator_basic():
    agg = StatsAggregator()
    items = [
        AnalyzedItem(id="1", text="x", url="https://x", timestamp=datetime.utcnow(), platform="google_search", entity_mentioned=["Taboola"], author="u", sentiment="positive", sentiment_score=0.5, topics=["ad_quality"], category="review", actionable=False, response_status="ignored"),
        AnalyzedItem(id="2", text="y", url="https://y", timestamp=datetime.utcnow(), platform="google_search", entity_mentioned=["Taboola"], author="u", sentiment="negative", sentiment_score=-0.3, topics=["pricing"], category="complaint", actionable=True, response_status="pending"),
    ]
    stats = agg.aggregate(items, days_back=7)
    assert stats["total_mentions"] == 2
    assert "sentiment_breakdown" in stats
