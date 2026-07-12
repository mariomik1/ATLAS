from __future__ import annotations

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.engines.chart_engine import ChartEngine


def test_chart_engine_builds_context_from_sample_ohlcv():
    orchestrator = AtlasOrchestrator()
    item = orchestrator.provider.resolve("MSFT")
    context = ChartEngine().analyze(item)
    assert context.symbol == "MSFT"
    assert context.current_price > 0
    assert context.ema_20 is not None
    assert context.ema_50 is not None
    assert context.sma_200 is not None
    assert context.rsi_14 is not None
    assert context.atr_14 is not None
    assert context.support_1 is not None
    assert context.resistance_1 is not None
    assert context.setup_type in {"momentum_pullback", "breakout", "trend_continuation", "mean_reversion", "watch"}
    assert context.score >= 0


def test_recommendation_contains_chart_context_and_chart_anchored_backbook():
    rec = AtlasOrchestrator().analyze_query("NVDA")
    assert rec.chart_context is not None
    assert rec.back_book_summary["chart"]["setup_type"] == rec.chart_context.setup_type
    assert rec.trade_plan is not None
    assert rec.trade_plan.stop_loss < rec.trade_plan.entry_low
    assert rec.trade_plan.take_profit_1 > rec.trade_plan.entry_high
