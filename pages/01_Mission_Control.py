from __future__ import annotations

from typing import Any

import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.ui.theme import candidate_card, hero, inject_atlas_theme, metric_card, progress, section


st.set_page_config(
    page_title="Mission Control",
    page_icon="🧭",
    layout="wide",
)

inject_atlas_theme()


def get_recommendations(symbols: list[str]) -> list[dict[str, Any]]:
    orchestrator = AtlasOrchestrator()
    results: list[dict[str, Any]] = []

    for symbol in symbols:
        try:
            rec = orchestrator.analyze_query(symbol)
            payload = rec.model_dump(mode="json")
            results.append(payload)
        except Exception as exc:
            results.append(
                {
                    "asset": {"symbol": symbol},
                    "recommendation": "neutral",
                    "error": str(exc),
                    "data_quality": {"level": "error"},
                }
            )

    return results


def extract_score(payload: dict[str, Any]) -> Any:
    atlas_score = payload.get("atlas_score", payload.get("score", "n/a"))
    if isinstance(atlas_score, dict):
        return atlas_score.get("total_score", atlas_score.get("score", "n/a"))
    return atlas_score


def extract_entry(payload: dict[str, Any]) -> str:
    trade = payload.get("trade_plan", {})
    entry_low = trade.get("entry_low", "n/a")
    entry_high = trade.get("entry_high", "n/a")
    return f"{entry_low} – {entry_high}"


def extract_symbol(payload: dict[str, Any]) -> str:
    return payload.get("asset", {}).get("symbol", "UNKNOWN")


def extract_status(payload: dict[str, Any]) -> str:
    return payload.get("recommendation", "neutral")


def extract_quality(payload: dict[str, Any]) -> str:
    return payload.get("data_quality", {}).get("level", "unknown")


symbols = ["V", "CRWD", "NVDA", "XLE", "MSFT"]
recommendations = get_recommendations(symbols)

buy_count = sum(1 for r in recommendations if extract_status(r).lower() == "buy")
watch_count = sum(1 for r in recommendations if extract_status(r).lower() == "watch")
avoid_count = sum(1 for r in recommendations if extract_status(r).lower() == "avoid")
delayed_count = sum(1 for r in recommendations if extract_quality(r).lower() == "delayed")

hero(
    title="Mission Control",
    subtitle=(
        "Der tägliche Atlas-Entscheidungsraum: Was ist heute attraktiv, was ist nur Watchlist, "
        "was sollte nicht gejagt werden — und wie passt alles zu Vermögensaufbau und finanzieller Freiheit?"
    ),
    kicker="ATLAS · Daily Decision Cockpit",
)

top_left, top_mid, top_right, top_far = st.columns(4)

with top_left:
    metric_card(
        "Actionable Today",
        str(buy_count),
        "Kandidaten mit Buy-Signal im aktuellen Atlas-Lauf.",
        strong=buy_count > 0,
    )

with top_mid:
    metric_card(
        "Watchlist",
        str(watch_count),
        "Interessant, aber noch nicht zwingend handlungsreif.",
    )

with top_right:
    metric_card(
        "Avoid / No Chase",
        str(avoid_count),
        "Atlas warnt vor schwachem Setup, Preis oder Risiko-Fit.",
    )

with top_far:
    data_mode = "Delayed" if delayed_count else "Sample"
    metric_card(
        "Data Mode",
        data_mode,
        "Live-/Delayed-Daten, sofern verfügbar; sonst Sample-/Fallback-Daten.",
    )

section("Today’s Decision Board")

if recommendations:
    cols = st.columns(3)
    for index, payload in enumerate(recommendations):
        symbol = extract_symbol(payload)
        status = extract_status(payload)
        score = extract_score(payload)
        entry = extract_entry(payload)
        quality = extract_quality(payload)

        with cols[index % 3]:
            candidate_card(
                symbol=symbol,
                status=status,
                score=score,
                entry=entry,
                note=f"Data quality: {quality}",
            )
else:
    st.warning("Keine Empfehlungen verfügbar.")

section("Portfolio & FIRE Lens")

a, b, c = st.columns(3)

with a:
    progress(
        "Decision Discipline",
        72,
        "Atlas priorisiert Setups, Risiko und Entry-Zonen statt spontaner Bauchentscheidungen.",
    )

with b:
    progress(
        "Live Data Foundation",
        55,
        "yfinance/delayed ist aktiv; Fundamentals und News/Catalysts folgen als nächste Datenebenen.",
    )

with c:
    progress(
        "Financial Freedom Fit",
        46,
        "Die persönliche Vermögens- und FIRE-Logik wird nach dem UI-Redesign weiter vertieft.",
    )

section("Today’s Operating Message")

if buy_count > 0:
    st.success(
        "Atlas sieht heute mindestens ein potenziell handlungsfähiges Setup. Trotzdem gilt: Entry-Zone, Positionsgröße und Portfolio-Fit prüfen."
    )
elif watch_count > 0:
    st.info(
        "Heute dominiert Watchlist-Logik. Atlas sieht interessante Kandidaten, aber kein klares Signal für aggressives Handeln."
    )
else:
    st.warning(
        "Heute ist eher Defensive angesagt. Kein Setup rechtfertigt blindes Nachlaufen."
    )

section("Next Improvement Layer")

x, y, z = st.columns(3)

with x:
    metric_card(
        "Fundamentals",
        "Next",
        "FMP-Anbindung für Profile, Ratios, Wachstum und Unternehmensqualität.",
    )

with y:
    metric_card(
        "News/Catalysts",
        "Next",
        "Echte Nachrichtenlage je Symbol statt nur technischer Betrachtung.",
    )

with z:
    metric_card(
        "Personal Portfolio",
        "Next",
        "Deine realen Positionen, Cash, Sparrate und FIRE-Ziele als Entscheidungsfilter.",
    )
