from __future__ import annotations

from atlas_core.config_loader import load_all_configs
from atlas_core.engines.market_engine import MarketEngine
from atlas_core.enums import MarketRegime


def test_market_engine_builds_regime_from_benchmark_history():
    configs = load_all_configs()
    snapshot = MarketEngine(configs["settings"]).get_market_snapshot()
    assert snapshot.regime in {MarketRegime.RISK_ON, MarketRegime.NEUTRAL, MarketRegime.RISK_OFF}
    assert 0 <= snapshot.score <= 100
    assert snapshot.indicators
    assert snapshot.component_scores
    assert snapshot.trade_permission
    assert 0 < snapshot.position_size_multiplier <= 1.0


def test_market_engine_contains_expected_benchmarks():
    configs = load_all_configs()
    snapshot = MarketEngine(configs["settings"]).get_market_snapshot()
    symbols = {indicator.symbol for indicator in snapshot.indicators}
    assert {"SPY", "QQQ", "ACWI", "VIX"}.issubset(symbols)


def test_orchestrator_uses_market_multiplier_in_recommendations():
    from atlas_core.orchestrator import AtlasOrchestrator

    briefing = AtlasOrchestrator().daily_briefing()
    assert briefing.market.position_size_multiplier > 0
    assert briefing.recommendations
    assert any("Market permission" in action for action in briefing.actions)
