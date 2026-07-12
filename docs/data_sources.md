# Atlas Data Sources

Atlas uses a provider layer. Engines never depend directly on a vendor payload; providers normalize data into internal models first.

## Sprint 3 active providers

| Layer | Active provider | Path | Status |
|---|---|---|---|
| Market regime | CSV sample benchmark history | `data/samples/benchmark_history.csv` | offline sample |
| Asset OHLCV | CSV sample asset history | `data/samples/asset_ohlcv.csv` | offline sample |
| News | CSV sample news | `data/samples/news_items.csv` | offline sample |
| Catalyst events | CSV sample events | `data/samples/events.csv` | offline sample |

## Future provider targets

| Data need | Candidate providers | Notes |
|---|---|---|
| Daily/intraday OHLCV | FMP, Alpha Vantage, Polygon/Massive, yfinance fallback | Must preserve delay/live status. |
| Company news | Marketaux, FMP, NewsAPI | Must store title, source, URL, timestamp, relevance and sentiment if available. |
| Fundamentals | FMP, Alpha Vantage | Sprint 4 target. |
| Identifier search | FMP, OpenFIGI, manual mapping | Needed for ticker/name/ISIN/WKN workflows. |
| Earnings/events | FMP, Alpha Vantage, provider calendar feeds | Add event quality flags. |

## Rules

- API keys must live in `.env` or deployment secrets, never in code.
- Live providers must use cache and throttling.
- AI statements may only cite normalized provider data.
- Every recommendation must expose `data_quality`.
- Sample data must never be presented as live market facts.
