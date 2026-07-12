# Atlas Sprint 3 Report - News + Catalyst Engine

## Objective

Add the first source-aware News + Catalyst layer to Atlas so daily recommendations are no longer based only on market regime, chart context, trade plan and portfolio fit. Sprint 3 remains offline-first and deterministic.

## Implemented

- Normalized `NewsItem` model.
- Normalized `CatalystEvent` model.
- Normalized `CatalystContext` model.
- `CsvSampleNewsProvider` for offline sample news.
- `CsvSampleNewsProvider.get_events_for_symbol()` for sample catalyst events.
- Future live-provider placeholder for Marketaux/NewsAPI/FMP-style adapters.
- `CatalystEngine` with deterministic scoring based on:
  - average sentiment,
  - average relevance,
  - average impact,
  - positive/negative news balance,
  - explicit risk flags,
  - upcoming/recent events.
- Catalyst factor integrated into Atlas Score via `catalyst_ai`.
- AI narrative upgraded with source-aware catalyst context.
- Recommendation Back-Book now stores catalyst evidence.
- Daily briefing includes market catalyst context.
- Streamlit UI updates:
  - main app,
  - Mission Control,
  - Daily Candidates,
  - Screener/Search,
  - new Catalyst Engine page.
- Documentation updates:
  - `docs/data_sources.md`,
  - `docs/news_catalysts.md`,
  - README and changelog.
- Tests for news provider, event provider, catalyst engine and recommendation integration.

## Files added or materially changed

- `atlas_core/models.py`
- `atlas_core/providers/news_provider.py`
- `atlas_core/engines/catalyst_engine.py`
- `atlas_core/engines/ai_narrative_engine.py`
- `atlas_core/engines/journal_engine.py`
- `atlas_core/orchestrator.py`
- `data/samples/news_items.csv`
- `data/samples/events.csv`
- `pages/10_Catalyst_Engine.py`
- `tests/test_catalyst_engine.py`
- `docs/news_catalysts.md`

## Test result

```text
15 passed
```

## Safety boundaries

Still not included:

- no broker integration,
- no automatic order execution,
- no live API keys,
- no real-time dependency,
- no autonomous trading,
- no ungrounded AI claims.

## Known limitations

- News and events are deterministic sample data.
- Sentiment/relevance/impact values are sample inputs, not provider-derived live analytics.
- The catalyst score is an explainable MVP heuristic, not a validated alpha model.
- Live providers still require caching, request throttling and mocked tests before activation.

## Recommended Sprint 4

**Fundamentals + Identifier Search Engine**

Suggested scope:

- Fundamentals provider interface.
- CSV sample fundamentals provider.
- Prepared FMP/Alpha Vantage fundamentals adapters.
- Quality metrics: margin, revenue growth, EPS growth, debt, ROE/ROIC, free cash flow.
- Identifier provider interface.
- Search by ticker, name, ISIN and WKN-like mappings.
- Fundamentals factor replaces simple sample hint.
- Screener page becomes more powerful.
- Tests for fundamentals and identifier resolution.
