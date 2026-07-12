import pandas as pd
import streamlit as st

from atlas_core.config_loader import load_all_configs
from atlas_core.providers.status import ProviderRegistry

st.title("Provider Status")
st.caption("Sprint 6B: API-key readiness, cache status, audit logs and controlled yfinance/FMP/OpenFIGI activation.")

configs = load_all_configs()
registry = ProviderRegistry(configs["settings"])
summary = registry.summary()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Providers", summary.total)
col2.metric("Ready", summary.ready)
col3.metric("Missing Keys", summary.missing_keys)
col4.metric("Live Disabled", summary.disabled_live)

rows = []
for status in summary.statuses:
    rows.append(
        {
            "Role": status.role,
            "Provider": status.selected_provider,
            "Status": status.status,
            "Live Enabled": status.live_enabled,
            "Requires Key": status.requires_api_key,
            "Env Var": status.env_var or "-",
            "Key": status.masked_key,
            "TTL seconds": status.cache_ttl_seconds,
            "Data Quality Mode": status.data_quality_mode,
            "Notes": " | ".join(status.notes),
        }
    )

st.subheader("Provider Readiness")
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Cache")
st.json(registry.cache_stats())

st.subheader("Fetch Audit Log")
audit_rows = registry.audit_tail(limit=50)
if audit_rows:
    st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
else:
    st.info("No provider fetch/audit events recorded yet.")

with st.expander("Current provider configuration"):
    st.json(configs["settings"].get("provider_activation", {}))

st.warning(
    "Sprint 6B can perform controlled yfinance OHLCV, FMP fundamentals/identifier and OpenFIGI identifier fetches if explicitly enabled. Enable live providers only after API keys, "
    "provider terms, cache TTLs and data-quality rules are reviewed."
)
