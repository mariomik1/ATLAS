from atlas_core.orchestrator import AtlasOrchestrator


def test_portfolio_snapshot_and_actions():
    briefing = AtlasOrchestrator().daily_briefing()
    assert briefing.portfolio.cash_eur == 140000
    assert briefing.portfolio.satellite_max_eur == 50000
    assert any("Cash" in action for action in briefing.actions)
