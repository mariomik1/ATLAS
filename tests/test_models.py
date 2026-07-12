from atlas_core.orchestrator import AtlasOrchestrator


def test_recommendation_serializes_to_json():
    rec = AtlasOrchestrator().analyze_query("MSFT")
    payload = rec.model_dump(mode="json")
    assert payload["asset"]["symbol"] == "MSFT"
    assert payload["trade_plan"]["entry_low"] > 0
    assert payload["data_quality"]["level"] == "sample"
