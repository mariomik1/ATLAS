# Sprint 6B Report - FMP / OpenFIGI Provider Activation

## Objective

Add controlled live/delayed provider paths for fundamentals and identifier search while keeping Atlas offline-first, auditable and safe.

## Implemented

- FMP fundamentals provider with cache, audit and sample fallback
- FMP ticker/name/ISIN search provider with cache and fallback
- OpenFIGI mapping/search provider with cache and fallback
- Provider composition in `ManualSampleProvider`
- Config-driven provider selection for fundamentals and identifiers
- `.env`-based API-key readiness path
- Provider Status copy updated for Sprint 6B
- README updated for Sprint 6B
- Documentation added: `docs/fmp_openfigi_activation.md`
- Tests for FMP and OpenFIGI provider behavior

## Tests

```text
40 passed
```

## Safety status

- Broker connections remain disabled.
- Auto-trading remains disabled.
- Live provider calls are disabled by default.
- API keys are never stored in code.
- Providers use cache/audit/fallback patterns.
- FMP/OpenFIGI data remains decision-support data, not execution-grade data.

## Known limitations

- WKN is not solved by FMP/OpenFIGI in this sprint and remains local/fallback-based.
- Provider payload schemas can differ by subscription tier and market.
- No persistent enriched security master yet.
- No live news provider activation yet.
- No FMP earnings/calendar integration yet.

## Recommended next sprint

Sprint 6C or Sprint 7 should activate the News/Catalyst provider layer:

- Marketaux provider
- NewsAPI provider
- FMP news fallback
- cache/audit for live news
- source URLs in catalyst context
- better AI narrative grounding
