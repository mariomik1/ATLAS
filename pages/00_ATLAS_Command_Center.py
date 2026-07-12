from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.ui.theme import candidate_card, hero, inject_atlas_theme, metric_card, progress, section


st.set_page_config(
    page_title="ATLAS Command Center",
    page_icon="🧭",
    layout="wide",
)

inject_atlas_theme()


def load_daily_export() -> dict[str, Any]:
    path = Path("data/exports/daily_briefing_sample.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def safe_candidates() -> list[Any]:
    symbols = ["V", "CRWD", "NVDA", "XLE", "MSFT"]
    recommendations = []
    orchestrator = AtlasOrchestrator()
    for symbol in symbols:
        try:
            recommendations.append(orchestrator.analyze_query(symbol))
        except Exception:
            continue
    return recommendations


hero(
    title="Atlas Command Center",
    subtitle=(
        "Dein privates Wealth Operating System: Marktregime, Chancen, Portfolio-Fit, "
        "FIRE-Fortschritt und nächste Entscheidungen in einem Cockpit."
    ),
    kicker="Sprint 11B · Visual System",
)

daily = load_daily_export()
recommendations = safe_candidates()

left, mid, right, far = st.columns(4)

with left:
    metric_card(
        "Market Mode",
        "Risk-aware",
        "Atlas bewertet Chancen im Kontext von Markt, Chart, Portfolio und Zielpfad.",
        strong=True,
    )

with mid:
    metric_card(
        "Data Mode",
        "Delayed / Sample",
        "yfinance ist vorbereitet; Sample- und Cache-Fallback bleiben aktiv.",
    )

with right:
    metric_card(
        "Decision Style",
        "Advisory",
        "Keine Broker-Anbindung, kein Auto-Trading, keine versteckten Orders.",
    )

with far:
    metric_card(
        "MVP Status",
        "Running",
        "Tests und Daily Snapshot wurden erfolgreich ausgeführt.",
    )

section("Today’s Opportunity Radar")

if recommendations:
    cols = st.columns(min(3, len(recommendations)))
    for index, rec in enumerate(recommendations[:6]):
        payload = rec.model_dump(mode="json")
        asset = payload.get("asset", {})
        trade = payload.get("trade_plan", {})
        symbol = asset.get("symbol", "UNKNOWN")
        status = payload.get("recommendation", "neutral")
        atlas_score = payload.get("atlas_score", payload.get("score", "n/a"))
        if isinstance(atlas_score, dict):
            score = atlas_score.get("total_score", atlas_score.get("score", "n/a"))
        else:
            score = atlas_score
        entry_low = trade.get("entry_low", "n/a")
        entry_high = trade.get("entry_high", "n/a")
        entry = f"{entry_low} – {entry_high}"
        data_quality = payload.get("data_quality", {}).get("level", "unknown")

        with cols[index % len(cols)]:
            candidate_card(
                symbol=symbol,
                status=status,
                score=score,
                entry=entry,
                note=f"Data quality: {data_quality}",
            )
else:
    st.info("Noch keine Kandidaten verfügbar. Führe python scripts/run_daily_snapshot.py aus.")

section("Wealth Mission")

a, b, c = st.columns(3)

with a:
    progress(
        "FIRE System Readiness",
        64,
        "Technisches MVP steht; echte persönliche Vermögensdaten folgen im nächsten Ausbauschritt.",
    )

with b:
    progress(
        "Live Data Readiness",
        48,
        "Kursdaten via yfinance laufen; Fundamentals und News kommen danach.",
    )

with c:
    progress(
        "Product Experience",
        36,
        "Visual System gestartet; jetzt werden die Kernseiten schrittweise ersetzt.",
    )

section("Current Daily Briefing Export")

if daily:
    st.markdown('<div class="atlas-card">', unsafe_allow_html=True)
    st.json(daily)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("Kein Daily Export gefunden. Bitte python scripts/run_daily_snapshot.py ausführen.")

section("Next Build Priorities")

p1, p2, p3 = st.columns(3)

with p1:
    metric_card(
        "1 · Mission Control",
        "Redesign",
        "Die bestehende Startseite wird als Premium-Dashboard neu aufgebaut.",
    )

with p2:
    metric_card(
        "2 · Live Fundamentals",
        "FMP",
        "Company Profile, Ratios, Growth und Estimates mit API-Key.",
    )

with p3:
    metric_card(
        "3 · Personal Wealth",
        "Portfolio + FIRE",
        "Deine echten Kapital-, Budget- und Portfolio-Daten werden integriert.",
    )
