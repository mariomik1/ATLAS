import streamlit as st
from atlas_core.orchestrator import AtlasOrchestrator

st.title("Technical MVP Status")
briefing = AtlasOrchestrator().daily_briefing()

st.success("Technical MVP block is wired: provider-ready data layer, daily candidates, portfolio, FIRE and journal/back-book.")
st.write("**MVP Version:**", briefing.technical_mvp_version)
st.write("**Headline:**", briefing.headline)
st.write("**Executive Summary**")
for item in briefing.executive_summary:
    st.write(f"- {item}")

st.write("**Safety Boundaries**")
for item in [
    "No broker connection.",
    "No automatic trading.",
    "No API keys in code.",
    "Live providers remain config-gated and cache/audit-wrapped.",
    "All recommendations are planning outputs requiring manual validation.",
]:
    st.write(f"- {item}")
