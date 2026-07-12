from atlas_core.providers.live_news_provider import MarketauxNewsProvider, NewsApiProvider
from atlas_core.providers.news_provider import CsvSampleNewsProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload


class FakeHttpClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, url, params=None, headers=None):
        self.calls.append((url, params or {}))
        return FakeResponse(self.payload)


def test_marketaux_provider_normalizes_live_payload(tmp_path):
    settings = {
        "news": {"csv_path": "data/samples/news_items.csv", "events_csv_path": "data/samples/events.csv", "max_items_per_symbol": 3},
        "cache": {"base_dir": str(tmp_path / "cache"), "stale_allowed_when_provider_fails": True},
        "audit": {"fetch_log_path": str(tmp_path / "audit.jsonl")},
    }
    payload = {
        "data": [
            {
                "title": "Microsoft announces AI infrastructure expansion",
                "description": "Cloud and AI investment update.",
                "source": "UnitTestWire",
                "url": "https://example.com/msft",
                "published_at": "2026-07-05T12:00:00Z",
                "sentiment_score": 0.42,
                "match_score": 91,
                "entities": [{"symbol": "MSFT", "sentiment_score": 0.42}],
            }
        ]
    }
    provider = MarketauxNewsProvider(
        api_key="test",
        settings=settings,
        fallback_provider=CsvSampleNewsProvider(settings),
        http_client=FakeHttpClient(payload),
        live_enabled=True,
        cache=None,
        audit=None,
    )
    items = provider.get_news_for_symbol("MSFT")
    assert items
    assert items[0].symbol == "MSFT"
    assert items[0].sentiment_score > 0
    assert items[0].data_quality.provider == "marketaux"


def test_newsapi_provider_falls_back_when_disabled(tmp_path):
    settings = {
        "news": {"csv_path": "data/samples/news_items.csv", "events_csv_path": "data/samples/events.csv", "max_items_per_symbol": 3},
        "cache": {"base_dir": str(tmp_path / "cache"), "stale_allowed_when_provider_fails": True},
        "audit": {"fetch_log_path": str(tmp_path / "audit.jsonl")},
    }
    provider = NewsApiProvider(
        api_key=None,
        settings=settings,
        fallback_provider=CsvSampleNewsProvider(settings),
        http_client=FakeHttpClient({"articles": []}),
        live_enabled=False,
    )
    items = provider.get_news_for_symbol("MSFT")
    assert items  # sample fallback from existing data
    assert items[0].data_quality.level == "sample"
