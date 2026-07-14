from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas_core.screener.quote_context import QuoteContext


ETF_LIKE_SYMBOLS = {
    "QQQ",
    "JEPQ",
    "JEPI",
    "SPY",
    "VOO",
    "VTI",
    "IWM",
    "XLE",
    "XLK",
    "XLF",
    "XLY",
    "XLV",
    "XLI",
    "XLP",
    "XLU",
    "DIA",
}


@dataclass(frozen=True)
class TradeSetup:
    symbol: str
    current_price: Any
    currency: str
    exchange: str
    entry_low: Any
    entry_high: Any
    entry_zone: str
    stop: Any
    target: Any
    target_horizon: str
    setup_type: str
    setup_source: str
    note: str


def is_missing(value: Any) -> bool:
    return value in (None, "", "n/a", "n/a – n/a", "None – None")


def as_float_or_none(value: Any) -> float | None:
    try:
        if is_missing(value):
            return None
        return float(value)
    except Exception:
        return None


def _round(value: float) -> float:
    return round(float(value), 2)


def _is_etf_like(symbol: str) -> bool:
    return str(symbol).upper() in ETF_LIKE_SYMBOLS


def _explicit_target(trade: dict[str, Any]) -> Any:
    return (
        trade.get("take_profit")
        or trade.get("target_price")
        or trade.get("take_profit_price")
        or trade.get("tp")
        or "n/a"
    )


def _fallback_from_quote(symbol: str, quote: QuoteContext) -> tuple[Any, Any, Any, Any, str, str]:
    current = as_float_or_none(quote.current_price)
    if current is None:
        return "n/a", "n/a", "n/a", "n/a", "n/a", "Insufficient quote data."

    if _is_etf_like(symbol):
        entry_low = _round(current * 0.98)
        entry_high = _round(current)
        stop = _round(current * 0.93)
        target = _round(current * 1.08)
        setup_type = "ETF Swing"
        note = "ETF fallback setup based on current quote."
    else:
        entry_low = _round(current * 0.97)
        entry_high = _round(current)
        stop = _round(current * 0.90)
        target = _round(current * 1.12)
        setup_type = "Stock Swing"
        note = "Stock fallback setup based on current quote."

    return entry_low, entry_high, stop, target, setup_type, note


def _target_from_entry_stop(entry_low: Any, entry_high: Any, stop: Any) -> Any:
    low = as_float_or_none(entry_low)
    high = as_float_or_none(entry_high)
    stop_value = as_float_or_none(stop)

    if low is None or high is None or stop_value is None:
        return "n/a"

    entry_mid = (low + high) / 2
    risk = entry_mid - stop_value

    if risk <= 0:
        return "n/a"

    return _round(entry_mid + (2 * risk))


def _horizon_from_target_distance(current_price: Any, target: Any) -> str:
    current = as_float_or_none(current_price)
    target_value = as_float_or_none(target)

    if current is None or target_value is None or current <= 0 or target_value <= 0:
        return "n/a"

    distance_pct = ((target_value - current) / current) * 100

    if distance_pct <= 0:
        return "n/a"
    if distance_pct <= 5:
        return "2–4 Wochen"
    if distance_pct <= 12:
        return "4–8 Wochen"
    if distance_pct <= 20:
        return "8–12 Wochen"
    return "3–6 Monate"


def _setup_type(symbol: str, horizon: str, source: str) -> str:
    if _is_etf_like(symbol) and horizon != "n/a":
        return "ETF Swing"
    if source == "fallback" and horizon != "n/a":
        return "Stock Swing"
    if horizon in {"2–4 Wochen", "4–8 Wochen", "8–12 Wochen"}:
        return "Swing"
    if horizon == "3–6 Monate":
        return "Position"
    return "n/a"


def build_trade_setup(payload: dict[str, Any], quote: QuoteContext) -> TradeSetup:
    symbol = quote.symbol
    trade = payload.get("trade_plan", {}) or {}

    entry_low = trade.get("entry_low", "n/a")
    entry_high = trade.get("entry_high", "n/a")
    stop = trade.get("stop_loss", "n/a")
    target = _explicit_target(trade)

    source = "engine"
    note = "Trade setup from Atlas engine."

    if is_missing(entry_low) or is_missing(entry_high) or is_missing(stop):
        entry_low, entry_high, stop, target, setup_type, note = _fallback_from_quote(symbol, quote)
        source = "fallback"
    else:
        setup_type = "Swing"

    if is_missing(target):
        target = _target_from_entry_stop(entry_low, entry_high, stop)

    if is_missing(target):
        fallback_low, fallback_high, fallback_stop, fallback_target, fallback_type, fallback_note = _fallback_from_quote(symbol, quote)
        if not is_missing(fallback_target):
            target = fallback_target
            if is_missing(entry_low):
                entry_low = fallback_low
            if is_missing(entry_high):
                entry_high = fallback_high
            if is_missing(stop):
                stop = fallback_stop
            setup_type = fallback_type
            note = fallback_note
            source = "fallback"

    horizon = _horizon_from_target_distance(quote.current_price, target)
    setup_type = _setup_type(symbol, horizon, source)

    entry_zone = f"{entry_low} – {entry_high}"

    return TradeSetup(
        symbol=symbol,
        current_price=quote.current_price,
        currency=quote.currency,
        exchange=quote.exchange,
        entry_low=entry_low,
        entry_high=entry_high,
        entry_zone=entry_zone,
        stop=stop,
        target=target,
        target_horizon=horizon,
        setup_type=setup_type,
        setup_source=source,
        note=note,
    )
