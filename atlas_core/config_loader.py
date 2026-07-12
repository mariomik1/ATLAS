from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


class ConfigError(RuntimeError):
    pass


def load_yaml(path: str | Path) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path
    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a mapping: {file_path}")
    return data


def load_config(name: str) -> Dict[str, Any]:
    return load_yaml(CONFIG_DIR / name)


def load_all_configs() -> Dict[str, Dict[str, Any]]:
    return {
        "settings": load_config("settings.yaml"),
        "risk_rules": load_config("risk_rules.yaml"),
        "scoring_weights": load_config("scoring_weights.yaml"),
        "watchlists": load_config("watchlists.yaml"),
        "portfolio": load_config("portfolio.yaml"),
    }
