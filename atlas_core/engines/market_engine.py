from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas_core.enums import DataQualityLevel, MarketRegime
from atlas_core.models import DataQuality, MarketIndicator, MarketSnapshot
from atlas_core.providers.benchmark_provider import (
    BenchmarkHistoryProvider,
    CSVBenchmarkProvider,
    YFinanceBenchmarkProvider,
)
from atlas_core.utils.indicators import clamp, pct_change, rsi, safe_mean, sma
from atlas_core.utils.time_utils import utc_now


class MarketEngine:
    """Market regime engine for Atlas Sprint 1.

    The engine converts benchmark OHLCV history into a practical trading permission:
    risk_on, neutral, risk_off or unknown. It is deliberately conservative: Atlas may miss
    opportunities when market data is weak, but it should not encourage aggressive trading in
    hostile market regimes.
    """

    def __init__(self, settings: dict[str, Any], provider: BenchmarkHistoryProvider | None = None):
        self.settings = settings
        self.market_settings = settings.get("market", {})
        self.provider = provider or self._build_provider()

    def _build_provider(self) -> BenchmarkHistoryProvider:
        provider_name = str(self.market_settings.get("provider", "csv_sample")).lower()
        if provider_name == "yfinance":
            return YFinanceBenchmarkProvider()
        csv_path = Path(self.market_settings.get("csv_path", "data/samples/benchmark_history.csv"))
        return CSVBenchmarkProvider(csv_path)

    def get_market_snapshot(self) -> MarketSnapshot:
        try:
            return self._snapshot_from_provider()
        except Exception as exc:
            if not self.market_settings.get("fallback_to_manual_regime", True):
                raise
            return self._manual_fallback_snapshot(exc)

    def _snapshot_from_provider(self) -> MarketSnapshot:
        benchmarks = self.market_settings.get("benchmarks", [])
        symbols = [row["symbol"] for row in benchmarks]
        if not symbols:
            raise ValueError("No market benchmarks configured.")

        lookback_days = int(self.market_settings.get("lookback_days", 320))
        history = self.provider.get_history(symbols, lookback_days=lookback_days)
        if history.empty:
            raise ValueError("No benchmark history returned.")

        provider_quality = self.provider.data_quality()
        indicators: list[MarketIndicator] = []
        weights_by_symbol = {row["symbol"].upper(): float(row.get("weight", 1.0)) for row in benchmarks}
        names_by_symbol = {row["symbol"].upper(): str(row.get("name", row["symbol"])) for row in benchmarks}
        roles_by_symbol = {row["symbol"].upper(): str(row.get("role", "benchmark")) for row in benchmarks}

        for symbol in symbols:
            symbol_upper = symbol.upper()
            frame = history[history["symbol"].str.upper() == symbol_upper].copy()
            if frame.empty:
                indicators.append(
                    MarketIndicator(
                        symbol=symbol_upper,
                        name=names_by_symbol.get(symbol_upper, symbol_upper),
                        close=0.01,
                        trend_status="missing",
                        score=35,
                        risks=[f"No history for {symbol_upper}."],
                        data_quality=DataQuality(
                            level=DataQualityLevel.MISSING,
                            provider=provider_quality.provider,
                            as_of=utc_now(),
                            issues=[f"Missing benchmark data for {symbol_upper}."],
                        ),
                    )
                )
                continue
            indicators.append(
                self._indicator_from_frame(
                    symbol=symbol_upper,
                    name=names_by_symbol.get(symbol_upper, symbol_upper),
                    role=roles_by_symbol.get(symbol_upper, "benchmark"),
                    frame=frame,
                    data_quality=provider_quality,
                )
            )

        component_scores = self._component_scores(indicators, weights_by_symbol)
        score = self._weighted_score(component_scores)
        regime = self._regime_from_score(score)
        multiplier = self._position_multiplier(regime)
        permission = self._trade_permission(regime)
        warnings = self._market_warnings(indicators, component_scores, provider_quality)
        summary = self._summary(regime, score, component_scores, indicators)
        data_quality = self._aggregate_quality(provider_quality, indicators)
        return MarketSnapshot(
            regime=regime,
            score=round(score, 2),
            summary=summary,
            as_of=utc_now(),
            data_quality=data_quality,
            indicators=indicators,
            component_scores={k: round(v, 2) for k, v in component_scores.items()},
            trade_permission=permission,
            position_size_multiplier=multiplier,
            warnings=warnings,
        )

    def _indicator_from_frame(
        self,
        symbol: str,
        name: str,
        role: str,
        frame: pd.DataFrame,
        data_quality: DataQuality,
    ) -> MarketIndicator:
        frame = frame.sort_values("date").copy()
        close = frame["close"].astype(float)
        last_close = float(close.iloc[-1])
        sma_50_value = self._latest_or_none(sma(close, 50))
        sma_200_value = self._latest_or_none(sma(close, 200))
        ret20 = pct_change(close, 20)
        ret60 = pct_change(close, 60)
        rsi14 = self._latest_or_none(rsi(close, 14))
        dist50 = self._distance_pct(last_close, sma_50_value)
        dist200 = self._distance_pct(last_close, sma_200_value)
        score, reasons, risks, status = self._score_indicator(
            symbol=symbol,
            role=role,
            close=last_close,
            sma_50=sma_50_value,
            sma_200=sma_200_value,
            ret20=ret20,
            ret60=ret60,
            rsi14=rsi14,
            dist50=dist50,
            dist200=dist200,
        )
        return MarketIndicator(
            symbol=symbol,
            name=name,
            close=round(last_close, 2),
            sma_50=round(sma_50_value, 2) if sma_50_value is not None else None,
            sma_200=round(sma_200_value, 2) if sma_200_value is not None else None,
            return_20d_pct=round(ret20, 2) if ret20 is not None else None,
            return_60d_pct=round(ret60, 2) if ret60 is not None else None,
            distance_to_sma_50_pct=round(dist50, 2) if dist50 is not None else None,
            distance_to_sma_200_pct=round(dist200, 2) if dist200 is not None else None,
            rsi_14=round(rsi14, 2) if rsi14 is not None else None,
            trend_status=status,
            score=round(score, 2),
            reasons=reasons,
            risks=risks,
            data_quality=data_quality,
        )

    def _score_indicator(
        self,
        symbol: str,
        role: str,
        close: float,
        sma_50: float | None,
        sma_200: float | None,
        ret20: float | None,
        ret60: float | None,
        rsi14: float | None,
        dist50: float | None,
        dist200: float | None,
    ) -> tuple[float, list[str], list[str], str]:
        if role == "volatility" or symbol.upper() in {"VIX", "^VIX"}:
            # VIX: lower is better for risk appetite. A falling VIX below 20 is supportive.
            vix_level_score = clamp(100 - (close - 12) * 5)
            ret_score = 55 if ret20 is None else clamp(60 - ret20 * 1.8)
            score = 0.70 * vix_level_score + 0.30 * ret_score
            reasons = [f"Volatility proxy at {close:.2f}."]
            risks = []
            if close > 22:
                risks.append("Volatility is elevated; reduce new risk positions.")
            if ret20 is not None and ret20 > 15:
                risks.append("Volatility has risen quickly over 20 sessions.")
            status = "supportive" if score >= 70 else "elevated" if score >= 45 else "hostile"
            return score, reasons, risks, status

        trend_parts: list[float] = []
        reasons: list[str] = []
        risks: list[str] = []
        if sma_50 is not None:
            above50 = close > sma_50
            trend_parts.append(75 if above50 else 35)
            reasons.append("Above SMA50." if above50 else "Below SMA50.")
        if sma_200 is not None:
            above200 = close > sma_200
            trend_parts.append(82 if above200 else 25)
            reasons.append("Above SMA200." if above200 else "Below SMA200.")
            if not above200:
                risks.append("Long-term trend is not supportive.")
        if sma_50 is not None and sma_200 is not None:
            golden = sma_50 > sma_200
            trend_parts.append(80 if golden else 35)
            reasons.append("SMA50 above SMA200." if golden else "SMA50 below SMA200.")
        if ret20 is not None:
            trend_parts.append(clamp(50 + ret20 * 3.0))
            reasons.append(f"20d return {ret20:.1f}%.")
        if ret60 is not None:
            trend_parts.append(clamp(50 + ret60 * 1.8))
        if rsi14 is not None:
            if 45 <= rsi14 <= 68:
                trend_parts.append(78)
                reasons.append("RSI is constructive, not extremely overbought.")
            elif rsi14 > 75:
                trend_parts.append(55)
                risks.append("RSI is extended; avoid chasing.")
            elif rsi14 < 40:
                trend_parts.append(40)
                risks.append("RSI is weak; momentum confirmation missing.")
            else:
                trend_parts.append(62)
        score = safe_mean(trend_parts) or 50
        if dist200 is not None and dist200 < -5:
            risks.append("Price is materially below SMA200.")
        if dist50 is not None and dist50 > 8:
            risks.append("Short-term market may be extended above SMA50.")
        status = "uptrend" if score >= 70 else "mixed" if score >= 45 else "downtrend"
        return score, reasons, risks, status

    def _component_scores(self, indicators: list[MarketIndicator], weights: dict[str, float]) -> dict[str, float]:
        weighted_scores = []
        weighted_total = 0.0
        equity_indicators = [i for i in indicators if i.symbol.upper() not in {"VIX", "^VIX"}]
        volatility_indicators = [i for i in indicators if i.symbol.upper() in {"VIX", "^VIX"}]
        for indicator in indicators:
            weight = weights.get(indicator.symbol.upper(), 1.0)
            weighted_scores.append(indicator.score * weight)
            weighted_total += weight
        trend_score = sum(weighted_scores) / weighted_total if weighted_total else 50.0
        above_50 = [i for i in equity_indicators if i.distance_to_sma_50_pct is not None and i.distance_to_sma_50_pct > 0]
        above_200 = [i for i in equity_indicators if i.distance_to_sma_200_pct is not None and i.distance_to_sma_200_pct > 0]
        breadth_base = len(equity_indicators) or 1
        breadth_score = ((len(above_50) / breadth_base) * 45) + ((len(above_200) / breadth_base) * 55)
        momentum_score = safe_mean([i.score for i in equity_indicators]) or trend_score
        volatility_score = safe_mean([i.score for i in volatility_indicators]) or 55
        return {
            "trend": trend_score,
            "breadth": breadth_score,
            "momentum": momentum_score,
            "volatility": volatility_score,
        }

    @staticmethod
    def _weighted_score(component_scores: dict[str, float]) -> float:
        return (
            0.35 * component_scores.get("trend", 50)
            + 0.25 * component_scores.get("momentum", 50)
            + 0.20 * component_scores.get("breadth", 50)
            + 0.20 * component_scores.get("volatility", 50)
        )

    def _regime_from_score(self, score: float) -> MarketRegime:
        thresholds = self.market_settings.get("regime_thresholds", {})
        risk_on = float(thresholds.get("risk_on", 70))
        neutral = float(thresholds.get("neutral", 45))
        if score >= risk_on:
            return MarketRegime.RISK_ON
        if score >= neutral:
            return MarketRegime.NEUTRAL
        return MarketRegime.RISK_OFF

    def _position_multiplier(self, regime: MarketRegime) -> float:
        multipliers = self.market_settings.get("position_multipliers", {})
        return float(multipliers.get(regime.value, {"risk_on": 1.0, "neutral": 0.65, "risk_off": 0.30, "unknown": 0.20}.get(regime.value, 0.5)))

    @staticmethod
    def _trade_permission(regime: MarketRegime) -> str:
        if regime == MarketRegime.RISK_ON:
            return "normal_new_trades_allowed"
        if regime == MarketRegime.NEUTRAL:
            return "selective_trades_reduced_size"
        if regime == MarketRegime.RISK_OFF:
            return "exceptional_setups_only_small_position"
        return "no_new_trades_until_market_data_available"

    def _summary(
        self,
        regime: MarketRegime,
        score: float,
        component_scores: dict[str, float],
        indicators: list[MarketIndicator],
    ) -> str:
        strongest = max(indicators, key=lambda item: item.score, default=None)
        weakest = min(indicators, key=lambda item: item.score, default=None)
        base = {
            MarketRegime.RISK_ON: "Risk-On: New trades are allowed, but Atlas still requires clean setups.",
            MarketRegime.NEUTRAL: "Neutral: Prefer smaller positions and higher-quality setups.",
            MarketRegime.RISK_OFF: "Risk-Off: Only exceptional setups with reduced position size.",
            MarketRegime.UNKNOWN: "Unknown: Market regime could not be determined.",
        }[regime]
        detail = f" Market score {score:.0f}/100; trend {component_scores.get('trend', 0):.0f}, breadth {component_scores.get('breadth', 0):.0f}, volatility {component_scores.get('volatility', 0):.0f}."
        if strongest and weakest:
            detail += f" Strongest signal: {strongest.symbol}; weakest signal: {weakest.symbol}."
        return base + detail

    def _market_warnings(
        self,
        indicators: list[MarketIndicator],
        component_scores: dict[str, float],
        provider_quality: DataQuality,
    ) -> list[str]:
        warnings: list[str] = []
        for indicator in indicators:
            warnings.extend(indicator.risks[:2])
        if component_scores.get("breadth", 50) < 50:
            warnings.append("Market breadth is weak; reduce conviction for individual long setups.")
        if provider_quality.level == DataQualityLevel.SAMPLE.value or provider_quality.level == DataQualityLevel.SAMPLE:
            warnings.append("Market regime is based on bundled sample history, not current live data.")
        return list(dict.fromkeys(warnings))[:8]

    def _aggregate_quality(self, provider_quality: DataQuality, indicators: list[MarketIndicator]) -> DataQuality:
        issues = list(provider_quality.issues)
        if any(i.data_quality.level in {DataQualityLevel.MISSING.value, DataQualityLevel.MISSING} for i in indicators):
            issues.append("At least one configured benchmark is missing.")
            level = DataQualityLevel.PARTIAL
        else:
            level = DataQualityLevel(provider_quality.level)
        return DataQuality(level=level, provider=provider_quality.provider, as_of=utc_now(), issues=issues)

    def _manual_fallback_snapshot(self, exc: Exception) -> MarketSnapshot:
        regime_raw = self.market_settings.get("default_regime", "neutral")
        regime = MarketRegime(regime_raw)
        score = {MarketRegime.RISK_ON: 78, MarketRegime.NEUTRAL: 55, MarketRegime.RISK_OFF: 28, MarketRegime.UNKNOWN: 40}[regime]
        summary = f"Fallback market regime from settings because provider failed: {exc}"
        return MarketSnapshot(
            regime=regime,
            score=score,
            summary=summary,
            data_quality=DataQuality(
                level=DataQualityLevel.PARTIAL,
                provider="settings.yaml fallback",
                issues=[str(exc), "Provider failed. Manual fallback regime used."],
            ),
            trade_permission=self._trade_permission(regime),
            position_size_multiplier=self._position_multiplier(regime),
            warnings=["Market provider failed; treat all signals as low confidence."],
        )

    @staticmethod
    def _latest_or_none(series: pd.Series) -> float | None:
        clean = series.dropna()
        if clean.empty:
            return None
        return float(clean.iloc[-1])

    @staticmethod
    def _distance_pct(close: float, average: float | None) -> float | None:
        if average is None or average == 0:
            return None
        return (close / average - 1.0) * 100.0
