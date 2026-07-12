# Atlas Sprint 6A - yfinance OHLCV Provider

Status: Sprint 6A

## Purpose

Sprint 6A activates Atlas' first real/delayed asset-level OHLCV provider path. The objective is not realtime trading. The objective is to replace static sample bars with a controlled, auditable, cache-backed provider that can improve the Chart Engine's entry, stop-loss and take-profit planning levels.

## What is activated

- `YFinanceAssetHistoryProvider`
- Daily OHLCV bars via `yfinance.Ticker(symbol).history(...)`
- JSON cache namespace: `asset_ohlcv`
- Fetch audit logging for cache hits, disabled provider fallback, successful provider fetches and provider failures
- CSV sample fallback when live calls are disabled, fail, return empty data or yfinance is unavailable
- Data-quality propagation into `ChartContext`, `Recommendation` and Back-Book payloads

## Configuration

Default mode remains offline-safe:

```yaml
asset_data:
  provider: csv_sample
  live_providers_enabled: false
```

To test yfinance locally:

```yaml
asset_data:
  provider: yfinance
  live_providers_enabled: true
  yfinance_period: 18mo
  yfinance_interval: 1d
  cache_ttl_hours: 24
```

No API key is required for yfinance. Network access is required.

## Safety rules

1. yfinance is treated as delayed/unverified data, not exchange-certified realtime data.
2. Atlas never places trades.
3. Every yfinance result must be cached.
4. Every provider decision must be audit logged.
5. If yfinance fails, Atlas must keep running through stale cache or CSV sample fallback.
6. Recommendations must expose their data-quality status.

## Cache behavior

- Fresh cache hit: use cached bars and skip network.
- Expired cache: attempt live fetch.
- Provider failure with stale cache: use stale bars and mark data quality as `partial`.
- Provider failure without stale cache: fallback to CSV sample and mark source accordingly.

## Limitations

- yfinance data can be delayed, adjusted, incomplete or unavailable.
- Data provider terms must be reviewed before any production-like deployment.
- This sprint does not activate realtime quotes, intraday signals or broker execution.
- Entry/stop/TP levels are planning outputs only and require manual review.
