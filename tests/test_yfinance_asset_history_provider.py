from __future__ import annotations

import sys
import types

import pandas as pd

from atlas_core.enums import DataQualityLevel
from atlas_core.providers.asset_history_provider import CsvAssetHistoryProvider, YFinanceAssetHistoryProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache


def test_yfinance_provider_disabled_uses_csv_fallback(tmp_path):
    fallback = CsvAssetHistoryProvider("data/samples/asset_ohlcv.csv")
    provider = YFinanceAssetHistoryProvider(
        fallback_provider=fallback,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
        live_enabled=False,
    )

    bars = provider.history_for("MSFT")
    quality = provider.data_quality_for("MSFT")

    assert len(bars) >= 300
    assert bars[-1].source == "csv_asset_sample"
    assert quality.level == DataQualityLevel.SAMPLE
    assert "fallback" in quality.provider


def test_yfinance_provider_fetches_and_caches_with_fake_module(monkeypatch, tmp_path):
    index = pd.date_range("2026-01-01", periods=5, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104],
            "High": [101, 102, 103, 104, 105],
            "Low": [99, 100, 101, 102, 103],
            "Close": [100.5, 101.5, 102.5, 103.5, 104.5],
            "Volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=index,
    )

    class FakeTicker:
        def __init__(self, symbol: str):
            self.symbol = symbol

        def history(self, period: str, interval: str, auto_adjust: bool):
            assert period == "18mo"
            assert interval == "1d"
            assert auto_adjust is False
            return frame

    fake_yf = types.SimpleNamespace(Ticker=FakeTicker)
    monkeypatch.setitem(sys.modules, "yfinance", fake_yf)

    cache = JsonFileCache(tmp_path / "cache")
    audit = FetchAuditLogger(tmp_path / "audit.jsonl")
    provider = YFinanceAssetHistoryProvider(cache=cache, audit=audit, live_enabled=True)

    bars = provider.history_for("MSFT")
    quality = provider.data_quality_for("MSFT")

    assert len(bars) == 5
    assert bars[-1].close == 104.5
    assert bars[-1].source == "yfinance"
    assert quality.level == DataQualityLevel.DELAYED
    assert cache.stats()["files"] == 1
    assert audit.tail(limit=1)[0]["status"] == "provider_fetch_success"


def test_yfinance_provider_cache_hit_avoids_network(monkeypatch, tmp_path):
    cache = JsonFileCache(tmp_path / "cache")
    audit = FetchAuditLogger(tmp_path / "audit.jsonl")
    payload = [
        {
            "symbol": "MSFT",
            "date": "2026-01-01",
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 100.5,
            "volume": 1000,
            "source": "yfinance",
        }
    ]
    cache.set("asset_ohlcv", "yfinance:MSFT:18mo:1d", payload)

    def fail_ticker(symbol: str):  # pragma: no cover - should never run
        raise AssertionError("network path should not be reached on cache hit")

    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(Ticker=fail_ticker))
    provider = YFinanceAssetHistoryProvider(cache=cache, audit=audit, live_enabled=True)

    bars = provider.history_for("MSFT")
    quality = provider.data_quality_for("MSFT")

    assert len(bars) == 1
    assert bars[0].source == "yfinance_cache"
    assert quality.provider == "yfinance_cache"
    assert audit.tail(limit=1)[0]["status"] == "cache_hit"
