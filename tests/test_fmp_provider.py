from __future__ import annotations

from atlas_core.enums import DataQualityLevel
from atlas_core.providers.fmp_provider import FMPFundamentalsProvider, FMPIdentifierProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache


def test_fmp_identifier_provider_fetches_and_caches(tmp_path):
    calls = []

    def fake_fetch(url: str, headers):
        calls.append(url)
        assert "apikey=test-key" in url
        return [
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "exchangeShortName": "NASDAQ",
                "currency": "USD",
                "isin": "US5949181045",
            }
        ]

    provider = FMPIdentifierProvider(
        api_key="test-key",
        live_enabled=True,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
        fetch_json=fake_fetch,
    )

    first = provider.search("Microsoft")
    second = provider.search("Microsoft")

    assert first.matches[0].symbol == "MSFT"
    assert first.matches[0].provider == "fmp_identifier"
    assert first.data_quality.level == DataQualityLevel.DELAYED
    assert second.matches[0].symbol == "MSFT"
    assert len(calls) == 1


def test_fmp_identifier_provider_disabled_uses_fallback(tmp_path):
    provider = FMPIdentifierProvider(
        api_key="test-key",
        live_enabled=False,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
    )

    result = provider.search("Visa")

    assert result.matches
    assert result.matches[0].symbol == "V"
    assert result.data_quality.level == DataQualityLevel.SAMPLE


def test_fmp_fundamentals_provider_normalizes_payload_and_caches(tmp_path):
    calls = []

    def fake_fetch(url: str, headers):
        calls.append(url)
        if "profile" in url:
            return [
                {
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "industry": "Software",
                    "country": "US",
                    "exchangeShortName": "NASDAQ",
                    "currency": "USD",
                    "isin": "US5949181045",
                    "mktCap": 3_000_000_000_000,
                    "beta": 1.1,
                }
            ]
        if "ratios-ttm" in url:
            return [
                {
                    "grossProfitMarginTTM": 0.69,
                    "operatingProfitMarginTTM": 0.44,
                    "netProfitMarginTTM": 0.36,
                    "returnOnEquityTTM": 0.32,
                    "debtEquityRatioTTM": 0.35,
                    "priceEarningsRatioTTM": 34,
                }
            ]
        if "key-metrics-ttm" in url:
            return [{"roicTTM": 0.22, "freeCashFlowYieldTTM": 0.026, "pegRatioTTM": 2.0}]
        if "income-statement-growth" in url:
            return [{"growthRevenue": 0.15, "growthEPSDiluted": 0.18}]
        if "analyst-estimates" in url:
            return [{"estimatedRevenueAvg": 300_000_000_000}]
        return []

    provider = FMPFundamentalsProvider(
        api_key="test-key",
        live_enabled=True,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
        fetch_json=fake_fetch,
    )

    first = provider.get_context("MSFT")
    second = provider.get_context("MSFT")

    assert first.profile.name == "Microsoft Corporation"
    assert first.metrics.gross_margin_pct == 69.0
    assert first.metrics.revenue_growth_yoy_pct == 15.0
    assert first.metrics.roic_pct == 22.0
    assert first.overall_score >= 75
    assert second.data_quality.provider == "fmp_fundamentals_cache"
    assert len(calls) == 5


def test_fmp_fundamentals_provider_fallback_on_failure(tmp_path):
    def fake_fetch(url: str, headers):
        raise RuntimeError("boom")

    provider = FMPFundamentalsProvider(
        api_key="test-key",
        live_enabled=True,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
        fetch_json=fake_fetch,
    )

    context = provider.get_context("MSFT")

    assert context.symbol == "MSFT"
    assert context.data_quality.level == DataQualityLevel.SAMPLE
    assert "fmp_fundamentals" in context.data_quality.provider
