# Sprint 3 News + Catalyst Engine

The Catalyst Engine adds source-aware context to Atlas recommendations. It does not make autonomous decisions and does not override weak chart, market, risk or portfolio-fit gates.

## Inputs

- `NewsItem`: symbol, title, summary, source, URL, timestamp, sentiment, relevance, impact, risk flag.
- `CatalystEvent`: symbol, event date, event type, description, importance, source.

## Outputs

- `CatalystContext`: score, catalyst type, news count, averages, primary catalyst, event types, events, reasons and risks.
- `FactorScore(name="catalyst_ai")`: integrated into Atlas Score with the configured weight.
- Back-Book catalyst evidence.
- Source-aware deterministic AI statement.

## Current scoring sketch

The Sprint 3 catalyst score starts at 50 and adjusts for:

- average sentiment,
- average relevance,
- average impact,
- positive vs. negative item balance,
- risk flags,
- high-importance events.

This is a transparent MVP heuristic, not a proven alpha model.

## Safety guardrails

- No claim may be made without a source item.
- Missing news downgrades data quality and score.
- Risk headlines are shown explicitly.
- Sample data is flagged as sample.
