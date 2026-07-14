from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.ui.theme import candidate_card, hero, inject_atlas_theme, metric_card, section


st.set_page_config(
    page_title="Daily Candidates",
    page_icon="🎯",
    layout="wide",
)

inject_atlas_theme()


WATCHLIST = ["V", "CRWD", "NVDA", "XLE", "MSFT"]


def get_payloads(symbols: list[str]) -> list[dict[str, Any]]:
    orchestrator = AtlasOrchestrator()
    payloads: list[dict[str, Any]] = []

    for symbol in symbols:
        try:
            rec = orchestrator.analyze_query(symbol)
            payloads.append(rec.model_dump(mode="json"))
        except Exception as exc:
            payloads.append(
                {
                    "asset": {"symbol": symbol},
                    "recommendation": "neutral",
                    "data_quality": {"level": "error"},
                    "error": str(exc),
                }
            )

    return payloads


def symbol_of(payload: dict[str, Any]) -> str:
    return payload.get("asset", {}).get("symbol", "UNKNOWN")


def status_of(payload: dict[str, Any]) -> str:
    return str(payload.get("recommendation", "neutral")).lower()


def quality_of(payload: dict[str, Any]) -> str:
    return payload.get("data_quality", {}).get("level", "unknown")


def score_of(payload: dict[str, Any]) -> Any:
    atlas_score = payload.get("atlas_score", payload.get("score", "n/a"))
    if isinstance(atlas_score, dict):
        return atlas_score.get("total_score", atlas_score.get("score", "n/a"))
    return atlas_score


def numeric_score(payload: dict[str, Any]) -> float:
    try:
        return float(score_of(payload))
    except Exception:
        return 0.0


def entry_of(payload: dict[str, Any]) -> str:
    trade = payload.get("trade_plan", {})
    low = trade.get("entry_low", "n/a")
    high = trade.get("entry_high", "n/a")
    return f"{low} – {high}"


def stop_of(payload: dict[str, Any]) -> Any:
    return payload.get("trade_plan", {}).get("stop_loss", "n/a")


def target_of(payload: dict[str, Any]) -> Any:
    trade = payload.get("trade_plan", {})
    return trade.get("take_profit", trade.get("target_price", "n/a"))


def decision_bucket(status: str) -> str:
    if status == "buy":
        return "Buy"
    if status == "watch":
        return "Watch"
    if status == "avoid":
        return "Avoid"
    return "Neutral"


payloads = sorted(get_payloads(WATCHLIST), key=numeric_score, reverse=True)

buy_payloads = [p for p in payloads if status_of(p) == "buy"]
watch_payloads = [p for p in payloads if status_of(p) == "watch"]
avoid_payloads = [p for p in payloads if status_of(p) == "avoid"]
other_payloads = [p for p in payloads if status_of(p) not in {"buy", "watch", "avoid"}]

hero(
    title="Opportunity Radar",
    subtitle=(
        "Die tägliche Kandidatenliste als Entscheidungsradar: Welche Assets sind heute handlungsfähig, "
        "welche gehören auf die Watchlist und welche sollte Atlas bewusst nicht jagen?"
    ),
    kicker="ATLAS · Daily Candidates",
)

a, b, c, d = st.columns(4)

with a:
    metric_card("Buy", str(len(buy_payloads)), "Handlungsfähige Setups mit positivem Atlas-Signal.", strong=len(buy_payloads) > 0)

with b:
    metric_card("Watch", str(len(watch_payloads)), "Interessant, aber noch nicht aggressiv verfolgen.")

with c:
    metric_card("Avoid", str(len(avoid_payloads)), "Nicht nachlaufen oder Risiko/Preis nicht attraktiv.")

with d:
    top_symbol = symbol_of(payloads[0]) if payloads else "n/a"
    metric_card("Top Candidate", top_symbol, "Höchster Atlas Score im aktuellen Lauf.", strong=True)

section("Top Ranked Candidates")

if payloads:
    cols = st.columns(3)
    for index, payload in enumerate(payloads):
        with cols[index % 3]:
            candidate_card(
                symbol=symbol_of(payload),
                status=status_of(payload),
                score=score_of(payload),
                entry=entry_of(payload),
                note=f"Data quality: {quality_of(payload)}",
            )
else:
    st.warning("Keine Kandidaten verfügbar.")

section("Decision Buckets")

buy_col, watch_col, avoid_col = st.columns(3)

with buy_col:
    metric_card("Buy Zone", str(len(buy_payloads)), "Nur prüfen, wenn Entry-Zone, Positionsgröße und Portfolio-Fit passen.", strong=len(buy_payloads) > 0)
    for payload in buy_payloads:
        candidate_card(symbol_of(payload), status_of(payload), score_of(payload), entry_of(payload), f"Stop: {stop_of(payload)} · Target: {target_of(payload)}")

with watch_col:
    metric_card("Watch Zone", str(len(watch_payloads)), "Gute Kandidaten, aber Timing, Bewertung oder Risiko noch nicht optimal.")
    for payload in watch_payloads:
        candidate_card(symbol_of(payload), status_of(payload), score_of(payload), entry_of(payload), f"Stop: {stop_of(payload)} · Target: {target_of(payload)}")

with avoid_col:
    metric_card("Avoid Zone", str(len(avoid_payloads)), "Kein FOMO. Atlas schützt vor schlechten Einstiegen.")
    for payload in avoid_payloads:
        candidate_card(symbol_of(payload), status_of(payload), score_of(payload), entry_of(payload), f"Stop: {stop_of(payload)} · Target: {target_of(payload)}")

if other_payloads:
    section("Other / Neutral")
    cols = st.columns(3)
    for index, payload in enumerate(other_payloads):
        with cols[index % 3]:
            candidate_card(symbol_of(payload), status_of(payload), score_of(payload), entry_of(payload), f"Data quality: {quality_of(payload)}")

section("Candidate Table")

rows = []
for payload in payloads:
    rows.append(
        {
            "Symbol": symbol_of(payload),
            "Decision": decision_bucket(status_of(payload)),
            "Atlas Score": score_of(payload),
            "Entry Zone": entry_of(payload),
            "Stop": stop_of(payload),
            "Target": target_of(payload),
            "Data Quality": quality_of(payload),
        }
    )

if rows:
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
else:
    st.info("Noch keine Tabelle verfügbar.")

section("Operating Rule")

if buy_payloads:
    st.success(
        "Mindestens ein Kandidat steht in der Buy-Zone. Nächster Schritt: Back Book öffnen, Chart prüfen, Positionsgröße definieren und Portfolio-Fit bewerten."
    )
elif watch_payloads:
    st.info(
        "Heute dominiert Watchlist-Logik. Der richtige Move kann sein: beobachten, Alerts setzen und nicht hinterherlaufen."
    )
else:
    st.warning(
        "Heute gibt es kein attraktives Setup. Atlas sagt: Cash ist auch eine Position."
    )
