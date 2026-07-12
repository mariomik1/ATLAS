# Atlas Provider Activation + Cache Layer

Status: Sprint 5

## Purpose

Sprint 5 adds the safety layer required before Atlas can use live or delayed data providers. The goal is not to fetch every live data source yet. The goal is to make provider activation explicit, auditable and reversible.

## Principles

1. Atlas defaults to offline sample data.
2. API keys are never committed to the repository.
3. Live providers must be enabled explicitly in config.
4. Missing API keys fail closed.
5. Every future provider fetch must be cached and audit logged.
6. Provider status must be visible in the UI.
7. Engines consume normalized Atlas models, not raw provider payloads.

## Supported Provider Roles

| Role | Sample Provider | Live/Delayed Providers Prepared |
|---|---|---|
| market | csv_sample | yfinance, alphavantage |
| asset_data | csv_sample | yfinance, fmp, alphavantage, polygon |
| news | csv_sample | marketaux, newsapi, fmp |
| fundamentals | csv_sample | fmp, alphavantage |
| identifiers | local_sample | openfigi, fmp |

## Environment Variables

Configured in `.env` locally or deployment secrets in cloud:

```text
FMP_API_KEY=
MARKETAUX_API_KEY=
NEWSAPI_API_KEY=
ALPHAVANTAGE_API_KEY=
OPENFIGI_API_KEY=
POLYGON_API_KEY=
```

## Activation Flow

1. Select a provider in `config/settings.yaml`.
2. Set `live_providers_enabled: true` for that provider role.
3. Add the relevant API key to `.env` or deployment secrets.
4. Check the `Provider Status` page.
5. Only then connect a real provider adapter.

Sprint 5 does not implement production fetches. It prepares readiness checks, cache and audit plumbing.

## Cache

Implemented by `atlas_core.utils.cache.JsonFileCache`.

Default path:

```text
data/cache/
```

The cache writes JSON envelopes:

```json
{
  "created_at": "...",
  "namespace": "news",
  "key": "MSFT/latest",
  "metadata": {},
  "payload": {}
}
```

## Audit Log

Implemented by `atlas_core.utils.cache.FetchAuditLogger`.

Default path:

```text
data/cache/fetch_audit.jsonl
```

Each record stores provider, resource, status, cache hit, data quality and message.

## Current Limitation

Live calls are intentionally not implemented in Sprint 5. This is by design. The next sprint can activate one provider at a time behind these interfaces.


## Sprint 6A Update: yfinance OHLCV

Sprint 6A implements the first live/delayed provider adapter behind the activation layer: `YFinanceAssetHistoryProvider`. It is disabled by default and does not require an API key. When enabled, it fetches daily OHLCV bars, writes them to the JSON cache, and appends provider decisions to the audit log. If the provider fails, Atlas falls back to stale cache or CSV sample data.

Recommended activation for local testing:

```yaml
asset_data:
  provider: yfinance
  live_providers_enabled: true
  yfinance_period: 18mo
  yfinance_interval: 1d
  cache_ttl_hours: 24
```

Data quality should be treated as delayed/unverified. This is not exchange-certified realtime data.
