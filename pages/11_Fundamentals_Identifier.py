import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.title("Fundamentals + Identifier Search")
st.caption("Sprint 6B: ranked ticker/name/ISIN/WKN-style search, FMP/OpenFIGI-ready providers and normalized fundamental contexts.")

orchestrator = AtlasOrchestrator()
query = st.text_input("Identifier query", value="Visa")

if query:
    result = orchestrator.search_assets(query)
    st.subheader("Matches")
    if not result or not result.matches:
        st.warning("No match found in local sample identifier master.")
    else:
        st.dataframe(
            pd.DataFrame([m.model_dump(mode="json") for m in result.matches])[
                ["symbol", "name", "asset_class", "isin", "wkn", "match_type", "confidence", "provider"]
            ],
            use_container_width=True,
            hide_index=True,
        )
        symbol = result.matches[0].symbol
        rec = orchestrator.analyze_query(symbol)
        st.subheader(f"Fundamental context: {symbol}")
        if rec is None or rec.fundamental_context is None:
            st.info("No normalized fundamental context is available for this symbol.")
        else:
            context = rec.fundamental_context
            cols = st.columns(6)
            cols[0].metric("Overall", context.overall_score)
            cols[1].metric("Class", context.classification)
            cols[2].metric("Growth", context.growth_score)
            cols[3].metric("Profitability", context.profitability_score)
            cols[4].metric("Valuation", context.valuation_score)
            cols[5].metric("Balance", context.balance_sheet_score)

            st.write("### Profile")
            if context.profile:
                profile = context.profile.model_dump(mode="json")
                st.dataframe(pd.DataFrame([profile]).T.rename(columns={0: "Value"}), use_container_width=True)

            st.write("### Metrics")
            if context.metrics:
                st.dataframe(pd.DataFrame([context.metrics.model_dump(mode="json")]).T.rename(columns={0: "Value"}), use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.write("### Reasons")
                for item in context.reasons:
                    st.write(f"- {item}")
            with col_b:
                st.write("### Risks")
                for item in context.risks:
                    st.write(f"- {item}")
            with st.expander("Raw recommendation JSON"):
                st.json(rec.model_dump(mode="json"))
