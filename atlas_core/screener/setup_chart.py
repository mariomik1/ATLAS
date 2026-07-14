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


def _value(value: Any) -> float | None:
    return as_float_or_none(value)


def _line_trace(
    x_values: list[Any],
    y_value: Any,
    name: str,
    color: str,
    width: int = 2,
    dash: str = "solid",
) -> go.Scatter | None:
    price = _value(y_value)
    if price is None:
        return None

    return go.Scatter(
        x=x_values,
        y=[price for _ in x_values],
        mode="lines",
        name=name,
        line=dict(width=width, dash=dash, color=color),
        hovertemplate=f"{name}<br>Level: {price}<extra></extra>",
    )


def _add_zone(
    fig: go.Figure,
    x_values: list[Any],
    lower: Any,
    upper: Any,
    name: str,
    color: str,
    opacity: float,
) -> None:
    low = _value(lower)
    high = _value(upper)

    if low is None or high is None:
        return

    y0 = min(low, high)
    y1 = max(low, high)

    fig.add_trace(
        go.Scatter(
            x=x_values + x_values[::-1],
            y=[y0 for _ in x_values] + [y1 for _ in x_values[::-1]],
            fill="toself",
            fillcolor=color,
            mode="lines",
            line=dict(width=0, color=color),
            name=name,
            opacity=opacity,
            hovertemplate=f"{name}<br>Low: {y0}<br>High: {y1}<extra></extra>",
        )
    )


def setup_chart(setup: TradeSetup, period: str = "3mo") -> None:
    history = load_price_history(setup.symbol, period=period)

    if history.empty:
        st.info("Für dieses Symbol konnte kein Chart geladen werden.")
        return

    x_values = list(history["Date"])

    current = _value(setup.current_price)
    entry_low = _value(setup.entry_low)
    entry_high = _value(setup.entry_high)
    stop = _value(setup.stop)
    target = _value(setup.target)

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=history["Date"],
            open=history["Open"],
            high=history["High"],
            low=history["Low"],
            close=history["Close"],
            name=f"{setup.symbol} price",
            increasing_line_width=1,
            decreasing_line_width=1,
            increasing_line_color="#22C55E",
            decreasing_line_color="#EF4444",
            increasing_fillcolor="#22C55E",
            decreasing_fillcolor="#EF4444",
            hovertemplate=(
                "Date: %{x}<br>"
                "Open: %{open}<br>"
                "High: %{high}<br>"
                "Low: %{low}<br>"
                "Close: %{close}<extra></extra>"
            ),
        )
    )

    if entry_low is not None and entry_high is not None:
        _add_zone(
            fig,
            x_values,
            entry_low,
            entry_high,
            "Entry Zone",
            color="rgba(59, 130, 246, 0.32)",
            opacity=1.0,
        )

    if stop is not None and entry_low is not None:
        _add_zone(
            fig,
            x_values,
            stop,
            entry_low,
            "Risk Zone",
            color="rgba(239, 68, 68, 0.24)",
            opacity=1.0,
        )

    if target is not None and entry_high is not None:
        _add_zone(
            fig,
            x_values,
            entry_high,
            target,
            "Reward Zone",
            color="rgba(34, 197, 94, 0.18)",
            opacity=1.0,
        )

    line_specs = [
        (setup.current_price, f"Current Price · {setup.current_price} {setup.currency}", "#F8FAFC", 3, "solid"),
        (setup.entry_low, f"Entry Low · {setup.entry_low} {setup.currency}", "#60A5FA", 2, "dot"),
        (setup.entry_high, f"Entry High · {setup.entry_high} {setup.currency}", "#60A5FA", 2, "dot"),
        (setup.stop, f"Stop Loss · {setup.stop} {setup.currency}", "#EF4444", 3, "dash"),
        (setup.target, f"Take Profit · {setup.target} {setup.currency}", "#22C55E", 3, "dash"),
    ]

    for y_value, name, color, width, dash in line_specs:
        trace = _line_trace(x_values, y_value, name=name, color=color, width=width, dash=dash)
        if trace is not None:
            fig.add_trace(trace)

    fig.update_layout(
        title=(
            f"{setup.symbol} Setup Chart · {setup.setup_type} · "
            f"Target horizon: {setup.target_horizon}"
        ),
        height=620,
        margin=dict(l=10, r=20, t=70, b=20),
        paper_bgcolor="#0B1020",
        plot_bgcolor="#0B1020",
        font=dict(color="#E5E7EB"),
        hovermode="x unified",
        dragmode="pan",
        clickmode="event",
        xaxis=dict(
            rangeslider=dict(visible=False),
            gridcolor="rgba(148, 163, 184, 0.15)",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
            linecolor="rgba(148, 163, 184, 0.35)",
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(step="all", label="All"),
                    ]
                ),
                bgcolor="#111827",
                activecolor="#1F2937",
                font=dict(color="#E5E7EB"),
            ),
        ),
        yaxis=dict(
            title=f"Price ({setup.currency})",
            gridcolor="rgba(148, 163, 184, 0.15)",
            showline=True,
            linecolor="rgba(148, 163, 184, 0.35)",
            side="right",
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
            bgcolor="rgba(2, 6, 23, 0.96)",
            bordercolor="rgba(226, 232, 240, 0.45)",
            borderwidth=1,
            font=dict(size=12, color="#F8FAFC"),
            itemclick="toggleothers",
            itemdoubleclick="toggle",
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "scrollZoom": False,
            "responsive": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "autoScale2d",
                "zoomIn2d",
                "zoomOut2d",
            ],
        },
    )


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
