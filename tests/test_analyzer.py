from src.analyzers.llm_analyzer import LLMAnalyzer
from src.analyzers.models import RawItem, AnalyzedItem
from datetime import datetime

def test_llm_analyzer_mock(monkeypatch):
    analyzer = LLMAnalyzer()

    def fake_single(self, item: RawItem):
        return AnalyzedItem(
            id=item.id,
            text=item.text,
            url=str(item.url),
            timestamp=item.timestamp,
            platform=item.platform,
            entity_mentioned=item.entity_mentioned,
            author=item.author,
            sentiment="positive",
            sentiment_score=0.7,
            topics=["pricing"],
            category="review",
            actionable=False,
            response_status="ignored",
        )

    monkeypatch.setattr(LLMAnalyzer, "_analyze_single", fake_single)

    items = [RawItem(id="1", platform="google_search", entity_mentioned=["Taboola"], text="text", author="u", timestamp=datetime.utcnow(), url="https://x.com")]
    analyzed = analyzer.analyze(items, delay=0.0)
    assert analyzed[0].sentiment == "positive"
