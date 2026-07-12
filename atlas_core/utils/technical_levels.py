from __future__ import annotations


def atr_level(price: float, atr_pct: float, multiple: float) -> float:
    return round(price + price * atr_pct / 100 * multiple, 2)
