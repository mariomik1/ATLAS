from atlas_core.config_loader import load_all_configs


def test_load_all_configs():
    cfg = load_all_configs()
    assert cfg["settings"]["app"]["name"] == "Atlas"
    assert cfg["risk_rules"]["satellite"]["max_capital_eur"] == 50000
    assert cfg["watchlists"]["default_watchlist"]
