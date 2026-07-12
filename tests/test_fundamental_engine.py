from atlas_core.config_loader import load_all_configs
from atlas_core.engines.fundamental_engine import FundamentalEngine
from atlas_core.providers.manual_provider import ManualSampleProvider


def test_fundamental_engine_uses_normalized_context():
    configs = load_all_configs()
    item = ManualSampleProvider(configs["watchlists"]).resolve("V")
    factor = FundamentalEngine().evaluate(item, weight=20)
    assert factor.name == "fundamentals"
    assert factor.score >= 70
    assert "csv_sample_fundamentals" in factor.data_quality.provider
    assert item.fundamental_context is not None
    assert item.fundamental_context.metrics is not None
