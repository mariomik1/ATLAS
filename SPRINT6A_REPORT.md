# Sprint 6A Report - yfinance OHLCV Provider

## Objective

Activate the first real/delayed asset-level market-data provider behind the Sprint 5 provider activation, cache and audit layer.

## Implemented

- Added cache/audit-backed `YFinanceAssetHistoryProvider`.
- Kept CSV sample OHLCV as the default safe fallback.
- Updated `ManualSampleProvider` to choose asset history provider from `config/settings.yaml`.
- Wired yfinance OHLCV data quality into recommendations and Chart Engine output.
- Added yfinance cache-hit, disabled-fallback and fake-live-fetch tests.
- Added documentation in `docs/yfinance_ohlcv.md`.
- Updated app version to `0.6.0-sprint6a`.

## Safety Boundaries

- No broker connection.
- No auto-trading.
- No API keys required.
- yfinance disabled by default.
- If enabled and unavailable, Atlas falls back safely.
- Provider decisions are audit logged.

## Test Result

```text
32 passed
```

## Next Sprint Recommendation

Sprint 6B: FMP/OpenFIGI provider activation for fundamentals and identifier search, or Sprint 7: Portfolio Engine v1 with real positions and allocation constraints.
