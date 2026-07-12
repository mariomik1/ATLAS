# Fundamentals + Identifier Search

Sprint 4 adds normalized security identification and fundamental context.

## Identifier flow

1. User enters ticker, name, ISIN, WKN or alias.
2. `IdentifierResolver` searches local sample master data.
3. Best match is converted into an `AssetMarketData` object.
4. Atlas enriches it with OHLCV, fundamentals and catalyst context.
5. The recommendation stores identifier evidence in the Back-Book through data quality metadata.

## Fundamental flow

1. `CsvSampleFundamentalsProvider` loads `data/samples/fundamentals.csv`.
2. Provider maps rows into `CompanyProfile` and `FundamentalMetrics`.
3. Provider creates an explainable `FundamentalContext`.
4. `FundamentalEngine` exposes that context as the fundamentals factor in Atlas Score.
5. AI narrative and Journal receive the same normalized context.

## Future live providers

- FMP for fundamentals, calendar and search.
- OpenFIGI for identifier mapping.
- Alpha Vantage as fallback for certain fundamentals.

Live providers must include API-key isolation, rate-limit handling, local caching, mocked tests and source attribution before they can affect recommendations.
