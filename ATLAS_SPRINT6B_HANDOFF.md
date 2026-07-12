# ATLAS Sprint 6B Handoff

## Sprint Objective

Activate the first controlled live/delayed provider paths for fundamentals and identifiers while preserving Atlas' offline-first and fail-closed architecture.

## Implemented

- FMP identifier provider for ticker/name/ISIN search.
- FMP fundamentals provider for company profile, ratios, key metrics, growth and analyst estimates.
- OpenFIGI identifier provider for FIGI search/mapping.
- Provider composition in the main Atlas asset provider.
- Cache and fetch-audit integration for FMP/OpenFIGI paths.
- Safe fallbacks to local sample fundamentals and identifier master.
- Provider Registry update for OpenFIGI optional API-key behavior.
- Streamlit text updates for Sprint 6B provider status and fundamentals/search pages.
- Documentation: `docs/fmp_openfigi_activation.md`.
- Tests for FMP provider, OpenFIGI provider and provider readiness.

## Tests

Executed in build environment:

```text
pytest -q
40 passed
```

Daily snapshot also executed successfully:

```text
python scripts/run_daily_snapshot.py
```

## Safety Boundaries

Sprint 6B still includes no:

- broker connection
- automatic trading
- order placement
- production authentication
- committed API keys
- mandatory network access

Live/delayed providers require explicit config activation. FMP requires `FMP_API_KEY`. OpenFIGI can work without a key at lower limits but still requires `live_providers_enabled: true`.

## Configuration Examples

FMP fundamentals:

```yaml
fundamentals:
  provider: fmp
  live_providers_enabled: true
```

FMP identifiers:

```yaml
identifiers:
  provider: fmp
  live_providers_enabled: true
```

OpenFIGI identifiers:

```yaml
identifiers:
  provider: openfigi
  live_providers_enabled: true
```

## Known Limitations

- FMP field names vary by endpoint/plan; provider normalization is robust but may need plan-specific tuning once real keys are tested.
- OpenFIGI does not provide WKN-native enrichment in this sprint.
- FMP does not provide WKN-native search in this sprint.
- Fundamentals are useful for scoring but still require human validation before investment decisions.
- No live fetch was executed in this build environment.

## Recommended Next Sprint

Sprint 7: News Provider Activation.

Recommended scope:

- Marketaux provider.
- NewsAPI or FMP news fallback.
- Source URLs and source-quality flags.
- Cache TTLs for news.
- AI summary input with strict citation/source guardrails.
- Catalyst Engine upgrade from sample news to controlled live/delayed news.
