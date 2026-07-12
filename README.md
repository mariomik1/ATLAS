# Atlas - Technical MVP

Atlas is a personal Wealth Operating System for decision support across market regime, charts, catalysts/news, fundamentals, identifier search, portfolio context, FIRE progress and recommendation back-book tracking.

This repository is the **Technical MVP block** built on Sprint 6B. It combines the remaining MVP sprints into one runnable version:

- Sprint 7: News Provider Activation
- Sprint 8: Portfolio Engine v1
- Sprint 9: FIRE Engine v1
- Sprint 10: Daily Mission Control + Journal/Back-Book v1

Atlas is decision support only. It is not investment advice, not a broker and not an autotrader. No orders are placed automatically.

## What the Technical MVP can do

- Calculate market regime from benchmark data.
- Analyze asset-level OHLCV chart context.
- Generate entry, stop-loss, take-profit and do-not-chase planning levels.
- Score fundamentals using sample or gated FMP provider data.
- Resolve securities by ticker, name, ISIN, WKN-like local aliases or provider search.
- Use sample news or gated Marketaux/NewsAPI providers with cache and audit fallback.
- Build catalyst context per symbol and market.
- Calculate portfolio exposures, cash status and advisory risk flags.
- Estimate deterministic FIRE progress and projected target year.
- Produce a Daily Mission Control briefing.
- Store recommendation snapshots in a local journal/back-book.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
python scripts/run_daily_snapshot.py
streamlit run app.py
```

## Default data mode

Atlas remains offline-safe by default:

```yaml
asset_data:
  provider: csv_sample
  live_providers_enabled: false

news:
  provider: csv_sample
  live_providers_enabled: false

fundamentals:
  provider: csv_sample
  live_providers_enabled: false

identifiers:
  provider: local_sample
  live_providers_enabled: false
```

## Optional provider modes

All live/delayed providers are config-gated and must use cache/audit wrappers. API keys belong in `.env`, never in code.

```text
FMP_API_KEY=
MARKETAUX_API_KEY=
NEWSAPI_API_KEY=
OPENFIGI_API_KEY=
ALPHAVANTAGE_API_KEY=
POLYGON_API_KEY=
```

Example Marketaux activation:

```yaml
news:
  provider: marketaux
  live_providers_enabled: true
```

Example yfinance activation:

```yaml
asset_data:
  provider: yfinance
  live_providers_enabled: true
```

Example FMP fundamentals/search activation:

```yaml
fundamentals:
  provider: fmp
  live_providers_enabled: true

identifiers:
  provider: fmp
  live_providers_enabled: true
```

## Main pages

- Mission Control
- Daily Candidates
- Screener/Search
- Back Book
- Portfolio
- Journal
- Settings
- Market Engine
- Chart Engine
- Catalyst Engine
- Fundamentals + Identifier Search
- Provider Status
- Technical MVP Status

## Safety boundaries

- Broker connections are disabled.
- Auto-trading is disabled.
- Generated entries, stops and take-profits are planning outputs only.
- Every recommendation requires manual review.
- Data quality is explicitly tracked.
- Sample and delayed/unverified data must not be treated as live facts.
- Provider data can be stale, incomplete, delayed or plan-limited.
- Fundamental context cannot override weak chart, weak market, poor CRV or bad portfolio fit.

## Current test status

```text
44 passed
```
