from __future__ import annotations

from atlas_core.models import CatalystContext, FundamentalContext


class AINarrativeEngine:
    """Deterministic narrative generator for the offline MVP.

    Later sprints can replace this with a guarded LLM call. Until then Atlas must
    never pretend that sample data, inferred news or missing fundamentals are live facts.
    Sprint 4 adds normalized fundamental context to the narrative.
    """

    def statement_for_candidate(
        self,
        symbol: str,
        verdict: str,
        score: float,
        reasons: list[str],
        risks: list[str],
        catalyst_context: CatalystContext | None = None,
        fundamental_context: FundamentalContext | None = None,
    ) -> str:
        reason_text = "; ".join(reasons[:3]) if reasons else "no strong deterministic reason"
        risk_text = "; ".join(risks[:3]) if risks else "no major MVP risk flag"
        catalyst_text = "No catalyst context available."
        if catalyst_context:
            catalyst_bits = []
            if catalyst_context.primary_catalyst:
                catalyst_bits.append(f"primary catalyst: {catalyst_context.primary_catalyst}")
            catalyst_bits.append(f"catalyst type: {catalyst_context.catalyst_type}")
            catalyst_bits.append(f"news items: {catalyst_context.news_count}")
            if catalyst_context.average_sentiment is not None:
                catalyst_bits.append(f"avg sentiment: {catalyst_context.average_sentiment:.2f}")
            catalyst_text = "; ".join(catalyst_bits)

        fundamental_text = "No normalized fundamental context available."
        if fundamental_context:
            fundamental_text = (
                f"classification {fundamental_context.classification}, "
                f"overall {fundamental_context.overall_score:.0f}/100, "
                f"growth {fundamental_context.growth_score:.0f}/100, "
                f"profitability {fundamental_context.profitability_score:.0f}/100, "
                f"valuation {fundamental_context.valuation_score:.0f}/100"
            )
        return (
            f"Atlas deterministic view: {symbol} is classified as {verdict} with score {score:.1f}. "
            f"Main reasons: {reason_text}. Fundamentals: {fundamental_text}. "
            f"Catalyst context: {catalyst_text}. Main risks: {risk_text}. "
            "Sprint 4 uses chart-aware OHLCV, source-aware sample news/catalyst data and normalized sample fundamentals; "
            "it is not investment advice. Any entry, stop-loss or take-profit level requires manual validation with live sources before action."
        )
