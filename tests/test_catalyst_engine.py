from __future__ import annotations

from atlas_core.config_loader import load_all_configs
from atlas_core.engines.catalyst_engine import CatalystEngine
from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.providers.news_provider import CsvSampleNewsProvider


def test_csv_sample_news_provider_loads_symbol_market_news_and_events():
    settings = load_all_configs()["settings"]
    provider = CsvSampleNewsProvider(settings)
    msft_news = provider.get_news_for_symbol("MSFT")
    market_news = provider.get_market_news()
    events = provider.get_events_for_symbol("MSFT")
    assert msft_news
    assert market_news
    assert events
    assert msft_news[0].symbol == "MSFT"
    assert msft_news[0].relevance_score >= 0
    assert events[0].symbol == "MSFT"


def test_catalyst_engine_builds_context_with_events():
    orch = AtlasOrchestrator()
    news = orch.news_provider.get_news_for_symbol("NVDA")
    events = orch.news_provider.get_events_for_symbol("NVDA")
    context = CatalystEngine(orch.settings).build("NVDA", news, events)
    assert context.symbol == "NVDA"
    assert context.news_count >= 1
    assert context.upcoming_events
    assert 0 <= context.score <= 100
    assert context.primary_catalyst
    assert context.reasons
    assert context.data_quality.level == "sample"


def test_recommendation_contains_catalyst_context_and_backbook():
    rec = AtlasOrchestrator().analyze_query("V")
    assert rec.catalyst_context is not None
    assert rec.catalyst_context.news_count >= 1
    assert rec.catalyst_context.upcoming_events
    assert rec.back_book_summary["catalyst"]["score"] == rec.catalyst_context.score
    assert "Catalyst context" in rec.ai_statement
