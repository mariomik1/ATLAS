from atlas_core.orchestrator import AtlasOrchestrator


def test_identifier_search_partial_and_isin():
    orchestrator = AtlasOrchestrator()
    result = orchestrator.search_assets("Crowd")
    assert result.matches
    assert result.matches[0].symbol == "CRWD"
    assert result.matches[0].confidence >= 60
    rec = orchestrator.analyze_query("US92826C8394")
    assert rec.asset.symbol == "V"
    assert rec.fundamental_context is not None
    assert rec.fundamental_context.overall_score >= 70


def test_identifier_search_wkn_like_mapping():
    orchestrator = AtlasOrchestrator()
    rec = orchestrator.analyze_query("A0NC7B")
    assert rec is not None
    assert rec.asset.symbol == "V"
