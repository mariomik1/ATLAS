from __future__ import annotations

from typing import Any

import yfinance as yf
import streamlit as st

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.ui.theme import candidate_card, hero, inject_atlas_theme, metric_card, premium_table, score_explanation_card, section


st.set_page_config(
    page_title="Screener Search",
    page_icon="🔎",
    layout="wide",
)

inject_atlas_theme()


DEFAULT_SYMBOLS = ""


def normalize_symbols(raw: str) -> list[str]:
    symbols: list[str] = []
    for part in raw.replace("\n", ",").replace(";", ",").split(","):
        symbol = part.strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols[:12]


def analyze_symbols(symbols: list[str]) -> list[dict[str, Any]]:
    orchestrator = AtlasOrchestrator()
    results: list[dict[str, Any]] = []

    for symbol in symbols:
        try:
            rec = orchestrator.analyze_query(symbol)
            results.append(rec.model_dump(mode="json"))
        except Exception as exc:
            results.append(
                {
                    "asset": {"symbol": symbol},
                    "recommendation": "neutral",
                    "data_quality": {"level": "error"},
                    "error": str(exc),
                }
            )

    return results


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


def current_price_of(payload: dict[str, Any]) -> Any:
    candidates = [
        payload.get("current_price"),
        payload.get("last_price"),
        payload.get("price"),
        payload.get("asset", {}).get("current_price", "n/a"),
        payload.get("asset", {}).get("last_price", "n/a"),
        payload.get("market_data", {}).get("current_price", "n/a"),
        payload.get("market_data", {}).get("last_close", "n/a"),
        payload.get("quote", {}).get("price", "n/a"),
        payload.get("quote", {}).get("regular_market_price", "n/a"),
    ]
    for value in candidates:
        if value not in (None, "", "n/a"):
            return value
    return "n/a"


def currency_of(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("currency"),
        payload.get("asset", {}).get("currency"),
        payload.get("market_data", {}).get("currency"),
        payload.get("quote", {}).get("currency"),
    ]
    for value in candidates:
        if value not in (None, "", "n/a"):
            return str(value)
    return "USD"


def exchange_of(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("exchange"),
        payload.get("asset", {}).get("exchange"),
        payload.get("asset", {}).get("exchange_name"),
        payload.get("market_data", {}).get("exchange"),
        payload.get("quote", {}).get("exchange"),
        payload.get("quote", {}).get("full_exchange_name"),
    ]
    for value in candidates:
        if value not in (None, "", "n/a"):
            return str(value)
    return "yfinance / default listing"


def target_of(payload: dict[str, Any]) -> Any:
    trade = payload.get("trade_plan", {})

    explicit_target = (
        trade.get("take_profit")
        or trade.get("target_price")
        or trade.get("take_profit_price")
        or trade.get("tp")
    )
    if explicit_target not in (None, "", "n/a"):
        return explicit_target

    try:
        entry_low = float(trade.get("entry_low"))
        entry_high = float(trade.get("entry_high"))
        stop = float(trade.get("stop_loss"))

        entry_mid = (entry_low + entry_high) / 2
        risk = entry_mid - stop

        if risk <= 0:
            return "n/a"

        technical_target = entry_mid + (2 * risk)
        return round(technical_target, 2)
    except Exception:
        return "n/a"



def live_quote_context(symbol: str) -> dict[str, Any]:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        current_price = getattr(info, "last_price", None)
        currency = getattr(info, "currency", None)

        raw_info = {}
        try:
            raw_info = ticker.info or {}
        except Exception:
            raw_info = {}

        if current_price in (None, "", "n/a"):
            current_price = raw_info.get("currentPrice") or raw_info.get("regularMarketPrice") or raw_info.get("previousClose")

        if currency in (None, "", "n/a"):
            currency = raw_info.get("currency", "n/a")

        exchange = (
            raw_info.get("fullExchangeName")
            or raw_info.get("exchange")
            or raw_info.get("market")
            or "yfinance / default listing"
        )

        if isinstance(current_price, (int, float)):
            current_price = round(float(current_price), 2)

        return {
            "current_price": current_price if current_price not in (None, "") else "n/a",
            "currency": currency if currency not in (None, "") else "n/a",
            "exchange": exchange if exchange not in (None, "") else "yfinance / default listing",
        }
    except Exception:
        return {
            "current_price": "n/a",
            "currency": "n/a",
            "exchange": "yfinance / unavailable",
        }


def current_price_display(payload: dict[str, Any]) -> Any:
    symbol = symbol_of(payload)
    quote = live_quote_context(symbol)
    value = quote.get("current_price", "n/a")
    if value not in (None, "", "n/a"):
        return value
    return current_price_of(payload)


def currency_display(payload: dict[str, Any]) -> str:
    symbol = symbol_of(payload)
    quote = live_quote_context(symbol)
    value = quote.get("currency", "n/a")
    if value not in (None, "", "n/a"):
        return str(value)
    return currency_of(payload)


def exchange_display(payload: dict[str, Any]) -> str:
    symbol = symbol_of(payload)
    quote = live_quote_context(symbol)
    value = quote.get("exchange", "n/a")
    if value not in (None, "", "n/a"):
        return str(value)
    return exchange_of(payload)

def bucket(status: str) -> str:
    if status == "buy":
        return "Buy"
    if status == "watch":
        return "Watch"
    if status == "avoid":
        return "Avoid"
    return "Neutral"


