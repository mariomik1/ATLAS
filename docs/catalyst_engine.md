# Catalyst Engine

Sprint 3 introduces the Catalyst Engine.

## Purpose

The Catalyst Engine answers:

- Why might this asset move now?
- Is there recent relevant news?
- Is sentiment positive, neutral, negative or mixed?
- Are there upcoming events such as earnings or macro catalysts?
- Are there risk flags that should reduce confidence?

## Inputs

- `NewsItem`
- `CatalystEvent`
- asset metadata from the watchlist

## Outputs

- `CatalystContext`
- `FactorScore(name="catalyst_ai")`
- AI statement context
- back-book evidence

## Scoring Logic v0.1

Base score starts at 50.

Positive inputs:

- average relevance above 50
- positive sentiment
- number of recent news items
- high-importance events on radar

Negative inputs:

- explicit risk flags
- negative sentiment
- missing news
- high-importance volatility events

## Important Guardrail

Catalyst score is not an instruction to trade. It is context. The final recommendation must still respect:

- market regime
- chart quality
- trade plan CRV
- portfolio fit
- risk limits
- data quality

## Future Upgrades

- provider freshness checks
- duplicate headline detection
- named-entity extraction
- earnings surprise integration
- analyst revision tracking
- SEC filing summaries
- source credibility scoring
- LLM-generated summaries with citations and strict grounding
