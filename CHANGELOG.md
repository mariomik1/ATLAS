# Changelog

## 0.10.0-technical-mvp

### Added
- Technical MVP block combining Sprint 7, Sprint 8, Sprint 9 and Sprint 10.
- Marketaux news provider adapter with cache, audit and CSV fallback.
- NewsAPI provider adapter with cache, audit and CSV fallback.
- Portfolio Engine v1 with asset-class, sector and theme exposure calculations.
- Cash target range, portfolio advisory actions and risk flags.
- FIRE Engine v1 with deterministic progress, capital target, projected year and rough probability estimate.
- Daily Mission Control executive summary.
- Journal/Back-Book v1 with append/read/summarize behavior.
- Streamlit Technical MVP Status page.
- Tests for live-news normalization, fallback behavior, Technical MVP briefing and journal append.

### Changed
- Updated app metadata to `0.10.0-technical-mvp`.
- Mission Control now shows wealth, cash percentage, FIRE projection and candidate trade-plan table.
- Portfolio page now shows positions, exposures, advisory actions and risk flags.
- Journal page can append the daily recommendations to the local back-book.
- Orchestrator now passes portfolio context into risk/portfolio-fit calculations.

### Safety
- No broker integration was added.
- No automatic trading was added.
- API keys remain environment-based and are never committed.
- All live providers remain disabled by default.
- Provider output remains cache/audit-wrapped and fallback-safe.

## 0.6.1-sprint6b

- Added FMP identifier provider for ticker/name/ISIN search.
- Added FMP fundamentals provider for company profile, ratios, key metrics, growth and analyst-estimate context.
- Added OpenFIGI identifier provider for FIGI mapping and keyword search.
- Integrated FMP/OpenFIGI providers into the Atlas composite provider with safe fallbacks.
- Added cache and fetch-audit handling for FMP/OpenFIGI provider paths.

## 0.6.0-sprint6a

- Activated first controlled real/delayed asset-level OHLCV provider path via yfinance.
- Added cache/audit-backed `YFinanceAssetHistoryProvider`.
- Kept CSV sample history as safe default and fallback.

## Earlier sprints

See `SPRINT0_REPORT.md` through `SPRINT6B_REPORT.md` for prior sprint details.
