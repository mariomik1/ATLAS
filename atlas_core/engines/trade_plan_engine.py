from __future__ import annotations

from atlas_core.enums import Strategy
from atlas_core.models import ChartContext, TradePlan
from atlas_core.providers.base import AssetMarketData


class TradePlanEngine:
    """Builds chart-anchored trade plans.

    Sprint 2 replaces pure ATR proxy levels with levels anchored to EMA, swing,
    support and resistance data from ChartContext. It remains decision support
    only and never places orders.
    """

    def build(self, item: AssetMarketData, strategy: Strategy, chart_context: ChartContext | None = None) -> TradePlan:
        context = chart_context or item.chart_context
        if context is None:
            return self._fallback_build(item, strategy)

        price = context.current_price
        atr_value = context.atr_14 or price * (context.atr_pct or item.atr_pct) / 100.0
        ema20 = context.ema_20 or price
        ema50 = context.ema_50 or ema20
        support1 = context.support_1 or context.swing_low_20 or price - 1.3 * atr_value
        support2 = context.support_2 or support1 - atr_value
        resistance1 = context.resistance_1 or context.swing_high_20 or price + 1.8 * atr_value
        resistance2 = context.resistance_2 or max(resistance1, price + 3.0 * atr_value)

        notes = [
            f"Chart setup: {context.setup_type}; trend: {context.trend_status}; structure: {context.market_structure}.",
            "Entry, stop and targets are chart-derived planning levels, not orders.",
            "Manual review is required before any real-world action.",
        ]

        if strategy == Strategy.MOMENTUM_PULLBACK:
            anchor = min(price, ema20)
            entry_low = max(support1, anchor - 0.35 * atr_value)
            entry_high = min(price + 0.10 * atr_value, max(entry_low + 0.35 * atr_value, ema20 + 0.20 * atr_value))
            stop = min(support1, ema50) - 0.65 * atr_value
            holding = "2-8 weeks. Review after TP1, after loss of EMA20/EMA50, or if market regime deteriorates."
            notes.append("Momentum pullback: preferred entry is near EMA20/support, not after an extended move.")
        elif strategy == Strategy.BREAKOUT:
            breakout_level = max(resistance1, price)
            entry_low = min(price, breakout_level)
            entry_high = breakout_level + 0.35 * atr_value
            stop = max(support1, ema20 - 0.3 * atr_value) - 0.90 * atr_value
            holding = "1-6 weeks. Breakout should hold above prior resistance; failed breakout requires fast review."
            notes.append("Breakout: entry is anchored around prior resistance and confirmation volume.")
        elif strategy == Strategy.TREND_CONTINUATION:
            entry_low = max(ema20, price - 0.70 * atr_value)
            entry_high = price + 0.20 * atr_value
            stop = min(ema20, support1) - 0.80 * atr_value
            holding = "2-6 weeks. Use smaller size if entry is extended above EMA20."
            notes.append("Trend continuation: acceptable only if do-not-chase level is respected.")
        elif strategy == Strategy.MEAN_REVERSION:
            entry_low = support1 + 0.05 * atr_value
            entry_high = min(price, support1 + 0.80 * atr_value)
            stop = min(support2, support1 - 1.00 * atr_value)
            holding = "3 days to 4 weeks. Requires confirmation; exit quickly if support breaks."
            notes.append("Mean reversion: setup is tactical and should not be treated as a core buy.")
        elif strategy == Strategy.CORE_INVESTMENT:
            entry_low = max(support1, ema20 - 0.40 * atr_value)
            entry_high = min(price + 0.15 * atr_value, ema20 + 0.75 * atr_value)
            stop = min(support2, ema50 - 1.50 * atr_value)
            holding = "Core: months to years. Tactical levels guide entry only; thesis review matters more than TP levels."
            notes.append("Core candidate: use tactical entry discipline without over-optimizing the first fill.")
        elif strategy == Strategy.DEFENSIVE_ALLOCATION:
            entry_low = price - 0.70 * atr_value
            entry_high = price + 0.10 * atr_value
            stop = min(support1, ema50) - 0.80 * atr_value
            holding = "2-12 weeks or portfolio diversification sleeve. Rebalance against total allocation."
            notes.append("Defensive allocation: position sizing should consider diversification value, not only chart score.")
        else:
            entry_low = max(support1, price - 1.00 * atr_value)
            entry_high = min(price, ema20 + 0.20 * atr_value)
            stop = min(support1, ema50) - 0.70 * atr_value
            holding = "Watch only until setup improves. No trade by default."
            notes.append("Watchlist: levels identify where a future setup may become interesting.")

        return self._finalize(
            item=item,
            strategy=strategy,
            price=price,
            atr_value=atr_value,
            entry_low=entry_low,
            entry_high=entry_high,
            stop=stop,
            resistance1=resistance1,
            resistance2=resistance2,
            holding=holding,
            notes=notes + context.reasons[:3] + context.risks[:2],
        )

    def _finalize(
        self,
        *,
        item: AssetMarketData,
        strategy: Strategy,
        price: float,
        atr_value: float,
        entry_low: float,
        entry_high: float,
        stop: float,
        resistance1: float,
        resistance2: float,
        holding: str,
        notes: list[str],
    ) -> TradePlan:
        entry_low = max(0.01, entry_low)
        entry_high = max(entry_low + 0.01, entry_high)
        stop = min(stop, entry_low - 0.01)
        stop = max(0.01, stop)
        risk = max(entry_high - stop, 0.01)
        tp1 = max(resistance1, entry_high + 1.65 * risk)
        tp2 = max(resistance2, entry_high + 2.60 * risk)
        tp3 = max(tp2 + 0.01, entry_high + 3.80 * risk)
        do_not_chase = max(entry_high + 0.01, min(tp1, price + 0.80 * atr_value))
        reward = max(tp1 - entry_high, 0)
        rr = round(reward / risk, 2)
        return TradePlan(
            currency=item.asset.currency,
            strategy=strategy,
            current_price=round(price, 2),
            entry_low=round(entry_low, 2),
            entry_high=round(entry_high, 2),
            do_not_chase_above=round(do_not_chase, 2),
            stop_loss=round(stop, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            take_profit_3=round(tp3, 2),
            reward_risk_ratio=rr,
            holding_period=holding,
            notes=notes,
        )

    def _fallback_build(self, item: AssetMarketData, strategy: Strategy) -> TradePlan:
        price = item.current_price
        atr_value = price * item.atr_pct / 100
        entry_low = price - 1.0 * atr_value
        entry_high = price - 0.1 * atr_value
        stop = price - 2.1 * atr_value
        return self._finalize(
            item=item,
            strategy=strategy,
            price=price,
            atr_value=atr_value,
            entry_low=entry_low,
            entry_high=entry_high,
            stop=stop,
            resistance1=price + 1.6 * atr_value,
            resistance2=price + 2.8 * atr_value,
            holding="2-8 weeks. Fallback plan; chart context unavailable.",
            notes=[
                "Fallback ATR plan used because chart context was unavailable.",
                "This should not happen in Sprint 2 if OHLCV sample history exists.",
            ],
        )
