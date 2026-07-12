import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.title("Chart Engine")
st.caption("Sprint 6A asset-level OHLCV analysis: EMA20, EMA50, SMA200, RSI, ATR, support/resistance, setup classification and provider data quality.")

briefing = AtlasOrchestrator().daily_briefing()
rows = []
for rec in briefing.recommendations:
    cc = rec.chart_context
    if cc:
        rows.append(
            {
                "Symbol": rec.asset.symbol,
                "Setup": cc.setup_type,
                "Trend": cc.trend_status,
                "Structure": cc.market_structure,
                "Price": cc.current_price,
                "EMA20": cc.ema_20,
                "EMA50": cc.ema_50,
                "SMA200": cc.sma_200,
                "RSI14": cc.rsi_14,
                "ATR%": cc.atr_pct,
                "Support 1": cc.support_1,
                "Resistance 1": cc.resistance_1,
                "Chart Score": cc.score,
                "Data Provider": cc.data_quality.provider,
                "Data Quality": cc.data_quality.level,
            }
        )

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

selected = st.selectbox("Inspect symbol", [r.asset.symbol for r in briefing.recommendations])
rec = next((r for r in briefing.recommendations if r.asset.symbol == selected), None)
if rec and rec.chart_context:
    st.subheader(f"{selected} chart reasons")
    for reason in rec.chart_context.reasons:
        st.write(f"- {reason}")
    if rec.chart_context.risks:
        st.subheader("Chart risks")
        for risk in rec.chart_context.risks:
            st.warning(risk)
    st.subheader("Raw chart context")
    st.json(rec.chart_context.model_dump(mode="json"))
