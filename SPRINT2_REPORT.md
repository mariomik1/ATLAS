# Atlas Sprint 2 Report

## Sprint name

Chart Engine + Asset Provider Layer

## Status

Implemented and tested.

```text
12 passed
```

## Goal

Upgrade Atlas from static asset hints to asset-level OHLCV-based technical analysis while preserving the offline-first and no-autotrading safety model.

## Delivered

### Provider layer

- Added normalized `OhlcvBar` model.
- Added `CsvAssetHistoryProvider` for offline sample OHLCV data.
- Added `YFinanceAssetHistoryProvider` skeleton for optional delayed/live-compatible future use.
- Added `data/samples/asset_ohlcv.csv` with deterministic sample history for MSFT, NVDA, V, CRWD and XLE.

### Chart Engine

Implemented asset-level chart context:

- EMA20
- EMA50
- SMA200
- RSI14
- ATR14 / ATR %
- 20-day return
- 60-day return
- distance to EMA20 / EMA50 / SMA200
- swing high / low
- support and resistance levels
- volume ratio
- trend status
- market structure
- setup classification
- chart score
- chart reasons and risks
- data quality flags

### Strategy Engine

Strategy assignment is now chart-context aware:

- momentum pullback
- breakout
- trend continuation
- mean reversion
- core investment
- defensive allocation
- watchlist only

### Trade Plan Engine

Trade plans now use chart-anchored levels instead of pure ATR proxy levels:

- entry low
- entry high
- do-not-chase-above
- stop-loss
- take-profit 1
- take-profit 2
- take-profit 3
- reward/risk ratio
- holding period
- explanatory notes

### Back-Book

Back-Book snapshots now include:

- strategy
- verdict
- Atlas Score
- entry range
- stop-loss
- take-profit levels
- chart setup
- trend status
- market structure
- EMA20 / EMA50 / SMA200
- RSI14
- ATR14
- support / resistance
- data quality

### UI

Updated Streamlit pages:

- app home page
- Mission Control
- Daily Candidates
- Screener/Search
- new Chart Engine page

### Tests

Added tests for:

- CSV asset history provider
- chart context generation
- recommendation chart context and Back-Book integration

## Safety boundaries preserved

- No broker connections.
- No automatic order placement.
- No live data dependency.
- No API keys required.
- Generated levels are planning outputs only.
- Sample data is explicitly flagged as sample data.

## Current limitations

- Asset OHLCV is deterministic sample data.
- Fundamentals remain sample hints.
- News/catalyst score is still placeholder.
- No live provider is enabled by default.
- No chart visualization is rendered yet; Sprint 2 calculates the data and shows tables/JSON.

## Recommended next sprint

Sprint 3: News + AI Narrative Provider Layer

Recommended scope:

- NewsProvider interface
- sample news provider
- Marketaux/NewsAPI/FMP provider skeletons
- symbol-level news cards
- relevance scoring
- sentiment placeholder
- catalyst score replacement
- strict AI summary guardrails
- news context in Back-Book

## Run commands

```bash
pytest
python scripts/run_daily_snapshot.py
streamlit run app.py
```
