from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas_core.screener.setup_chart import (
    distance_to_stop_pct,
    distance_to_target_pct,
    risk_reward_ratio,
)
from atlas_core.screener.trade_setup import TradeSetup, as_float_or_none


@dataclass(frozen=True)
class DecisionLayer:
    label: str
    priority: str
    action: str
    reason: str
    color_hint: str


def _score_value(score: Any) -> float:
    try:
        if isinstance(score, dict):
            score = score.get("total_score", score.get("score", 0))
        return float(score)
    except Exception:
        return 0.0


def _status_value(status: Any) -> str:
    return str(status or "neutral").lower()


def _number(value: Any) -> float | None:
    return as_float_or_none(value)


def _inside_entry_zone(setup: TradeSetup) -> bool:
    current = _number(setup.current_price)
    low = _number(setup.entry_low)
    high = _number(setup.entry_high)

    if current is None or low is None or high is None:
        return False

    return min(low, high) <= current <= max(low, high)


def _above_entry_zone(setup: TradeSetup) -> bool:
    current = _number(setup.current_price)
    high = _number(setup.entry_high)

    if current is None or high is None:
        return False

    return current > high


def _below_entry_zone(setup: TradeSetup) -> bool:
    current = _number(setup.current_price)
    low = _number(setup.entry_low)

    if current is None or low is None:
        return False

    return current < low


def _distance_above_entry_pct(setup: TradeSetup) -> float | None:
    current = _number(setup.current_price)
    high = _number(setup.entry_high)

    if current is None or high is None or high <= 0:
        return None

    return ((current - high) / high) * 100


def build_decision_layer(score: Any, status: Any, setup: TradeSetup) -> DecisionLayer:
    score_num = _score_value(score)
    status_text = _status_value(status)

    rr = risk_reward_ratio(setup)
    dist_target = distance_to_target_pct(setup)
    dist_stop = distance_to_stop_pct(setup)

    rr_num = _number(rr)
    dist_target_num = _number(dist_target)
    dist_stop_num = _number(dist_stop)

    if setup.current_price in (None, "", "n/a") or setup.target in (None, "", "n/a"):
        return DecisionLayer(
            label="Insufficient data",
            priority="Low",
            action="Nicht entscheiden, bis Kurs- und Setupdaten vollständig sind.",
            reason="Für dieses Symbol fehlen wesentliche Kurs- oder Setupdaten.",
            color_hint="neutral",
        )

    if status_text == "avoid" or score_num < 60:
        return DecisionLayer(
            label="Avoid",
            priority="Low",
            action="Nicht verfolgen.",
            reason="Score oder Status sprechen aktuell gegen ein Setup.",
            color_hint="negative",
        )

    if rr_num is not None and rr_num < 1.2:
        return DecisionLayer(
            label="Bad risk/reward",
            priority="Low",
            action="Nicht einsteigen, außer das Setup verbessert sich deutlich.",
            reason=f"Das Chance/Risiko-Verhältnis ist mit {rr} zu schwach.",
            color_hint="negative",
        )

    if _inside_entry_zone(setup) and score_num >= 70 and rr_num is not None and rr_num >= 1.5:
        return DecisionLayer(
            label="Actionable now",
            priority="High",
            action="Setup ist grundsätzlich handlungsfähig. Positionsgröße und Risiko prüfen.",
            reason=(
                f"Aktueller Kurs liegt in der Entry-Zone, Score ist konstruktiv "
                f"und Risk/Reward liegt bei {rr}."
            ),
            color_hint="positive",
        )

    if _above_entry_zone(setup):
        distance_above = _distance_above_entry_pct(setup)
        if distance_above is not None and distance_above > 3:
            return DecisionLayer(
                label="Too far extended",
                priority="Medium",
                action="Nicht hinterherlaufen. Auf Pullback in die Entry-Zone warten.",
                reason=f"Der Kurs liegt ca. {round(distance_above, 2)}% über der Entry-Zone.",
                color_hint="warning",
            )

        return DecisionLayer(
            label="Wait for pullback",
            priority="Medium",
            action="Beobachten und auf besseren Entry warten.",
            reason="Der Kurs liegt leicht oberhalb der Entry-Zone.",
            color_hint="warning",
        )

    if _below_entry_zone(setup):
        return DecisionLayer(
            label="Below entry zone",
            priority="Medium",
            action="Beobachten. Erst prüfen, ob Schwäche oder attraktiver Pullback.",
            reason="Der Kurs liegt unterhalb der Entry-Zone.",
            color_hint="neutral",
        )

    if status_text == "watch" or score_num >= 65:
        return DecisionLayer(
            label="Watch",
            priority="Medium",
            action="Auf Watchlist lassen und Setup weiter beobachten.",
            reason=(
                f"Score ist brauchbar, aber die Kombination aus Entry-Zone, "
                f"Risk/Reward und Signalstärke ist noch nicht eindeutig."
            ),
            color_hint="neutral",
        )

    return DecisionLayer(
        label="Neutral",
        priority="Low",
        action="Keine klare Aktion.",
        reason="Das Setup liefert aktuell keine klare Entscheidung.",
        color_hint="neutral",
    )
