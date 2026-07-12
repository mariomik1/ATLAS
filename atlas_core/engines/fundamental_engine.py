from __future__ import annotations

from atlas_core.models import DataQuality, FactorScore, FundamentalContext
from atlas_core.providers.base import AssetMarketData
from atlas_core.providers.fundamentals_provider import FundamentalsProvider
from atlas_core.utils.indicators import clamp


class FundamentalEngine:
    """Evaluate company/ETF fundamentals from normalized provider contexts."""

    def __init__(self, provider: FundamentalsProvider | None = None):
        self.provider = provider

    def context_for(self, item: AssetMarketData) -> FundamentalContext | None:
        if item.fundamental_context is not None:
            return item.fundamental_context
        if self.provider is None:
            return None
        context = self.provider.get_context(item.asset.symbol)
        if context is not None:
            item.fundamental_context = context
        return context

    def evaluate(self, item: AssetMarketData, weight: float) -> FactorScore:
        context = self.context_for(item)
        if context is None:
            risks = []
            if item.fundamental_hint < 70:
                risks.append("Fundamental profile is below preferred Atlas quality threshold.")
            return FactorScore(
                name="fundamentals",
                score=float(item.fundamental_hint),
                weight=weight,
                reasons=["Fundamental score uses fallback sample hint because no normalized provider context is available."],
                risks=risks + ["Fundamental context is missing; use only as provisional analysis."],
                data_quality=DataQuality(
                    level=item.data_quality.level,
                    provider=f"{item.data_quality.provider}+fundamental_fallback",
                    issues=item.data_quality.issues + ["Missing normalized fundamental context."],
                ),
            )

        score = self._score(context)
        reasons = list(context.reasons)
        risks = list(context.risks)
        reasons.extend(self._metric_reasons(context))
        risks.extend(self._metric_risks(context))
        return FactorScore(
            name="fundamentals",
            score=round(score, 2),
            weight=weight,
            reasons=reasons[:6] or ["Normalized fundamental context is available."],
            risks=risks[:6],
            data_quality=context.data_quality,
        )

    @staticmethod
    def _score(context: FundamentalContext) -> float:
        raw = (
            0.25 * context.quality_score
            + 0.18 * context.growth_score
            + 0.20 * context.profitability_score
            + 0.15 * context.balance_sheet_score
            + 0.15 * context.valuation_score
            + 0.07 * context.ownership_score
        )
        return clamp(raw)

    @staticmethod
    def _metric_reasons(context: FundamentalContext) -> list[str]:
        m = context.metrics
        if m is None:
            return []
        reasons: list[str] = []
        if m.gross_margin_pct is not None and m.gross_margin_pct >= 55:
            reasons.append(f"Gross margin is high ({m.gross_margin_pct:.1f}%).")
        if m.operating_margin_pct is not None and m.operating_margin_pct >= 25:
            reasons.append(f"Operating margin is strong ({m.operating_margin_pct:.1f}%).")
        if m.roe_pct is not None and m.roe_pct >= 18:
            reasons.append(f"ROE is attractive ({m.roe_pct:.1f}%).")
        if m.revenue_growth_yoy_pct is not None and m.revenue_growth_yoy_pct >= 10:
            reasons.append(f"Revenue growth is positive ({m.revenue_growth_yoy_pct:.1f}% YoY).")
        if m.debt_to_equity is not None and m.debt_to_equity <= 0.6:
            reasons.append(f"Debt-to-equity is controlled ({m.debt_to_equity:.2f}).")
        return reasons

    @staticmethod
    def _metric_risks(context: FundamentalContext) -> list[str]:
        m = context.metrics
        if m is None:
            return []
        risks: list[str] = []
        if m.peg_ratio is not None and m.peg_ratio > 2.5:
            risks.append(f"PEG appears elevated ({m.peg_ratio:.2f}); valuation discipline required.")
        if m.forward_pe is not None and m.forward_pe > 45:
            risks.append(f"Forward P/E is high ({m.forward_pe:.1f}); multiple compression risk.")
        if m.debt_to_equity is not None and m.debt_to_equity > 1.5:
            risks.append(f"Debt-to-equity is high ({m.debt_to_equity:.2f}).")
        if m.revenue_growth_yoy_pct is not None and m.revenue_growth_yoy_pct < 0:
            risks.append(f"Revenue growth is negative ({m.revenue_growth_yoy_pct:.1f}% YoY).")
        if m.net_margin_pct is not None and m.net_margin_pct < 5:
            risks.append(f"Net margin is thin ({m.net_margin_pct:.1f}%).")
        return risks
