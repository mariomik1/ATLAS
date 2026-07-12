import pandas as pd
import streamlit as st
from atlas_core.config_loader import load_all_configs
from atlas_core.providers.status import ProviderRegistry

st.title("Settings")
configs = load_all_configs()
registry = ProviderRegistry(configs["settings"])

st.subheader("Provider Summary")
summary = registry.summary()
st.write(f"Ready providers: **{summary.ready}/{summary.total}**")
st.dataframe(
    pd.DataFrame([status.model_dump() for status in summary.statuses]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Raw Config")
st.json(configs)
