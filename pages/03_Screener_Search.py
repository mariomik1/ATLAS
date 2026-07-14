from __future__ import annotations

from typing import Any

import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.screener.quote_context import get_quote_context
from atlas_core.screener.trade_setup import TradeSetup, build_trade_setup
from atlas_core.ui.theme import (
    candidate_card,
    hero,
    inject_atlas_theme,
    metric_card,
    premium_table,
    score_explanation_card,
    section,
)


MAX_SYMBOLS = 12
PLACEHOLDER_SYMBOLS = "z. B. AAPL, MSFT, NVDA, V, JEPQ, QQQ"


def normalize_symbols(raw: str) -> list[str]:
    cleaned = raw.replace(";", ",").replace("\n", ",")
    symbols = []
    for item in cleaned.split(","):
        symbol = item.strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols[:MAX_SYMBOLS]


@st.cache_data(show_spinner=False, ttl=300)
def analyze_symbol(symbol: str) -> dict[str, Any]:
    return AtlasOrchestrator().analyze_query(symbol).model_dump(mode="json")


def analyze_symbols(symbols: list[str]) -> list[dict[str, Any]]:
    payloads = []
    for symbol in symbols:
        try:
            payloads.append(analyze_symbol(symbol))
        except Exception as exc:
            payloads.append(
                {
                    "asset": {"symbol": symbol},
                    "symbol": symbol,
                    "status": "error",
                    "atlas_score": 0,
                    "data_quality": {"level": "error"},
                    "error": str(exc),
                }
            )
    return payloads


def symbol_of(payload: dict[str, Any]) -> str:
    asset = payload.get("asset", {}) or {}
    return str(payload.get("symbol") or asset.get("symbol") or "n/a").upper()


def status_of(payload: dict[str, Any]) -> str:
    return str(payload.get("status", payload.get("recommendation", "neutral"))).lower()


def quality_of(payload: dict[str, Any]) -> str:
    quality = payload.get("data_quality", "unknown")
    if isinstance(quality, dict):
        return str(quality.get("level", "unknown"))
    return str(quality)


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


def bucket(status: str) -> str:
    if status == "buy":
        return "Buy"
    if status == "watch":
        return "Watch"
    if status == "avoid":
        return "Avoid"
    if status == "error":
        return "Error"
    return "Neutral"


def setup_for(payload: dict[str, Any]) -> TradeSetup:
    quote = get_quote_context(payload)
    return build_trade_setup(payload, quote)


def setup_badge(setup: TradeSetup) -> str:
    if setup.setup_source == "fallback":
        return f"{setup.setup_type} · Fallback"
    return setup.setup_type


st.set_page_config(page_title="Screener Search", page_icon="🔎", layout="wide")
inject_atlas_theme()

hero(
    "Screener Search",
    (
        "ATLAS SCREENER · Prüfe Aktien und ETFs auf Score, Kurskontext, Entry-Zone, "
        "Stop, Target und Swing-Horizont. Atlas trennt Engine-Setups und Fallback-Setups sichtbar."
    ),
)

left, right = st.columns([2, 1])

with left:
    raw_symbols = st.text_area(
        "Ticker eingeben",
        value="",
        placeholder=PLACEHOLDER_SYMBOLS,
        help=f"Mehrere Symbole mit Komma, Semikolon oder Zeilenumbruch trennen. Maximal {MAX_SYMBOLS} Symbole pro Lauf.",
        height=110,
    )

with right:
    metric_card(
        "Search Mode",
        "Manual",
        "Live/delayed quote context via yfinance where available.",
    )

symbols = normalize_symbols(raw_symbols)

run_search = st.button("Atlas Search starten", type="primary")

if not run_search and not symbols:
    st.info("Gib Ticker ein und starte die Suche. Beispiel: AAPL, MSFT, NVDA, V, JEPQ, QQQ")
    st.stop()

if not symbols:
    st.warning("Bitte mindestens einen Ticker eingeben.")
    st.stop()

with st.spinner("Atlas analysiert die Symbole..."):
    payloads = analyze_symbols(symbols)
    setups = {symbol_of(payload): setup_for(payload) for payload in payloads}

payloads = sorted(payloads, key=numeric_score, reverse=True)

