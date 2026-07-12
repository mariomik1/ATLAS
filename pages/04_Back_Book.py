import streamlit as st
from atlas_core.orchestrator import AtlasOrchestrator

st.title("Back-Book")
st.info("Sprint 0 stores back-book snapshots in each recommendation. Persistent tracking comes in a later sprint.")
briefing = AtlasOrchestrator().daily_briefing()
for rec in briefing.recommendations:
    with st.expander(rec.asset.symbol):
        st.json(rec.back_book_summary)
