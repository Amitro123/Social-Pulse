from src.analyzers.models import (
    FieldSentiment,
    AnalyzedItem,
    AggregatedStats,
    Campaign,
)
import pytest

def test_field_sentiment_validation():
    """Test that FieldSentiment validates correctly"""
    fs = FieldSentiment(
        field="ad_quality",
        sentiment="positive",
        confidence=0.85,
        quote="great ads",
        reasoning="user likes them"
    )
    assert fs.sentiment in ["positive", "negative", "neutral", "mixed"]
    assert 0 <= fs.confidence <= 1.0

def test_invalid_sentiment():
    """Test that invalid sentiment raises error"""
    with pytest.raises(ValueError):
        FieldSentiment(
            field="ad_quality",
            sentiment="invalid",  # ❌ Should fail
            confidence=0.85,
            quote="test",
            reasoning="test"
        )


def test_analyzed_item_backward_compatibility():
    """Legacy fields should still work and populate id from item_id."""
    ai = AnalyzedItem(
        item_id="legacy_1",
        entity="Taboola",
        overall_sentiment="neutral",
        field_sentiments=[
            FieldSentiment(
                field="ad_quality",
                sentiment="neutral",
                confidence=0.5,
                quote="ok",
                reasoning="n/a",
            )
        ],
        raw_text="some text",
    )
    assert ai.id == "legacy_1"
    assert ai.response_status == "pending"
    assert ai.actionable is False


def test_analyzed_item_new_fields_validation():
    """Validate bounds for new fields like rating and sentiment_score."""
    ok = AnalyzedItem(
        id="ok_1",
        sentiment="positive",
        sentiment_score=0.7,
        rating=5,
        topics=["pricing", "ad_quality"],
        category="review",
        confidence=0.9,
        actionable=True,
        response_status="pending",
    )
    assert ok.rating == 5 and -1.0 <= ok.sentiment_score <= 1.0

    with pytest.raises(ValueError):
        AnalyzedItem(id="bad_score", sentiment_score=1.5)

    with pytest.raises(ValueError):
        AnalyzedItem(id="bad_rating", rating=6)


def test_aggregated_stats_and_campaign_models():
    """Ensure AggregatedStats and Campaign accept valid payloads and defaults."""
    stats = AggregatedStats(
        total_mentions=10,
        date_range={"start_date": "2025-11-01T00:00:00Z", "end_date": "2025-11-07T00:00:00Z"},
        sentiment_breakdown={"positive": 5, "neutral": 3, "negative": 2},
        average_sentiment_score=0.2,
        average_rating=4.0,
        sentiment_trend=[{"date": "2025-11-01", "score": 0.1}],
        hot_topics=[{"topic": "ad_quality", "count": 3, "avg_sentiment": -0.2}],
        action_required_count=2,
        response_stats={"replied": 1, "pending": 1, "in_campaign": 0},
    )
    assert stats.total_mentions == 10
    assert isinstance(stats.sentiment_trend, list)

    camp = Campaign(
        id="cmp1",
        name="Improve Ad Experience",
        created_at="2025-11-01T12:00:00Z",
        theme="Ad Intrusiveness",
        target_audience="Publishers",
        message="We are reducing ad density and improving placements.",
        channels=["email", "linkedin"],
        related_items=["legacy_1", "ok_1"],
    )
    assert camp.status == "draft"
