# Atlas Technical MVP Handoff

## Version

`0.10.0-technical-mvp`

## Scope

This package continues from Sprint 6B and implements the remaining technical MVP sprints as a single block:

- Sprint 7: News Provider Activation
- Sprint 8: Portfolio Engine v1
- Sprint 9: FIRE Engine v1
- Sprint 10: Daily Mission Control + Journal/Back-Book v1

## What is included

- Market regime engine from prior sprints.
- Asset-level chart engine from prior sprints.
- FMP/OpenFIGI provider activation from prior sprints.
- New Marketaux and NewsAPI news adapters.
- Portfolio exposure calculations.
- FIRE progress calculation.
- Daily Mission Control briefing.
- Journal/back-book recommendation persistence.
- Updated Streamlit pages.
- Updated README and changelog.
- Tests for the new MVP block.

## Test result

```text
44 passed
```

## How to run

```bash
cd atlas_technical_mvp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
python scripts/run_daily_snapshot.py
streamlit run app.py
```

## Safety boundaries

- No broker connection.
- No automatic order placement.
- No API keys committed.
- Live providers are disabled by default.
- All provider paths are cache/audit/fallback wrapped.
- Recommendation levels are planning outputs only.

## Current default mode

The app remains offline-first:

- asset_data: csv_sample
- news: csv_sample
- fundamentals: csv_sample
- identifiers: local_sample

## Next recommended phase

The technical MVP is now complete enough for first local testing. The next phase should be **Private Daily v0.1**, not more foundation work.

Recommended next sprints:

1. Local run + visual QA on Mac.
2. Provider smoke test with real `.env` keys.
3. Deploy to Streamlit Cloud or Render.
4. Mobile layout pass for iPad/iPhone.
5. Strategy/backtest/journal outcome tracking.

## Known limitations

- News sentiment is provider/native or neutral; no LLM sentiment classifier yet.
- FIRE engine is deterministic, not Monte Carlo.
- Portfolio file is manual YAML, not broker-synced.
- Sample data remains the default.
- Live provider endpoints should be smoke-tested with real keys in the user's environment.
