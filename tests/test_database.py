import os
import tempfile
from datetime import datetime

from api.database import Database


class DummyItem:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_database_save_and_get_items_and_stats():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "test.db")
        db = Database(db_path=db_path)

        # No data initially
        items = db.get_items(entity="Taboola", days=30, limit=10)
        assert items == []
        stats = db.get_stats(entity="Taboola", days=30)
        assert stats.get("total", 0) == 0

        # Save one analyzed item
        now = datetime.utcnow()
        analyzed = [
            DummyItem(
                id="1",
                text="ok",
                url="https://example.com",
                platform="google_search",
                author="u",
                sentiment="positive",
                sentiment_score=0.8,
                rating=5,
                topics=["ad_quality"],
                category="praise",
                key_insight="great",
                summary="short",
                confidence=0.9,
                actionable=False,
                response_status="ignored",
                response_draft=None,
                timestamp=now,
            )
        ]

        db.save_items(analyzed, entity="Taboola")

        # Read back
        items = db.get_items(entity="Taboola", days=30, limit=10)
        assert len(items) == 1
        assert items[0]["id"] == "1"
        assert items[0]["topics"] == ["ad_quality"]

        stats = db.get_stats(entity="Taboola", days=30)
        assert stats["total"] == 1
        assert stats["positive"] == 1
        assert stats["neutral"] == 0
        assert stats["negative"] == 0
        assert round(stats["avg_sentiment"], 2) == 0.8
