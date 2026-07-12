import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.set_page_config(page_title="Atlas Mission Control", layout="wide")
st.title("Mission Control")
st.caption("Technical MVP: market + chart + catalysts/news + fundamentals/search + portfolio + FIRE + journal/back-book.")

orchestrator = AtlasOrchestrator()
briefing = orchestrator.daily_briefing()

cols = st.columns(6)
cols[0].metric("Market", str(briefing.market.regime), f"{briefing.market.score:.0f}/100")
cols[1].metric("Trade Permission", briefing.market.trade_permission)
cols[2].metric("Candidates", len(briefing.recommendations))
cols[3].metric("Tracked Wealth", f"EUR {briefing.portfolio.total_tracked_eur:,.0f}")
cols[4].metric("Cash", f"{briefing.portfolio.cash_pct:.1f}%")
cols[5].metric("FIRE", f"{briefing.fire.progress_pct:.1f}%", f"{briefing.fire.projected_year}")

st.subheader("Executive Summary")
for item in briefing.executive_summary:
    st.write(f"- {item}")
if briefing.no_trade_message:
    st.info(briefing.no_trade_message)

st.subheader("Today's Actions")
for action in briefing.actions:
    st.write(f"- {action}")

st.subheader("Best Candidates")
rows = []
for r in briefing.recommendations:
    tp = r.trade_plan
    cc = r.chart_context
    cat = r.catalyst_context
    fc = r.fundamental_context
    rows.append({
        "Symbol": r.asset.symbol,
        "Name": r.asset.name,
        "Score": r.atlas_score,
        "Confidence": r.score_breakdown.confidence_pct,
        "Verdict": r.verdict,
        "Strategy": r.strategy,
        "Setup": cc.setup_type if cc else "n/a",
        "Trend": cc.trend_status if cc else "n/a",
        "Fundamental": fc.overall_score if fc else None,
        "Catalyst": cat.score if cat else None,
        "Lead Catalyst": cat.primary_catalyst if cat else "n/a",
        "Entry": f"{tp.entry_low} - {tp.entry_high}" if tp else "n/a",
        "Stop": tp.stop_loss if tp else None,
        "TP1": tp.take_profit_1 if tp else None,
        "CRV": tp.reward_risk_ratio if tp else None,
        "Do Not Chase": tp.do_not_chase_above if tp else None,
        "Portfolio Fit": r.portfolio_fit.score,
        "Max EUR": r.portfolio_fit.max_position_eur,
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with st.expander("Portfolio risk flags"):
    if briefing.portfolio.risk_flags:
        for flag in briefing.portfolio.risk_flags:
            st.warning(flag)
    else:
        st.success("No portfolio risk flag from configured MVP rules.")

with st.expander("Data quality notes"):
    for note in briefing.data_quality_notes or ["No aggregated data quality notes."]:
        st.write(f"- {note}")
