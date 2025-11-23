import os
import pytest

from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_env():
    os.environ["GEMINI_API_KEY"] = "fake_key"
    os.environ["SERPAPI_KEY"] = "fake_key"

@pytest.fixture(autouse=True)
def mock_genai():
    """Mock genai globally to prevent API calls during tests"""
    with patch("src.analyzers.llm_analyzer.genai") as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        # Mock ping response
        mock_model.generate_content.return_value.text = "pong"
        yield mock_genai
