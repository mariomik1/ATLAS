from __future__ import annotations


def weights_for_intent(scoring_config: dict, intent: str) -> dict[str, float]:
    overrides = scoring_config.get("intent_overrides", {})
    if intent in overrides:
        return {k: float(v) for k, v in overrides[intent].items()}
    return {k: float(v) for k, v in scoring_config.get("base_weights", {}).items()}
