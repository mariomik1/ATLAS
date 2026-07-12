import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator

st.title("Screener / Search")
st.caption("Search by ticker, name, ISIN or WKN. Sprint 4 adds identifier search and normalized fundamentals.")
orchestrator = AtlasOrchestrator()
query = st.text_input("Search", value="MSFT")
if query:
    matches = orchestrator.search_assets(query)
    if matches and matches.matches:
        with st.expander("Identifier matches", expanded=True):
            st.dataframe(
                pd.DataFrame([m.model_dump(mode="json") for m in matches.matches])[
                    ["symbol", "name", "asset_class", "isin", "wkn", "match_type", "confidence", "provider"]
                ],
                use_container_width=True,
                hide_index=True,
            )
    rec = orchestrator.analyze_query(query)
    if rec is None:
        st.warning("No asset found in the current Sprint 4 sample identifier master.")
    else:
        tp = rec.trade_plan
        cc = rec.chart_context
        cat = rec.catalyst_context
        fc = rec.fundamental_context
        st.subheader(f"{rec.asset.symbol} - {rec.asset.name}")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Atlas Score", rec.atlas_score)
        col2.metric("Verdict", rec.verdict)
        col3.metric("Portfolio Fit", rec.portfolio_fit.score)
        col4.metric("Market", rec.market_snapshot.regime)
        col5.metric("Fundamental", f"{fc.overall_score:.0f}/100" if fc else "n/a")
        col6.metric("Catalyst", f"{cat.score:.0f}/100" if cat else "n/a")
        st.write(rec.ai_statement)

        if fc:
            st.subheader("Fundamental Context")
            f1, f2, f3, f4, f5, f6 = st.columns(6)
            f1.metric("Overall", fc.overall_score)
            f2.metric("Class", fc.classification)
            f3.metric("Growth", fc.growth_score)
            f4.metric("Profitability", fc.profitability_score)
            f5.metric("Valuation", fc.valuation_score)
            f6.metric("Balance", fc.balance_sheet_score)
            if fc.profile:
                st.write(f"Sector: **{fc.profile.sector}** | Industry: **{fc.profile.industry}** | Currency: **{fc.profile.currency}**")
            if fc.metrics:
                st.write(
                    f"Market Cap: **{fc.metrics.market_cap_usd} USD** | Forward P/E: **{fc.metrics.forward_pe}** | "
                    f"PEG: **{fc.metrics.peg_ratio}** | ROIC: **{fc.metrics.roic_pct}%** | Debt/Equity: **{fc.metrics.debt_to_equity}**"
                )
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Fundamental Reasons**")
                for item in fc.reasons:
                    st.write(f"- {item}")
            with col_b:
                st.write("**Fundamental Risks**")
                for item in fc.risks:
                    st.write(f"- {item}")

        if cat:
            st.subheader("Catalyst Context")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Catalyst Score", cat.score)
            c2.metric("Type", cat.catalyst_type)
            c3.metric("News", cat.news_count)
            c4.metric("Avg Sentiment", cat.average_sentiment)
            st.write(f"Primary catalyst: **{cat.primary_catalyst or 'n/a'}**")
            with st.expander("News and events"):
                for news in cat.news:
                    st.write(f"- **{news.title}** | source={news.source} | relevance={news.relevance_score} | sentiment={news.sentiment_score}")
                    if news.summary:
                        st.caption(news.summary)
                if cat.upcoming_events:
                    st.write("Events")
                    for event in cat.upcoming_events:
                        st.write(f"- {event.event_date}: {event.description} ({event.importance})")

        if cc:
            st.subheader("Chart Context")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Setup", cc.setup_type)
            c2.metric("Trend", cc.trend_status)
            c3.metric("RSI", cc.rsi_14)
            c4.metric("ATR %", cc.atr_pct)
            c5.metric("Chart Score", cc.score)
            st.write(f"EMA20 / EMA50 / SMA200: **{cc.ema_20} / {cc.ema_50} / {cc.sma_200}**")
            st.write(f"Support: **{cc.support_1} / {cc.support_2}** | Resistance: **{cc.resistance_1} / {cc.resistance_2}**")
        if tp:
            st.subheader("Trade Plan")
            st.write(f"Entry: **{tp.entry_low} - {tp.entry_high} {tp.currency}**")
            st.write(f"Stop-loss: **{tp.stop_loss} {tp.currency}**")
            st.write(f"Take-profit: **{tp.take_profit_1} / {tp.take_profit_2} / {tp.take_profit_3} {tp.currency}**")
            st.write(f"Do not chase above: **{tp.do_not_chase_above} {tp.currency}**")
            st.write(f"CRV: **{tp.reward_risk_ratio}:1**")
            with st.expander("Trade plan notes"):
                for note in tp.notes:
                    st.write(f"- {note}")
        with st.expander("Full recommendation JSON"):
            st.json(rec.model_dump(mode="json"))
