from __future__ import annotations

import html
from typing import Any

import streamlit as st


ATLAS_CSS = """
<style>
:root {
    --atlas-bg: #070A12;
    --atlas-panel: rgba(17, 24, 39, 0.82);
    --atlas-panel-strong: rgba(15, 23, 42, 0.96);
    --atlas-border: rgba(148, 163, 184, 0.18);
    --atlas-border-strong: rgba(96, 165, 250, 0.45);
    --atlas-text: #E5E7EB;
    --atlas-muted: #94A3B8;
    --atlas-soft: #CBD5E1;
    --atlas-gold: #D6B35A;
    --atlas-blue: #60A5FA;
    --atlas-green: #34D399;
    --atlas-red: #F87171;
    --atlas-orange: #F59E0B;
    --atlas-purple: #A78BFA;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(96, 165, 250, 0.16), transparent 32rem),
        radial-gradient(circle at top right, rgba(214, 179, 90, 0.10), transparent 28rem),
        linear-gradient(135deg, #050816 0%, #070A12 38%, #0B1020 100%);
    color: var(--atlas-text);
}

[data-testid="stSidebar"] {
    background: rgba(5, 8, 22, 0.92);
    border-right: 1px solid var(--atlas-border);
}

[data-testid="stSidebar"] * {
    color: var(--atlas-soft);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1320px;
}

h1, h2, h3 {
    letter-spacing: -0.03em;
}

.atlas-hero {
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.25rem;
    border-radius: 28px;
    background:
        linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(17, 24, 39, 0.72)),
        radial-gradient(circle at top right, rgba(214, 179, 90, 0.16), transparent 18rem);
    border: 1px solid var(--atlas-border);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
}

.atlas-kicker {
    color: var(--atlas-gold);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 700;
    margin-bottom: 0.35rem;
}

.atlas-title {
    color: #F8FAFC;
    font-size: 2.55rem;
    line-height: 1.02;
    font-weight: 800;
    margin: 0;
}

.atlas-subtitle {
    color: var(--atlas-muted);
    font-size: 1.02rem;
    max-width: 850px;
    margin-top: 0.75rem;
}

.atlas-card {
    padding: 1.05rem 1.1rem;
    border-radius: 22px;
    background: var(--atlas-panel);
    border: 1px solid var(--atlas-border);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.25);
    height: 100%;
}

.atlas-card-strong {
    padding: 1.15rem 1.2rem;
    border-radius: 24px;
    background: var(--atlas-panel-strong);
    border: 1px solid var(--atlas-border-strong);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.32);
    height: 100%;
}

.atlas-label {
    color: var(--atlas-muted);
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
    margin-bottom: 0.35rem;
}

.atlas-value {
    color: #F8FAFC;
    font-size: 1.85rem;
    line-height: 1.08;
    font-weight: 800;
}

.atlas-note {
    color: var(--atlas-muted);
    font-size: 0.88rem;
    margin-top: 0.35rem;
}

.atlas-section {
    color: #F8FAFC;
    font-size: 1.22rem;
    font-weight: 800;
    margin: 1.4rem 0 0.7rem 0;
    letter-spacing: -0.02em;
}

.atlas-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.32rem 0.66rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid rgba(255,255,255,0.12);
}

.atlas-pill.buy {
    color: #052e1f;
    background: rgba(52, 211, 153, 0.92);
}

.atlas-pill.watch {
    color: #172554;
    background: rgba(96, 165, 250, 0.92);
}

.atlas-pill.avoid {
    color: #450a0a;
    background: rgba(248, 113, 113, 0.92);
}

.atlas-pill.neutral {
    color: #111827;
    background: rgba(203, 213, 225, 0.92);
}

.atlas-progress {
    width: 100%;
    height: 9px;
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.22);
    overflow: hidden;
    margin-top: 0.65rem;
}

.atlas-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--atlas-blue), var(--atlas-gold));
}

.atlas-small-table {
    font-size: 0.88rem;
    color: var(--atlas-soft);
}

.atlas-divider {
    height: 1px;
    background: var(--atlas-border);
    margin: 1rem 0;
}

div[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid var(--atlas-border);
    padding: 1rem;
    border-radius: 18px;
}

button[kind="primary"], .stButton > button {
    border-radius: 999px;
    border: 1px solid rgba(214, 179, 90, 0.35);
    background: linear-gradient(135deg, rgba(214, 179, 90, 0.92), rgba(96, 165, 250, 0.72));
    color: #050816;
    font-weight: 800;
}

</style>
"""


def inject_atlas_theme() -> None:
    st.markdown(ATLAS_CSS, unsafe_allow_html=True)


def _escape(value: Any) -> str:
    return html.escape(str(value))


def hero(title: str, subtitle: str, kicker: str = "ATLAS") -> None:
    st.markdown(
        f"""
        <div class="atlas-hero">
            <div class="atlas-kicker">{_escape(kicker)}</div>
            <h1 class="atlas-title">{_escape(title)}</h1>
            <div class="atlas-subtitle">{_escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="atlas-section">{_escape(title)}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, note: str = "", strong: bool = False) -> None:
    cls = "atlas-card-strong" if strong else "atlas-card"
    st.markdown(
        f"""
        <div class="{cls}">
            <div class="atlas-label">{_escape(label)}</div>
            <div class="atlas-value">{_escape(value)}</div>
            <div class="atlas-note">{_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(status: str) -> str:
    normalized = (status or "neutral").lower()
    if normalized not in {"buy", "watch", "avoid", "neutral"}:
        normalized = "neutral"
    return f'<span class="atlas-pill {normalized}">{_escape(status)}</span>'


def progress(label: str, value: float, note: str = "") -> None:
    pct = max(0, min(100, float(value)))
    st.markdown(
        f"""
        <div class="atlas-card">
            <div class="atlas-label">{_escape(label)}</div>
            <div class="atlas-value">{pct:.0f}%</div>
            <div class="atlas-progress"><div class="atlas-progress-fill" style="width:{pct:.0f}%"></div></div>
            <div class="atlas-note">{_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def candidate_card(symbol: str, status: str, score: Any, entry: str, note: str = "") -> None:
    try:
        score_text = f"{float(score):.1f}"
    except Exception:
        score_text = str(score)

    st.markdown(
        f"""
        <div class="atlas-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;">
                <div>
                    <div class="atlas-label">Candidate</div>
                    <div class="atlas-value">{_escape(symbol)}</div>
                </div>
                <div>{pill(status)}</div>
            </div>
            <div class="atlas-divider"></div>
            <div class="atlas-small-table">
                <b>Atlas Score:</b> {score_text}<br/>
                <b>Entry Zone:</b> {_escape(entry)}<br/>
                <span style="color:var(--atlas-muted);">{_escape(note)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
