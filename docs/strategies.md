# Strategies

Sprint 2 strategy assignment is chart-context aware.

## Supported strategy labels

- Momentum Pullback
- Breakout
- Trend Continuation
- Mean Reversion
- Core Investment
- Defensive Allocation
- Cash Deployment
- Watchlist Only

## Setup classification inputs

- Trend status from EMA20/EMA50/SMA200 and returns
- Market structure from recent highs/lows
- Distance to EMA20
- RSI14
- Support/resistance proximity
- Volume ratio

## Trade plan outputs

Every candidate with a plan receives:

- strategy
- entry low
- entry high
- do-not-chase-above
- stop-loss
- take-profit 1
- take-profit 2
- take-profit 3
- reward/risk ratio
- holding period
- notes

Plans are not orders. Manual review is mandatory.
