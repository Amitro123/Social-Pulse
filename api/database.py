import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Iterable
from contextlib import contextmanager


class Database:
    """SQLite database for persisting analyzed items"""

    def __init__(self, db_path: str = "social_pulse.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyzed_items (
                    id TEXT PRIMARY KEY,
                    entity TEXT NOT NULL,
                    text TEXT,
                    url TEXT,
                    platform TEXT,
                    author TEXT,
                    sentiment TEXT,
                    sentiment_score REAL,
                    rating INTEGER,
                    topics TEXT,
                    category TEXT,
                    key_insight TEXT,
                    summary TEXT,
                    confidence REAL,
                    actionable BOOLEAN,
                    response_status TEXT,
                    response_draft TEXT,
                    timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_entity_timestamp 
                ON analyzed_items(entity, timestamp DESC)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sentiment 
                ON analyzed_items(entity, sentiment)
                """
            )

            # Campaigns table (simple)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    summary TEXT,
                    sentiment TEXT,
                    trigger_count INTEGER
                )
                """
            )

            # Replies table (per mention)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS replies (
                    id TEXT PRIMARY KEY,
                    mention_id TEXT NOT NULL,
                    by TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved INTEGER DEFAULT 1,
                    FOREIGN KEY (mention_id) REFERENCES analyzed_items(id)
                )
                """
            )

            conn.commit()

    def save_items(self, items: Iterable[Any], entity: str):
        """Save analyzed items to database"""
        with self.get_connection() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analyzed_items 
                    (id, entity, text, url, platform, author, sentiment, sentiment_score,
                     rating, topics, category, key_insight, summary, confidence, 
                     actionable, response_status, response_draft, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        getattr(item, "id", None),
                        entity,
                        getattr(item, "text", None),
                        str(getattr(item, "url", None)) if getattr(item, "url", None) is not None else None,
                        getattr(item, "platform", None),
                        getattr(item, "author", None),
                        getattr(item, "sentiment", None),
                        getattr(item, "sentiment_score", None),
                        getattr(item, "rating", None),
                        json.dumps(getattr(item, "topics", None) or []),
                        getattr(item, "category", None),
                        getattr(item, "key_insight", None),
                        getattr(item, "summary", None),
                        getattr(item, "confidence", None),
                        1 if getattr(item, "actionable", False) else 0,
                        getattr(item, "response_status", None),
                        getattr(item, "response_draft", None),
                        getattr(item, "timestamp", None).isoformat() if getattr(item, "timestamp", None) else None,
                    ),
                )
            conn.commit()

    def get_items(
        self,
        entity: str,
        days: int = 30,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get items from database with filters"""

        query = (
            """
            SELECT * FROM analyzed_items
            WHERE entity = ? 
            AND datetime(timestamp) > datetime('now', '-' || ? || ' days')
            """
        )
        params: List[Any] = [entity, days]

        if sentiment:
            query += " AND sentiment = ?"
            params.append(sentiment)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY datetime(timestamp) DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            items: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("topics"):
                    try:
                        item["topics"] = json.loads(item["topics"]) if isinstance(item["topics"], str) else item["topics"]
                    except json.JSONDecodeError:
                        item["topics"] = []
                items.append(item)
            return items

    def get_stats(self, entity: str, days: int = 30) -> Dict[str, Any]:
        """Get statistics from database (basic aggregates)"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(rating) as avg_rating,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN actionable = 1 THEN 1 ELSE 0 END) as actionable_count
                FROM analyzed_items
                WHERE entity = ?
                AND datetime(timestamp) > datetime('now', '-' || ? || ' days')
                """,
                (entity, days),
            )

            row = cursor.fetchone()
            return dict(row) if row else {}

    # --- Campaign persistence ---
    def save_campaign(self, campaign: Dict[str, Any]):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO campaigns (id, topic, created_at, summary, sentiment, trigger_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign.get("id"),
                    campaign.get("topic"),
                    campaign.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    campaign.get("summary"),
                    campaign.get("sentiment"),
                    campaign.get("trigger_count"),
                ),
            )
            conn.commit()

    def list_campaigns(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM campaigns ORDER BY datetime(created_at) DESC LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    # --- Replies persistence ---
    def save_reply(self, reply: Dict[str, Any]):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO replies (id, mention_id, by, content, created_at, resolved)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    reply.get("id"),
                    reply.get("mention_id"),
                    reply.get("by"),
                    reply.get("content"),
                    reply.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    1 if reply.get("resolved", True) else 0,
                ),
            )
            conn.commit()

    def list_replies_for_item(self, mention_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM replies WHERE mention_id = ? ORDER BY datetime(created_at) DESC
                """,
                (mention_id,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
            for r in rows:
                r["resolved"] = bool(r.get("resolved", 0))
            return rows

    def update_mention_status(self, mention_id: str, *, response_status: Optional[str] = None, actionable: Optional[bool] = None):
        with self.get_connection() as conn:
            if response_status is not None and actionable is not None:
                conn.execute(
                    "UPDATE analyzed_items SET response_status = ?, actionable = ? WHERE id = ?",
                    (response_status, 1 if actionable else 0, mention_id),
                )
            elif response_status is not None:
                conn.execute(
                    "UPDATE analyzed_items SET response_status = ? WHERE id = ?",
                    (response_status, mention_id),
                )
            elif actionable is not None:
                conn.execute(
                    "UPDATE analyzed_items SET actionable = ? WHERE id = ?",
                    (1 if actionable else 0, mention_id),
                )
            conn.commit()


# Global instance
db = Database()
