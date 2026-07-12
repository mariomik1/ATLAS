from atlas_core.orchestrator import AtlasOrchestrator


def test_technical_mvp_daily_briefing_contains_portfolio_fire_and_summary():
    briefing = AtlasOrchestrator().daily_briefing()
    assert briefing.technical_mvp_version == "technical_mvp_0.1"
    assert briefing.executive_summary
    assert briefing.portfolio.cash_pct >= 0
    assert briefing.fire.target_capital_eur > 0
    assert briefing.recommendations
    assert briefing.recommendations[0].trade_plan is not None


def test_orchestrator_can_append_recommendations_to_journal():
    orchestrator = AtlasOrchestrator()
    path = orchestrator.append_daily_recommendations_to_journal()
    assert path.endswith("recommendations.jsonl")
