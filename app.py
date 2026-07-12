import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.set_page_config(page_title="Atlas", page_icon="🧭", layout="wide")
st.title("Atlas")
st.caption("Personal Wealth Operating System - Sprint 6B FMP/OpenFIGI data activation Provider")

briefing = AtlasOrchestrator().daily_briefing()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Market", briefing.market.regime)
col2.metric("Market Score", f"{briefing.market.score:.0f}/100")
col3.metric("Position Multiplier", f"{briefing.market.position_size_multiplier:.2f}x")
col4.metric("Tracked Wealth", f"€{briefing.portfolio.total_tracked_eur:,.0f}")
col5.metric("FIRE Progress", f"{briefing.fire.progress_pct:.1f}%")

st.success(briefing.headline)
st.info(
    "Sprint 6B adds gated FMP/OpenFIGI provider activation for fundamentals and identifiers. "
    "Atlas remains decision support, not investment advice, and not an autotrader."
)

st.subheader("Top Candidates")
rows = []
for rec in briefing.recommendations:
    tp = rec.trade_plan
    cc = rec.chart_context
    cat = rec.catalyst_context
    fp = rec.fundamental_context
    rows.append(
        {
            "Symbol": rec.asset.symbol,
            "Name": rec.asset.name,
            "Verdict": rec.verdict,
            "Strategy": rec.strategy,
            "Setup": cc.setup_type if cc else "n/a",
            "Trend": cc.trend_status if cc else "n/a",
            "Fundamental": fp.quality_score if fp else None,
            "Growth": fp.growth_score if fp else None,
            "Overall": fp.overall_score if fp else None,
            "Catalyst": cat.score if cat else None,
            "News": cat.news_count if cat else 0,
            "Atlas Score": rec.atlas_score,
            "Confidence": rec.score_breakdown.confidence_pct,
            "Entry": f"{tp.entry_low} - {tp.entry_high}" if tp else "n/a",
            "Stop": tp.stop_loss if tp else "n/a",
            "TP1": tp.take_profit_1 if tp else "n/a",
            "CRV": tp.reward_risk_ratio if tp else "n/a",
            "Max EUR": rec.portfolio_fit.max_position_eur,
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Actions")
for action in briefing.actions:
    st.write(f"- {action}")

with st.expander("Back-book JSON preview"):
    st.json(briefing.recommendations[0].model_dump(mode="json") if briefing.recommendations else {})
