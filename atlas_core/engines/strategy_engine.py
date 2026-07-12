from __future__ import annotations

from atlas_core.enums import AssetClass, InvestmentIntent, Strategy
from atlas_core.models import ChartContext
from atlas_core.providers.base import AssetMarketData


class StrategyEngine:
    def assign(self, item: AssetMarketData, chart_context: ChartContext | None = None) -> tuple[InvestmentIntent, Strategy]:
        asset = item.asset
        context = chart_context or item.chart_context

        if asset.asset_class == AssetClass.ETF and asset.sector == "Energy":
            return InvestmentIntent.DIVERSIFICATION, Strategy.DEFENSIVE_ALLOCATION

        if context:
            if context.setup_type == "momentum_pullback":
                return InvestmentIntent.SWING, Strategy.MOMENTUM_PULLBACK
            if context.setup_type == "breakout":
                return InvestmentIntent.SWING, Strategy.BREAKOUT
            if context.setup_type == "trend_continuation":
                return InvestmentIntent.SWING, Strategy.TREND_CONTINUATION
            if context.setup_type == "mean_reversion":
                return InvestmentIntent.SWING, Strategy.MEAN_REVERSION
            if asset.sector in {"Payments", "Software"} and item.fundamental_hint >= 88 and context.trend_status in {"bullish", "neutral"}:
                return InvestmentIntent.CORE, Strategy.CORE_INVESTMENT
            return InvestmentIntent.WATCH, Strategy.WATCHLIST_ONLY

        if item.momentum_hint >= 84 and item.atr_pct >= 3.5:
            return InvestmentIntent.SWING, Strategy.MOMENTUM_PULLBACK
        if asset.sector in {"Payments", "Software"} and item.fundamental_hint >= 88:
            return InvestmentIntent.CORE, Strategy.CORE_INVESTMENT
        if item.momentum_hint >= 78:
            return InvestmentIntent.SWING, Strategy.TREND_CONTINUATION
        return InvestmentIntent.WATCH, Strategy.WATCHLIST_ONLY
