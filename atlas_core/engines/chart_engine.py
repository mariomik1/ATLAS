from __future__ import annotations

import pandas as pd

from atlas_core.models import ChartContext, DataQuality, FactorScore
from atlas_core.providers.base import AssetMarketData
from atlas_core.utils.indicators import atr, clamp, ema, pct_change, rsi, sma


class ChartEngine:
    """Asset-level technical analysis engine.

    Sprint 2 calculates indicators from normalized OHLCV history instead of using
    static hints. The output is intentionally explainable: every chart context
    carries reasons, risks and data-quality metadata used in the Back-Book.
    """

    def analyze(self, item: AssetMarketData) -> ChartContext:
        if item.chart_context is not None:
            return item.chart_context
        if not item.history:
            context = self._fallback_context(item)
            item.chart_context = context
            return context

        df = self._to_dataframe(item)
        if len(df) < 60:
            context = self._fallback_context(item, extra_issue="OHLCV history is shorter than 60 bars.")
            item.chart_context = context
            return context

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        ema_20_series = ema(close, 20)
        ema_50_series = ema(close, 50)
        sma_200_series = sma(close, 200)
        rsi_14_series = rsi(close, 14)
        atr_14_series = atr(high, low, close, 14)

        price = float(close.iloc[-1])
        ema_20 = self._latest(ema_20_series)
        ema_50 = self._latest(ema_50_series)
        sma_200 = self._latest(sma_200_series)
        rsi_14 = self._latest(rsi_14_series)
        atr_14 = self._latest(atr_14_series)
        atr_pct = (atr_14 / price * 100.0) if atr_14 else item.atr_pct

        previous_20 = df.iloc[-21:-1] if len(df) >= 21 else df.iloc[:-1]
        previous_60 = df.iloc[-61:-1] if len(df) >= 61 else df.iloc[:-1]
        swing_low_20 = float(previous_20["low"].min()) if not previous_20.empty else float(low.iloc[-1])
        swing_high_20 = float(previous_20["high"].max()) if not previous_20.empty else float(high.iloc[-1])
        support_1 = swing_low_20
        support_2 = float(previous_60["low"].min()) if not previous_60.empty else support_1
        resistance_1 = swing_high_20
        resistance_2 = float(previous_60["high"].max()) if not previous_60.empty else resistance_1

        avg_vol_20 = float(volume.iloc[-21:-1].mean()) if len(volume) > 21 else float(volume.mean())
        volume_ratio = float(volume.iloc[-1] / avg_vol_20) if avg_vol_20 > 0 else None

        ret_20 = pct_change(close, 20)
        ret_60 = pct_change(close, 60)
        distance_ema20 = self._distance(price, ema_20)
        distance_ema50 = self._distance(price, ema_50)
        distance_sma200 = self._distance(price, sma_200)

        trend_status, trend_score, trend_reasons, trend_risks = self._trend_score(
            price=price,
            ema_20=ema_20,
            ema_50=ema_50,
            sma_200=sma_200,
            rsi_14=rsi_14,
            ret_20=ret_20,
            ret_60=ret_60,
        )
        market_structure, structure_score, structure_reasons = self._market_structure(df)
        setup_type, setup_score, setup_reasons, setup_risks = self._setup_score(
            price=price,
            ema_20=ema_20,
            ema_50=ema_50,
            sma_200=sma_200,
            rsi_14=rsi_14,
            distance_ema20=distance_ema20,
            support_1=support_1,
            resistance_1=resistance_1,
            volume_ratio=volume_ratio,
            trend_status=trend_status,
        )

        score = clamp(0.45 * trend_score + 0.25 * structure_score + 0.30 * setup_score)
        issues = list(item.data_quality.issues)
        if len(df) < 220:
            issues.append("Less than 220 OHLCV bars; SMA200 and long-term trend may be partial.")
        quality = DataQuality(level=item.data_quality.level, provider=f"{item.data_quality.provider}+chart_engine", issues=issues)
        context = ChartContext(
            symbol=item.asset.symbol,
            current_price=round(price, 2),
            ema_20=self._round(ema_20),
            ema_50=self._round(ema_50),
            sma_200=self._round(sma_200),
            rsi_14=self._round(rsi_14),
            atr_14=self._round(atr_14),
            atr_pct=self._round(atr_pct),
            return_20d_pct=self._round(ret_20),
            return_60d_pct=self._round(ret_60),
            distance_to_ema_20_pct=self._round(distance_ema20),
            distance_to_ema_50_pct=self._round(distance_ema50),
            distance_to_sma_200_pct=self._round(distance_sma200),
            swing_low_20=round(swing_low_20, 2),
            swing_high_20=round(swing_high_20, 2),
            support_1=round(support_1, 2),
            support_2=round(support_2, 2),
            resistance_1=round(resistance_1, 2),
            resistance_2=round(resistance_2, 2),
            volume_ratio_20d=self._round(volume_ratio),
            trend_status=trend_status,
            market_structure=market_structure,
            setup_type=setup_type,
            score=round(score, 2),
            reasons=trend_reasons + structure_reasons + setup_reasons,
            risks=trend_risks + setup_risks,
            data_quality=quality,
        )
        item.chart_context = context
        item.current_price = context.current_price
        if context.atr_pct:
            item.atr_pct = context.atr_pct
        return context

    def evaluate_momentum(self, item: AssetMarketData, weight: float) -> FactorScore:
        context = self.analyze(item)
        score = context.score
        if context.return_20d_pct is not None and context.return_20d_pct > 8:
            score = min(100, score + 4)
        if context.trend_status == "bullish":
            score = min(100, score + 3)
        if context.trend_status == "bearish":
            score = max(0, score - 10)
        return FactorScore(
            name="momentum",
            score=round(score, 2),
            weight=weight,
            reasons=context.reasons[:4] or ["Momentum derived from asset-level OHLCV chart context."],
            risks=context.risks[:3],
            data_quality=context.data_quality,
        )

    def evaluate_timing(self, item: AssetMarketData, weight: float) -> FactorScore:
        context = self.analyze(item)
        score = 50.0
        reasons: list[str] = []
        risks: list[str] = []

        if context.setup_type == "momentum_pullback":
            score = 88
            reasons.append("Pullback is inside the preferred trend zone near EMA20/support.")
        elif context.setup_type == "breakout":
            score = 82
            reasons.append("Price is near or above prior resistance with supportive volume.")
        elif context.setup_type == "trend_continuation":
            score = 76
            reasons.append("Trend is constructive, but entry is less optimal than a pullback.")
        elif context.setup_type == "mean_reversion":
            score = 68
            reasons.append("Mean-reversion setup exists near support, but confirmation is required.")
        else:
            score = 55
            reasons.append("No high-quality chart setup is currently confirmed.")
            risks.append("Atlas should prefer waiting for a cleaner entry zone.")

        if context.distance_to_ema_20_pct is not None:
            if context.distance_to_ema_20_pct > 5:
                score -= 14
                risks.append("Price is extended above EMA20; do not chase.")
            elif -3 <= context.distance_to_ema_20_pct <= 2:
                score += 5
                reasons.append("Distance to EMA20 is inside the preferred entry band.")
        if context.rsi_14 is not None and context.rsi_14 > 72:
            score -= 10
            risks.append("RSI is elevated; staged entry or waiting is preferred.")

        return FactorScore(
            name="chart_timing",
            score=round(clamp(score), 2),
            weight=weight,
            reasons=reasons,
            risks=risks + context.risks[:2],
            data_quality=context.data_quality,
        )

    def technical_context(self, item: AssetMarketData) -> dict:
        context = self.analyze(item)
        return context.model_dump(mode="json")

    @staticmethod
    def _to_dataframe(item: AssetMarketData) -> pd.DataFrame:
        rows = [bar.model_dump(mode="json") for bar in item.history]
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        return df[["open", "high", "low", "close", "volume"]].astype(float)

    @staticmethod
    def _latest(series: pd.Series) -> float | None:
        clean = series.dropna()
        if clean.empty:
            return None
        return float(clean.iloc[-1])

    @staticmethod
    def _round(value: float | None, digits: int = 2) -> float | None:
        if value is None:
            return None
        return round(float(value), digits)

    @staticmethod
    def _distance(price: float, reference: float | None) -> float | None:
        if reference is None or reference <= 0:
            return None
        return (price / reference - 1.0) * 100.0

    def _trend_score(
        self,
        *,
        price: float,
        ema_20: float | None,
        ema_50: float | None,
        sma_200: float | None,
        rsi_14: float | None,
        ret_20: float | None,
        ret_60: float | None,
    ) -> tuple[str, float, list[str], list[str]]:
        score = 50.0
        reasons: list[str] = []
        risks: list[str] = []
        if ema_20 and price > ema_20:
            score += 8
            reasons.append("Price is above EMA20.")
        elif ema_20:
            score -= 7
            risks.append("Price is below EMA20.")
        if ema_20 and ema_50 and ema_20 > ema_50:
            score += 10
            reasons.append("EMA20 is above EMA50.")
        elif ema_20 and ema_50:
            score -= 8
            risks.append("EMA20 is below EMA50.")
        if ema_50 and sma_200 and ema_50 > sma_200:
            score += 12
            reasons.append("EMA50 is above SMA200.")
        elif ema_50 and sma_200:
            score -= 12
            risks.append("EMA50 is below SMA200.")
        if sma_200 and price > sma_200:
            score += 10
            reasons.append("Price is above SMA200.")
        elif sma_200:
            score -= 15
            risks.append("Price is below SMA200.")
        if ret_20 is not None and ret_20 > 0:
            score += min(10, ret_20 * 0.7)
            reasons.append(f"20-day return is positive ({ret_20:.1f}%).")
        elif ret_20 is not None:
            score -= min(10, abs(ret_20) * 0.9)
            risks.append(f"20-day return is negative ({ret_20:.1f}%).")
        if ret_60 is not None and ret_60 > 0:
            score += min(8, ret_60 * 0.25)
        if rsi_14 is not None:
            if 45 <= rsi_14 <= 68:
                score += 8
                reasons.append("RSI is in the preferred constructive range.")
            elif rsi_14 > 75:
                score -= 8
                risks.append("RSI is potentially overheated.")
            elif rsi_14 < 38:
                score -= 6
                risks.append("RSI is weak; wait for confirmation.")
        score = clamp(score)
        if score >= 72:
            status = "bullish"
        elif score <= 42:
            status = "bearish"
        else:
            status = "neutral"
        return status, score, reasons, risks

    def _market_structure(self, df: pd.DataFrame) -> tuple[str, float, list[str]]:
        if len(df) < 40:
            return "unknown", 50.0, ["Insufficient history for market-structure comparison."]
        last = df.iloc[-20:]
        prev = df.iloc[-40:-20]
        last_high = float(last["high"].max())
        prev_high = float(prev["high"].max())
        last_low = float(last["low"].min())
        prev_low = float(prev["low"].min())
        if last_high > prev_high and last_low > prev_low:
            return "higher_high_higher_low", 86.0, ["Market structure shows higher high and higher low."]
        if last_high < prev_high and last_low < prev_low:
            return "lower_high_lower_low", 34.0, ["Market structure shows lower high and lower low."]
        return "mixed", 58.0, ["Market structure is mixed."]

    def _setup_score(
        self,
        *,
        price: float,
        ema_20: float | None,
        ema_50: float | None,
        sma_200: float | None,
        rsi_14: float | None,
        distance_ema20: float | None,
        support_1: float,
        resistance_1: float,
        volume_ratio: float | None,
        trend_status: str,
    ) -> tuple[str, float, list[str], list[str]]:
        reasons: list[str] = []
        risks: list[str] = []
        near_support = support_1 > 0 and (price / support_1 - 1.0) * 100 <= 5.0
        near_resistance = resistance_1 > 0 and price >= resistance_1 * 0.985
        trend_bullish = trend_status == "bullish"
        if trend_bullish and distance_ema20 is not None and -4.0 <= distance_ema20 <= 2.5 and rsi_14 is not None and 42 <= rsi_14 <= 70:
            reasons.append("Momentum pullback candidate: bullish trend and price near EMA20.")
            return "momentum_pullback", 90.0, reasons, risks
        if trend_bullish and near_resistance and (volume_ratio or 1.0) >= 1.05:
            reasons.append("Breakout candidate: price is pressing prior resistance with volume support.")
            return "breakout", 82.0, reasons, risks
        if trend_bullish and distance_ema20 is not None and 2.5 < distance_ema20 <= 6.0:
            reasons.append("Trend-continuation candidate: trend is strong but not deeply pulled back.")
            risks.append("Entry quality is weaker than a pullback; use do-not-chase discipline.")
            return "trend_continuation", 74.0, reasons, risks
        if rsi_14 is not None and rsi_14 < 42 and near_support and sma_200 and price > sma_200:
            reasons.append("Mean-reversion candidate near support inside a larger uptrend.")
            risks.append("Mean reversion requires confirmation; not a blind catch-the-knife setup.")
            return "mean_reversion", 68.0, reasons, risks
        risks.append("No preferred chart setup confirmed today.")
        return "watch", 52.0, reasons, risks

    def _fallback_context(self, item: AssetMarketData, extra_issue: str | None = None) -> ChartContext:
        price = item.current_price
        atr_value = price * item.atr_pct / 100.0
        issues = list(item.data_quality.issues)
        issues.append("Chart context uses fallback because OHLCV history is missing or insufficient.")
        if extra_issue:
            issues.append(extra_issue)
        quality = DataQuality(level=item.data_quality.level, provider=f"{item.data_quality.provider}+chart_fallback", issues=issues)
        return ChartContext(
            symbol=item.asset.symbol,
            current_price=round(price, 2),
            atr_14=round(atr_value, 2),
            atr_pct=round(item.atr_pct, 2),
            swing_low_20=round(price - 1.2 * atr_value, 2),
            swing_high_20=round(price + 1.8 * atr_value, 2),
            support_1=round(price - 1.2 * atr_value, 2),
            resistance_1=round(price + 1.8 * atr_value, 2),
            trend_status="unknown",
            market_structure="unknown",
            setup_type="watch",
            score=float(item.momentum_hint),
            reasons=["Fallback chart context from configured price and ATR hint."],
            risks=["No asset-level OHLCV history available."],
            data_quality=quality,
        )
