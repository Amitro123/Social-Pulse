from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from api.main import app
from src.analyzers.models import AnalyzedItem, RawItem
from datetime import datetime

client = TestClient(app)

import os

def test_api_stats_mocked():
    """Test /api/stats with mocked collector and analyzer"""
    # Patch where it is imported in the router
    with patch("api.routes.stats.GoogleSearchCollector") as MockCollector, \
         patch("api.routes.stats.LLMAnalyzer") as MockAnalyzer:

        # Mock Collector
        mock_collector_instance = MagicMock()
        MockCollector.return_value = mock_collector_instance
        mock_collector_instance.collect.return_value = [
            RawItem(
                id="1", platform="google_search", entity_mentioned=["Taboola"],
                text="Great stuff", author="user", timestamp=datetime.now(), url="http://x.com"
            )
        ]

        # Mock Analyzer
        mock_analyzer_instance = MagicMock()
        MockAnalyzer.return_value = mock_analyzer_instance
        analyzed_item = AnalyzedItem(
            id="1",
            text="Great stuff",
            url="http://x.com",
            timestamp=datetime.now(),
            platform="google_search",
            entity_mentioned=["Taboola"],
            author="user",
            sentiment="positive",
            sentiment_score=0.9,
            topics=["quality"],
            category="praise",
            key_insight="Good",
            summary="Good",
            confidence=1.0,
            actionable=False
        )
        mock_analyzer_instance.analyze.return_value = [analyzed_item]

        # Call API
        response = client.get("/api/stats?entity=Taboola&force_refresh=true&use_db=false")

        assert response.status_code == 200
        data = response.json()
        assert data["total_mentions"] == 1
        assert data["sentiment_breakdown"]["positive"] == 1

def test_api_mentions_mocked():
    # Patch where it is imported in the router
    with patch("api.routes.mentions.GoogleSearchCollector") as MockCollector, \
         patch("api.routes.mentions.LLMAnalyzer") as MockAnalyzer:

        mock_collector_instance = MockCollector.return_value
        mock_collector_instance.collect.return_value = []

        mock_analyzer_instance = MockAnalyzer.return_value
        mock_analyzer_instance.analyze.return_value = []

        response = client.get("/api/mentions?entity=Taboola")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
