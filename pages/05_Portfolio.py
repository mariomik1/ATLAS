import pandas as pd
import streamlit as st
from atlas_core.orchestrator import AtlasOrchestrator

st.title("Portfolio")
briefing = AtlasOrchestrator().daily_briefing()
p = briefing.portfolio

cols = st.columns(5)
cols[0].metric("Cash", f"EUR {p.cash_eur:,.0f}", f"{p.cash_pct:.1f}%")
cols[1].metric("Invested", f"EUR {p.invested_eur:,.0f}")
cols[2].metric("Tracked", f"EUR {p.total_tracked_eur:,.0f}")
cols[3].metric("Satellite Cap", f"EUR {p.satellite_max_eur:,.0f}")
cols[4].metric("Cash Range", f"EUR {p.target_cash_min_eur:,.0f}-{p.target_cash_max_eur:,.0f}")

st.subheader("Positions")
st.dataframe(pd.DataFrame([pos.model_dump() for pos in p.positions]), use_container_width=True, hide_index=True)

st.subheader("Exposure")
col1, col2, col3 = st.columns(3)
col1.write("**Asset Classes**")
col1.json(p.exposure_by_asset_class)
col2.write("**Sectors**")
col2.json(p.exposure_by_sector)
col3.write("**Themes**")
col3.json(p.exposure_by_theme)

st.subheader("Advisory Actions")
for action in p.advisory_actions:
    st.write(f"- {action}")

st.subheader("Risk Flags")
if p.risk_flags:
    for flag in p.risk_flags:
        st.warning(flag)
else:
    st.success("No portfolio risk flags from current MVP rules.")