buy_count = sum(1 for payload in payloads if status_of(payload) == "buy")
watch_count = sum(1 for payload in payloads if status_of(payload) == "watch")
error_count = sum(1 for payload in payloads if status_of(payload) == "error")
fallback_count = sum(
    1
    for payload in payloads
    if setups[symbol_of(payload)].setup_source == "fallback"
)

section("Search Summary")
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Symbols", len(payloads), "Analyzed in this run.")
with c2:
    metric_card("Buy", buy_count, "Potential action candidates.")
with c3:
    metric_card("Watch", watch_count, "Interesting, but not yet decisive.")
with c4:
    metric_card("Fallback Setups", fallback_count, "Generated from quote context.")

section("Ranked Search Results")

for payload in payloads:
    symbol = symbol_of(payload)
    setup = setups[symbol]
    status = status_of(payload)
    quality = quality_of(payload)
    score = score_of(payload)

    candidate_card(
        symbol=symbol,
        status=status,
        score=score,
        entry=setup.entry_zone,
        note=(
            f"{setup_badge(setup)} · Target {setup.target} {setup.currency} · "
            f"Horizon {setup.target_horizon} · {quality}"
        ),
    )

section("Score Transparency")

selected_symbol = st.selectbox(
    "Symbol für Score-Erklärung auswählen",
    options=[symbol_of(payload) for payload in payloads],
    index=0,
)

selected_payload = next(payload for payload in payloads if symbol_of(payload) == selected_symbol)
selected_setup = setups[selected_symbol]

score_explanation_card(
    symbol=selected_symbol,
    score=score_of(selected_payload),
    status=status_of(selected_payload),
    data_quality=quality_of(selected_payload),
    entry_zone=selected_setup.entry_zone,
    stop=selected_setup.stop,
    target=selected_setup.target,
    current_price=selected_setup.current_price,
    currency=selected_setup.currency,
    exchange=selected_setup.exchange,
    target_horizon=selected_setup.target_horizon,
    setup_type=setup_badge(selected_setup),
    note=(
        f"Setup source: {selected_setup.setup_source}. {selected_setup.note} "
        "Der Horizont ist aktuell eine technische Swing-Schätzung und noch keine fundamentale Prognose."
    ),
)

section("Detailed Search Table")

rows = []
for payload in payloads:
    symbol = symbol_of(payload)
    setup = setups[symbol]

    rows.append(
        {
            "Symbol": symbol,
            "Status": bucket(status_of(payload)),
            "Score": score_of(payload),
            "Current Price": f"{setup.current_price} {setup.currency}",
            "Entry Zone": f"{setup.entry_zone} {setup.currency}",
            "Stop": f"{setup.stop} {setup.currency}",
            "Target": f"{setup.target} {setup.currency}",
            "Target Horizon": setup.target_horizon,
            "Setup Type": setup_badge(setup),
            "Exchange": setup.exchange,
            "Data Quality": quality_of(payload),
        }
    )

premium_table(rows)

section("Decision Guidance")

st.markdown(
    """
    **So ist die Seite aktuell zu lesen:**  
    Atlas zeigt dir pro Symbol eine technische Einschätzung mit Score, aktuellem Kurskontext,
    Entry-Zone, Stop, Target und Zeithorizont. Wenn die Engine keinen vollständigen Trade-Plan
    liefert, erzeugt Atlas ein klar markiertes Fallback-Setup.
    """
)

st.warning(
    "Fallback-Setups sind keine fundamentalen Kursziele. Sie dienen als technische MVP-Swing-Orientierung, "
    "bis Fundamentals, News, Portfolio-Fit und Risikomodell vollständig angebunden sind."
)

section("How to Use This Page")

st.markdown(
    """
    1. Gib mehrere Ticker ein, zum Beispiel `AAPL, MSFT, NVDA, QQQ, JEPQ`.
    2. Prüfe zuerst Score, Status und Setup Type.
    3. Öffne die Score Transparency für den wichtigsten Kandidaten.
    4. Achte besonders auf Fallback-Hinweise, Währung, Börsenplatz und Target-Horizont.
    5. Nutze Atlas als Entscheidungs-Cockpit, nicht als automatische Kaufempfehlung.
    """
)
