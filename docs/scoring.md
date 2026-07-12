# Scoring

Atlas combines factor scores by intent-specific weights.

## Current factors

- Market
- Fundamentals
- Momentum
- Chart Timing
- Risk
- Portfolio Fit
- Catalyst / AI placeholder

## Sprint 2 changes

- Momentum and chart timing now use asset-level OHLCV-derived ChartContext.
- Data quality includes chart-engine provider information.
- Missing or sample data reduces confidence.

## Future work

- Add live/delayed provider quality tiers.
- Add news and earnings catalyst score.
- Add sector-relative strength.
- Add recommendation outcome tracking to calibrate weights.
