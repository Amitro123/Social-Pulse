
import pytest
from unittest.mock import Mock, patch
from src.collectors.google_search import GoogleSearchCollector
from src.analyzers.models import RawItem

@pytest.fixture
def mock_response():
    return {
        "organic_results": [
            {
                "title": "Taboola Review",
                "snippet": "Great platform for ads.",
                "link": "https://example.com/review",
                "source": "TechReview"
            }
        ]
    }

def test_google_search_collector(mock_response):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        collector = GoogleSearchCollector()
        items = collector.collect(keywords=["Taboola"], limit=1)
        
        assert len(items) == 1
        assert items[0].platform == "google_search"
        assert "Taboola" in items[0].entity_mentioned
        assert str(items[0].url) == "https://example.com/review"
