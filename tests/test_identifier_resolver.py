from atlas_core.config_loader import load_all_configs
from atlas_core.providers.identifier_resolver import IdentifierResolver
from atlas_core.providers.manual_provider import ManualSampleProvider


def test_resolve_ticker_name_isin_wkn():
    provider = ManualSampleProvider(load_all_configs()["watchlists"])
    resolver = IdentifierResolver(provider)
    assert resolver.resolve("MSFT").asset.symbol == "MSFT"
    assert resolver.resolve("Microsoft").asset.symbol == "MSFT"
    assert resolver.resolve("US67066G1040").asset.symbol == "NVDA"
    assert resolver.resolve("A0NC7B").asset.symbol == "V"


def test_search_returns_ranked_matches():
    provider = ManualSampleProvider(load_all_configs()["watchlists"])
    resolver = IdentifierResolver(provider)
    result = resolver.search("Visa")
    assert result.matches[0].symbol == "V"
    assert result.matches[0].match_type in {"name", "alias", "partial"}
    assert result.matches[0].confidence >= 75
