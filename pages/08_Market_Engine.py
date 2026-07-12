import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.title("Market Engine")
briefing = AtlasOrchestrator().daily_briefing()
market = briefing.market

col1, col2, col3 = st.columns(3)
col1.metric("Regime", market.regime)
col2.metric("Score", f"{market.score:.0f}/100")
col3.metric("Position Multiplier", f"{market.position_size_multiplier:.2f}x")
st.write(market.summary)

st.subheader("Component Scores")
st.dataframe(
    pd.DataFrame([{"Component": k, "Score": v} for k, v in market.component_scores.items()]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Benchmark Signals")
st.dataframe(
    pd.DataFrame([indicator.model_dump(mode="json") for indicator in market.indicators]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Data Quality")
st.json(market.data_quality.model_dump(mode="json"))
