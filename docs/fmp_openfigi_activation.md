# Atlas Sprint 6B - FMP / OpenFIGI Provider Activation

Status: Sprint 6B

## Objective

Sprint 6B adds the first controlled provider paths for:

- FMP fundamentals
- FMP ticker/name/ISIN search
- OpenFIGI identifier mapping/search

The goal is not to turn Atlas into a live trading system. The goal is to improve the Screener, Fundamentals Engine and identifier resolution while keeping Atlas offline-first, auditable and safe.

## Provider principles

1. No provider performs network calls unless explicitly enabled.
2. API keys are read from process environment or `.env`, never hard-coded.
3. Every provider path has cache and audit logging.
4. Every provider path has fallback behavior.
5. Provider results are normalized into Atlas models before any engine consumes them.
6. Data quality is explicitly marked as live/delayed/partial/sample/missing.
7. Identifier matches are never treated as verified tradability or execution instructions.

## FMP fundamentals

Class: `atlas_core.providers.fmp_provider.FMPFundamentalsProvider`

Used endpoints:

- `profile`
- `ratios-ttm`
- `key-metrics-ttm`
- `income-statement-growth`
- `analyst-estimates`

Normalized into:

- `CompanyProfile`
- `FundamentalMetrics`
- `FundamentalContext`

Fallback:

- `CsvSampleFundamentalsProvider`

## FMP identifiers

Class: `atlas_core.providers.fmp_provider.FMPIdentifierProvider`

Used endpoints:

- `search-name`
- `search-symbol`
- `search-isin`

Supported well in Sprint 6B:

- ticker
- company/ETF name
- ISIN

Not natively solved by FMP in Sprint 6B:

- WKN

WKN-like mappings remain local/fallback-based until a licensed WKN-capable data source is added.

## OpenFIGI identifiers

Class: `atlas_core.providers.openfigi_provider.OpenFigiIdentifierProvider`

Used endpoints:

- `POST /v3/mapping`
- `POST /v3/search`

OpenFIGI is useful for FIGI mapping and symbol/name discovery. It is not a fundamentals provider and does not replace FMP or a broker/security master.

OpenFIGI can be used without an API key at lower limits, but Atlas still requires explicit `live_providers_enabled: true` before it will perform network calls.

## Configuration examples

### Offline defaults

```yaml
fundamentals:
  provider: csv_sample
  live_providers_enabled: false

identifiers:
  provider: local_sample
  live_providers_enabled: false
```

### FMP fundamentals and identifiers

```yaml
fundamentals:
  provider: fmp
  live_providers_enabled: true

identifiers:
  provider: fmp
  live_providers_enabled: true
```

`.env`:

```text
FMP_API_KEY=...
```

### OpenFIGI identifiers

```yaml
identifiers:
  provider: openfigi
  live_providers_enabled: true
```

`.env` optional but recommended:

```text
OPENFIGI_API_KEY=...
```

## Cache and audit

FMP/OpenFIGI provider responses use the Sprint 5 JSON cache and append decisions to the fetch audit log.

Typical statuses:

- `provider_fetch_success`
- `cache_hit`
- `provider_fetch_failed`
- `disabled_by_config`
- `missing_api_key`
- `provider_failed_fallback`

## Data quality

Atlas does not assume provider data is perfect. The UI and recommendation JSON should surface quality and source metadata.

Typical concerns:

- provider plan limitations
- delayed or stale data
- missing fields
- non-primary listings
- identifier ambiguity
- ETF/fund classification ambiguity
- ISIN/WKN mismatch risk

## Next provider sprint candidates

After Sprint 6B, likely options are:

1. Marketaux/NewsAPI provider activation for live news and catalysts.
2. FMP earnings/calendar activation.
3. Improved provider selection UI with provider diagnostics and sample/live toggles.
4. Persistent security master enriched by provider responses.
