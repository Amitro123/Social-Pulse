import os
import time
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database import db


def _seed_item(entity: str, *, id_: str, text: str, platform: str = "google_search", author: str = "demo",
               sentiment: str = "positive", sentiment_score: float = 0.5, topics: list[str] | None = None,
               category: str = "review", response_status: str = "pending", actionable: bool = False) -> None:
    item = type("AI", (), {})()
    item.id = id_
    item.text = text
    item.url = f"https://example.com/{id_}"
    item.platform = platform
    item.author = author
    item.sentiment = sentiment
    item.sentiment_score = sentiment_score
    item.rating = None
    item.topics = topics or ["general"]
    item.category = category
    item.key_insight = ""
    item.summary = text[:60]
    item.confidence = 0.9
    item.actionable = actionable
    item.response_status = response_status
    item.response_draft = None
    item.timestamp = datetime.now(timezone.utc)
    db.save_items([item], entity)


@pytest.fixture()
def fresh_db(tmp_path):
    # Point the global db to a fresh sqlite file
    db.db_path = str(tmp_path / "integration.db")
    db.init_db()
    yield


def test_end_to_end_flows_persist(fresh_db, capsys):
    client = TestClient(app)

    # Optionally seed Realize via endpoint
    r = client.post("/api/seed/realize")
    assert r.status_code == 200

    # Seed Taboola directly (no external calls)
    _seed_item("Taboola", id_="taboola_seed", text="Taboola ads discussion - mixed feedback", sentiment="neutral")

    # 1) Fetch latest mentions (DB fast path) and validate entities and timestamps
    rt = client.get("/api/mentions", params={"entity": "Taboola", "use_db": True, "days": 30, "limit": 50})
    rr = client.get("/api/mentions", params={"entity": "Realize", "use_db": True, "days": 30, "limit": 50})
    assert rt.status_code == 200 and rr.status_code == 200
    taboola_mentions = rt.json()
    realize_mentions = rr.json()
    assert any(
        "Taboola" in m.get("entity_mentioned", [])
        for m in taboola_mentions
    ), "Taboola not present"

    assert any(
        "Realize" in m.get("entity_mentioned", [])
        for m in realize_mentions
    ), "Realize not present"


    # timestamps should be present and parseable
    for m in taboola_mentions + realize_mentions:
        if m.get("timestamp"):
            datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))

    # 2) Create replies (AI + manual) and verify response_status updated to 'sent'
    first_id = taboola_mentions[0]["id"]
    r1 = client.post(f"/api/mentions/{first_id}/reply", json={"by": "AI", "content": "AI thanks"})
    assert r1.status_code == 200
    r2 = client.post(f"/api/mentions/{first_id}/reply", json={"by": "Taboola Employee", "content": "We are on it"})
    assert r2.status_code == 200

    # Re-fetch and verify status
    r = client.get("/api/mentions", params={"entity": "Taboola", "use_db": True, "days": 30, "limit": 50})
    assert r.status_code == 200
    mentions2 = r.json()
    m0 = next(m for m in mentions2 if m["id"] == first_id)
    assert m0.get("response_status") == "sent"

    # Replies list should persist
    r = client.get(f"/api/mentions/{first_id}/replies")
    assert r.status_code == 200
    assert len(r.json().get("replies", [])) >= 2

    # 3) Create a campaign and confirm it is listed
    r = client.post("/api/campaigns", json={
        "topic": "Ad Intrusiveness",
        "summary": "AI proposal initiated",
        "sentiment": "negative",
        "trigger_count": 3,
    })
    assert r.status_code == 200
    r = client.get("/api/campaigns")
    assert r.status_code == 200
    assert any(c.get("topic") == "Ad Intrusiveness" for c in r.json())

    # 4) Entity filtering
    r = client.get("/api/mentions", params={"entity": "Taboola", "use_db": True})
    assert r.status_code == 200
    assert all("Taboola" in m.get("entity_mentioned", []) for m in r.json())
    r = client.get("/api/mentions", params={"entity": "Realize", "use_db": True})
    assert r.status_code == 200
    assert all("Realize" in m.get("entity_mentioned", []) for m in r.json())

    # 5) Persistence across reload (new client simulates reload)
    client = TestClient(app)
    r = client.get("/api/campaigns")
    assert r.status_code == 200
    assert any(c.get("topic") == "Ad Intrusiveness" for c in r.json())
    r = client.get("/api/mentions", params={"entity": "Taboola", "use_db": True, "days": 30, "limit": 50})
    assert r.status_code == 200
    mentions3 = r.json()
    m0 = next(m for m in mentions3 if m["id"] == first_id)
    assert m0.get("response_status") == "sent"

    print("PASS: All integration checks passed")
    captured = capsys.readouterr()
    assert "PASS" in captured.out