hero(
    title="Screener Search",
    subtitle=(
        "Prüfe gezielt Aktien, ETFs oder Ideen: Atlas bewertet Score, Entry-Zone, Stop, Target, "
        "Datenqualität und Entscheidungsstatus in einer Search Console."
    ),
    kicker="ATLAS · Search Console",
)

left, right = st.columns([2, 1])

with left:
    raw_symbols = st.text_area(
        "Ticker eingeben",
        value=DEFAULT_SYMBOLS,
        placeholder="z. B. AAPL, MSFT, NVDA, V, JEPQ, QQQ",
        help="Mehrere Symbole mit Komma, Semikolon oder Zeilenumbruch trennen. Maximal 12 Symbole pro Lauf.",
        height=110,
    )

with right:
    metric_card(
        "Search Mode",
        "Manual",
        "Gezielte Analyse einzelner Ideen, Watchlist-Werte oder Depotkandidaten.",
        strong=True,
    )

symbols = normalize_symbols(raw_symbols)

run_search = st.button("Atlas Search starten", type="primary")

if not symbols:
    st.warning("Bitte mindestens ein Symbol eingeben.")
    st.stop()

if run_search:
    payloads = analyze_symbols(symbols)
else:
    payloads = analyze_symbols(symbols[:5])

payloads = sorted(payloads, key=numeric_score, reverse=True)

buy_count = sum(1 for p in payloads if status_of(p) == "buy")
watch_count = sum(1 for p in payloads if status_of(p) == "watch")
avoid_count = sum(1 for p in payloads if status_of(p) == "avoid")
error_count = sum(1 for p in payloads if quality_of(p) == "error")

section("Search Summary")

a, b, c, d = st.columns(4)

with a:
    metric_card("Symbols", str(len(payloads)), "Analysierte Ticker in diesem Suchlauf.")

with b:
    metric_card("Buy", str(buy_count), "Handlungsfähige Kandidaten.", strong=buy_count > 0)

with c:
    metric_card("Watch", str(watch_count), "Interessant, aber nicht zwingend heute handeln.")

with d:
    metric_card("Errors", str(error_count), "Fehlerhafte oder nicht verfügbare Symbole.")

section("Ranked Search Results")

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
    st.info("Keine Suchergebnisse verfügbar.")


section("Score Transparency")

if payloads:
    selected_symbol = st.selectbox(
        "Symbol für Score-Erklärung auswählen",
        options=[symbol_of(payload) for payload in payloads],
        index=0,
    )

    selected_payload = next(
        payload for payload in payloads if symbol_of(payload) == selected_symbol
    )

    score_explanation_card(
        symbol=symbol_of(selected_payload),
        score=score_of(selected_payload),
        status=status_of(selected_payload),
        data_quality=quality_of(selected_payload),
        entry_zone=entry_of(selected_payload),
        stop=stop_of(selected_payload),
        target=target_of(selected_payload),
        current_price=current_price_display(selected_payload),
        currency=currency_display(selected_payload),
        exchange=exchange_display(selected_payload),
        note="Sprint 12B: Score-Kontext mit aktuellem Kurs, Währung und Börsenplatz. Fundamentals, News und Portfolio-Fit folgen in den nächsten Ausbaustufen.",
    )

section("Detailed Search Table")

rows = []
for payload in payloads:
    rows.append(
        {
            "Symbol": symbol_of(payload),
            "Decision": bucket(status_of(payload)),
            "Atlas Score": score_of(payload),
            "Current Price": f"{current_price_display(payload)} {currency_display(payload)}",
            "Entry Zone": f"{entry_of(payload)} {currency_display(payload)}",
            "Stop": f"{stop_of(payload)} {currency_display(payload)}",
            "Target": f"{target_of(payload)} {currency_display(payload)}",
            "Exchange": exchange_display(payload),
            "Data Quality": quality_of(payload),
            "Error": payload.get("error", ""),
        }
    )

if rows:
    premium_table(rows)

section("Decision Guidance")

if buy_count > 0:
    st.success(
        "Mindestens ein Suchergebnis liegt in der Buy-Zone. Nächster Schritt: Back Book öffnen, Chart prüfen, Positionsgröße und Portfolio-Fit bewerten."
    )
elif watch_count > 0:
    st.info(
        "Die Suche liefert vor allem Watch-Kandidaten. Atlas empfiehlt: beobachten, Entry-Zonen respektieren und nicht nachlaufen."
    )
elif avoid_count > 0:
    st.warning(
        "Die Suche liefert überwiegend Avoid-Signale. Das ist kein Fehler, sondern Schutz vor schlechten Einstiegen."
    )
else:
    st.info(
        "Keine klare Entscheidungslogik verfügbar. Prüfe Symbol, Datenqualität und Provider Status."
    )

section("How to Use This Page")

x, y, z = st.columns(3)

with x:
    metric_card(
        "1 · Idee eingeben",
        "Ticker",
        "Beispiele: MSFT, V, NVDA, JEPQ, QQQ, XLE.",
    )

with y:
    metric_card(
        "2 · Score lesen",
        "Atlas",
        "Score, Status und Entry-Zone sagen dir, ob die Idee prüfenswert ist.",
    )

with z:
    metric_card(
        "3 · Nicht blind handeln",
        "Back Book",
        "Diese Seite ist ein Vorfilter. Die Detailentscheidung kommt im Back Book.",
    )
