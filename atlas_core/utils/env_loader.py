from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from atlas_core.config_loader import PROJECT_ROOT


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_env_file(path: str | Path = ".env") -> Dict[str, str]:
    """Load simple KEY=VALUE pairs without mutating os.environ.

    Atlas intentionally keeps secret loading explicit so tests, Streamlit and
    coding agents can inspect provider readiness without accidentally leaking or
    overwriting deployment secrets.
    """

    env_path = Path(path)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path
    if not env_path.exists():
        return {}

    values: Dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _strip_quotes(value)
    return values


def get_secret(name: str, env_values: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Return a secret from process env first, then from a parsed .env mapping."""

    process_value = os.environ.get(name)
    if process_value:
        return process_value
    if env_values:
        value = env_values.get(name)
        if value:
            return value
    return None


def mask_secret(value: Optional[str], visible: int = 4) -> str:
    """Return a non-sensitive representation of an API key."""

    if not value:
        return "missing"
    if len(value) <= visible:
        return "*" * len(value)
    return f"{'*' * max(len(value) - visible, 4)}{value[-visible:]}"
