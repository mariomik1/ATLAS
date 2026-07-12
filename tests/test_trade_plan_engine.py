from atlas_core.orchestrator import AtlasOrchestrator


def test_trade_plan_has_entry_stop_targets_and_crv():
    rec = AtlasOrchestrator().analyze_query("NVDA")
    plan = rec.trade_plan
    assert plan.entry_low < plan.entry_high
    assert plan.stop_loss < plan.entry_low
    assert plan.take_profit_1 > plan.entry_high
    assert plan.reward_risk_ratio >= 0
