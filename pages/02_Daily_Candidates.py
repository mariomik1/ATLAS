import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.title("Daily Candidates")
briefing = AtlasOrchestrator().daily_briefing()
if briefing.market_catalysts:
    st.caption(
        f"Market regime: {briefing.market.regime} | Score: {briefing.market.score:.0f}/100 | "
        f"Market catalysts: {briefing.market_catalysts.score:.0f}/100"
    )
else:
    st.caption(f"Market regime: {briefing.market.regime} | Score: {briefing.market.score:.0f}/100 | Market catalysts: n/a")

rows = []
for r in briefing.recommendations:
    tp = r.trade_plan
    cc = r.chart_context
    cat = r.catalyst_context
    fc = r.fundamental_context
    rows.append(
        {
            "Symbol": r.asset.symbol,
            "Name": r.asset.name,
            "Score": r.atlas_score,
            "Confidence": r.score_breakdown.confidence_pct,
            "Verdict": r.verdict,
            "Strategy": r.strategy,
            "Setup": cc.setup_type if cc else "n/a",
            "Trend": cc.trend_status if cc else "n/a",
            "RSI": cc.rsi_14 if cc else None,
            "ATR %": cc.atr_pct if cc else None,
            "Fundamental": fc.overall_score if fc else None,
            "Growth": fc.growth_score if fc else None,
            "Valuation": fc.valuation_score if fc else None,
            "Catalyst": cat.score if cat else None,
            "Sentiment": cat.average_sentiment if cat else None,
            "News": cat.news_count if cat else 0,
            "Risk News": cat.risk_flag_count if cat else 0,
            "Entry Low": tp.entry_low,
            "Entry High": tp.entry_high,
            "Do Not Chase": tp.do_not_chase_above,
            "Stop": tp.stop_loss,
            "TP1": tp.take_profit_1,
            "TP2": tp.take_profit_2,
            "CRV": tp.reward_risk_ratio,
            "Max EUR": r.portfolio_fit.max_position_eur,
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

selected = st.selectbox("Open back-book details", [r.asset.symbol for r in briefing.recommendations])
rec = next((r for r in briefing.recommendations if r.asset.symbol == selected), None)
if rec:
    st.subheader(f"{rec.asset.symbol} - {rec.asset.name}")
    st.write(rec.ai_statement)
    if rec.fundamental_context:
        st.write("**Fundamental Context**")
        st.json(rec.fundamental_context.model_dump(mode="json"))
    if rec.catalyst_context:
        st.write("**Catalyst Context**")
        st.json(rec.catalyst_context.model_dump(mode="json"))
    if rec.chart_context:
        st.write("**Chart Context**")
        st.json(rec.chart_context.model_dump(mode="json"))
    st.write("**Trade Plan Notes**")
    for note in rec.trade_plan.notes:
        st.write(f"- {note}")
    st.write("**Reasons**")
    for reason in rec.key_reasons:
        st.write(f"- {reason}")
    st.write("**Risks**")
    for risk in rec.key_risks:
        st.write(f"- {risk}")
    st.write("**Back-Book Snapshot**")
    st.json(rec.back_book_summary)
