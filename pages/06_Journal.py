import pandas as pd
import streamlit as st
from atlas_core.engines.journal_engine import JournalEngine
from atlas_core.orchestrator import AtlasOrchestrator

st.title("Journal & Back-Book")
st.caption("Technical MVP: stores Atlas recommendations for later outcome tracking. It does not place trades.")

orchestrator = AtlasOrchestrator()
journal = JournalEngine()

col1, col2 = st.columns(2)
if col1.button("Append today's recommendations to journal"):
    path = orchestrator.append_daily_recommendations_to_journal()
    st.success(f"Saved to {path}")

summary = journal.summarize_recommendations()
col2.metric("Stored Records", summary.get("count", 0))
if summary.get("count", 0):
    st.write(summary)

rows = journal.read_recommendations(limit=200)
if rows:
    st.subheader("Latest Records")
    compact = []
    for row in rows[-50:]:
        compact.append({
            "Created": row.get("created_at"),
            "Symbol": row.get("symbol"),
            "Score": row.get("atlas_score"),
            "Verdict": row.get("verdict"),
            "Strategy": row.get("strategy"),
            "Entry": row.get("entry"),
            "Stop": row.get("stop_loss"),
            "TP": row.get("take_profit"),
            "Status": row.get("status"),
        })
    st.dataframe(pd.DataFrame(compact), use_container_width=True, hide_index=True)
    with st.expander("Raw latest record"):
        st.json(rows[-1])
else:
    st.info("No journal records yet. Add today's recommendations when ready.")
