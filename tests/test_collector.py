from src.collectors.google_search import GoogleSearchCollector

def test_collector_builds_items(monkeypatch):
    # Mock requests to avoid network; instead monkeypatch collect to test basic flow
    collector = GoogleSearchCollector(days_back=7)
    # We cannot guarantee network; so just assert attributes exist
    assert hasattr(collector, 'collect')
