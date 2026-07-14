from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

from atlas_core.screener.trade_setup import TradeSetup, as_float_or_none


@st.cache_data(show_spinner=False, ttl=300)
def load_price_history(symbol: str, period: str = "3mo") -> pd.DataFrame:
    if yf is None:
        return pd.DataFrame()

    try:
        data = yf.download(
            tickers=symbol,
            period=period,
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if data is None or data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        data = data.reset_index()

        expected = {"Date", "Open", "High", "Low", "Close"}
        if not expected.issubset(set(data.columns)):
            return pd.DataFrame()

        return data
    except Exception:
        return pd.DataFrame()


def _add_horizontal_line(fig: go.Figure, y: Any, label: str, dash: str = "solid") -> None:
    value = as_float_or_none(y)
    if value is None:
        return

    fig.add_hline(
        y=value,
        line_dash=dash,
        annotation_text=label,
        annotation_position="right",
        opacity=0.85,
    )


def _add_entry_band(fig: go.Figure, entry_low: Any, entry_high: Any) -> None:
    low = as_float_or_none(entry_low)
    high = as_float_or_none(entry_high)

    if low is None or high is None:
        return

    y0 = min(low, high)
    y1 = max(low, high)

    fig.add_hrect(
        y0=y0,
        y1=y1,
        opacity=0.18,
        line_width=0,
        annotation_text="Entry Zone",
        annotation_position="top left",
    )


def setup_chart(setup: TradeSetup, period: str = "3mo") -> None:
    history = load_price_history(setup.symbol, period=period)

    if history.empty:
        st.info("Für dieses Symbol konnte kein Chart geladen werden.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=history["Date"],
            open=history["Open"],
            high=history["High"],
            low=history["Low"],
            close=history["Close"],
            name=setup.symbol,
        )
    )

    _add_entry_band(fig, setup.entry_low, setup.entry_high)

    _add_horizontal_line(
        fig,
        setup.current_price,
        f"Current {setup.current_price} {setup.currency}",
        dash="solid",
    )
    _add_horizontal_line(
        fig,
        setup.entry_low,
        f"Entry Low {setup.entry_low}",
        dash="dot",
    )
    _add_horizontal_line(
        fig,
        setup.entry_high,
        f"Entry High {setup.entry_high}",
        dash="dot",
    )
    _add_horizontal_line(
        fig,
        setup.stop,
        f"Stop {setup.stop}",
        dash="dash",
    )
    _add_horizontal_line(
        fig,
        setup.target,
        f"Target {setup.target}",
        dash="dash",
    )

    fig.update_layout(
        title=f"{setup.symbol} Setup Chart · {setup.setup_type}",
        height=560,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="#0B1020",
        plot_bgcolor="#0B1020",
        font=dict(color="#E5E7EB"),
        xaxis=dict(
            rangeslider=dict(visible=False),
            gridcolor="rgba(148, 163, 184, 0.15)",
        ),
        yaxis=dict(
            title=f"Price ({setup.currency})",
            gridcolor="rgba(148, 163, 184, 0.15)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    st.plotly_chart(fig, width="stretch")


def risk_reward_ratio(setup: TradeSetup) -> Any:
    current = as_float_or_none(setup.current_price)
    stop = as_float_or_none(setup.stop)
    target = as_float_or_none(setup.target)

    if current is None or stop is None or target is None:
        return "n/a"

    risk = current - stop
    reward = target - current

    if risk <= 0 or reward <= 0:
        return "n/a"

    return round(reward / risk, 2)


def distance_to_stop_pct(setup: TradeSetup) -> Any:
    current = as_float_or_none(setup.current_price)
    stop = as_float_or_none(setup.stop)

    if current is None or stop is None or current <= 0:
        return "n/a"

    return round(((stop - current) / current) * 100, 2)


def distance_to_target_pct(setup: TradeSetup) -> Any:
    current = as_float_or_none(setup.current_price)
    target = as_float_or_none(setup.target)

    if current is None or target is None or current <= 0:
        return "n/a"

    return round(((target - current) / current) * 100, 2)


def setup_quality_note(setup: TradeSetup) -> str:
    rr = risk_reward_ratio(setup)
    target_distance = distance_to_target_pct(setup)
    stop_distance = distance_to_stop_pct(setup)

    if rr == "n/a":
        return "Setupqualität kann noch nicht vollständig bewertet werden."

    try:
        rr_value = float(rr)
    except Exception:
        return "Setupqualität kann noch nicht vollständig bewertet werden."

    if rr_value >= 2:
        rr_text = "attraktives Chance/Risiko-Verhältnis"
    elif rr_value >= 1.3:
        rr_text = "brauchbares, aber nicht starkes Chance/Risiko-Verhältnis"
    else:
        rr_text = "schwaches Chance/Risiko-Verhältnis"

    return (
        f"Risk/Reward: {rr}. Distance to Stop: {stop_distance}%. "
        f"Distance to Target: {target_distance}%. Einschätzung: {rr_text}."
    )
