# Sprint 7 Report - News Provider Activation

Implemented controlled Marketaux and NewsAPI provider adapters.

- Live providers are disabled by default.
- Providers require explicit `live_providers_enabled: true`.
- API keys are loaded from `.env` or environment variables.
- Every provider path uses cache and audit wrappers.
- CSV sample fallback remains active.
- Tests use fake HTTP clients and no network calls.
