import pytest
from unittest.mock import MagicMock, patch
import os
from src.analyzers.llm_analyzer import LLMAnalyzer, RawItem, AnalyzedItem
from datetime import datetime
import json
from pydantic import ValidationError

class MockResponse:
    def __init__(self, text):
        self.text = text

@pytest.fixture
def raw_item():
    return RawItem(
        id="test_1",
        platform="google_search",
        entity_mentioned=["Taboola"],
        text="Test text",
        author="tester",
        timestamp=datetime.now(),
        url="http://example.com"
    )

@pytest.fixture
def mock_genai():
    with patch("src.analyzers.llm_analyzer.genai") as mock_genai:
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            # Mock the model creation and ping
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value = MockResponse("pong")
            yield mock_genai, mock_model

def test_analyze_single_retry_on_invalid_json(raw_item, mock_genai):
    """Test that analyzer retries when JSON is invalid"""
    _, mock_model = mock_genai

    # First attempt: Invalid JSON
    # Second attempt: Valid JSON
    mock_model.generate_content.side_effect = [
        MockResponse("ping"), # Init ping
        MockResponse("Not JSON"), # 1st attempt
        MockResponse("""```json
{
  "sentiment": "positive",
  "sentiment_score": 0.8,
  "rating": 5,
  "category": "praise",
  "topics": ["quality"],
  "key_insight": "Good stuff",
  "summary": "Positive review",
  "confidence": 0.9,
  "actionable": false
}
```""") # 2nd attempt
    ]

    analyzer = LLMAnalyzer()

    # We need to reset side_effect or handle the ping call.
    # The init called generate_content("ping"), consuming one side_effect if we set it before init.
    # But here we set side_effect AFTER init? No, init happens in LLMAnalyzer()

    # Let's re-set side_effect for the actual call
    mock_model.generate_content.side_effect = [
        MockResponse("Not JSON"),
        MockResponse("""```json
{
  "sentiment": "positive",
  "sentiment_score": 0.8,
  "rating": 5,
  "category": "praise",
  "topics": ["quality"],
  "key_insight": "Good stuff",
  "summary": "Positive review",
  "confidence": 0.9,
  "actionable": false
}
```""")
    ]

    result = analyzer._analyze_single(raw_item)

    assert isinstance(result, AnalyzedItem)
    assert result.sentiment == "positive"
    # call_count: 1 (init) + 2 (attempts) = 3.
    # But checking calls to ensure retried.
    assert mock_model.generate_content.call_count >= 2

def test_analyze_single_fail_on_wrong_literal_schema(raw_item, mock_genai):
    """
    Test what happens when LLM returns 'Mixed' which passes AnalysisResult (str)
    but fails AnalyzedItem (Literal).
    """
    _, mock_model = mock_genai

    # Returns 'Mixed' which is invalid for AnalyzedItem
    mock_model.generate_content.return_value = MockResponse("""
{
  "sentiment": "Mixed",
  "sentiment_score": 0.0,
  "category": "review",
  "topics": [],
  "key_insight": "mixed feelings",
  "summary": "mixed",
  "confidence": 0.5,
  "actionable": false
}
""")

    analyzer = LLMAnalyzer()

    # Expectation: It raises Exception because the validation error IS caught in the retry loop,
    # and after retries it raises a generic Exception with the error details.

    with pytest.raises(Exception) as excinfo:
        analyzer._analyze_single(raw_item)

    assert "Validation failed" in str(excinfo.value)
    # It should fail at AnalysisResult validation now
    assert "sentiment" in str(excinfo.value)
