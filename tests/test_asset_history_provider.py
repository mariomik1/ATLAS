from __future__ import annotations

from atlas_core.providers.asset_history_provider import CsvAssetHistoryProvider


def test_csv_asset_history_provider_loads_sample_bars():
    provider = CsvAssetHistoryProvider("data/samples/asset_ohlcv.csv")
    bars = provider.history_for("MSFT")
    assert len(bars) >= 300
    assert bars[-1].close > 0
    assert bars[-1].symbol == "MSFT"
