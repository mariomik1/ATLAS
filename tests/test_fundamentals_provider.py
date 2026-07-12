from atlas_core.config_loader import load_all_configs
from atlas_core.providers.fundamentals_provider import CsvSampleFundamentalsProvider


def test_csv_sample_fundamentals_provider_loads_profile():
    settings = load_all_configs()["settings"]
    path = settings["fundamentals"]["csv_path"]
    provider = CsvSampleFundamentalsProvider(path)
    profile = provider.get_context("MSFT")
    assert profile is not None
    assert profile.symbol == "MSFT"
    assert profile.quality_score >= 90
    assert profile.data_quality.level == "sample"
