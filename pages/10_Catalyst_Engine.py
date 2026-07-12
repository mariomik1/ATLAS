import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.title("Catalyst Engine")
st.caption("Sprint 3: normalized news, events, relevance, sentiment and catalyst risk flags.")

orch = AtlasOrchestrator()
briefing = orch.daily_briefing()

rows = []
for rec in briefing.recommendations:
    cat = rec.catalyst_context
    rows.append(
        {
            "Symbol": rec.asset.symbol,
            "Name": rec.asset.name,
            "Catalyst Score": cat.score if cat else None,
            "Type": cat.catalyst_type if cat else "n/a",
            "News Count": cat.news_count if cat else 0,
            "Avg Sentiment": cat.average_sentiment if cat else None,
            "Avg Relevance": cat.average_relevance if cat else None,
            "Primary Catalyst": cat.primary_catalyst if cat else None,
            "Data Quality": cat.data_quality.level if cat else "missing",
        }
    )

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

symbol = st.selectbox("Inspect symbol", [rec.asset.symbol for rec in briefing.recommendations])
rec = next((r for r in briefing.recommendations if r.asset.symbol == symbol), None)
if rec and rec.catalyst_context:
    cat = rec.catalyst_context
    st.subheader(f"{symbol} Catalyst Back-Book")
    st.write("**Reasons**")
    for reason in cat.reasons:
        st.write(f"- {reason}")
    st.write("**Risks**")
    for risk in cat.risks:
        st.write(f"- {risk}")
    st.write("**News**")
    for news in cat.news:
        st.write(f"- **{news.title}**")
        st.caption(f"{news.published_at} | {news.source} | relevance={news.relevance_score} | sentiment={news.sentiment_score}")
        if news.summary:
            st.write(news.summary)
    st.write("**Events**")
    if cat.upcoming_events:
        for event in cat.upcoming_events:
            st.write(f"- {event.event_date}: {event.description} ({event.event_type}, {event.importance})")
    else:
        st.caption("No configured events for this symbol.")
    with st.expander("Full catalyst JSON"):
        st.json(cat.model_dump(mode="json"))
