from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache
from atlas_core.utils.env_loader import get_secret, load_env_file, mask_secret


PROVIDER_KEY_ENV: dict[str, str | None] = {
    "csv_sample": None,
    "local_sample": None,
    "manual_sample": None,
    "yfinance": None,
    "fmp": "FMP_API_KEY",
    "alphavantage": "ALPHAVANTAGE_API_KEY",
    "alpha_vantage": "ALPHAVANTAGE_API_KEY",
    "marketaux": "MARKETAUX_API_KEY",
    "newsapi": "NEWSAPI_API_KEY",
    "openfigi": "OPENFIGI_API_KEY",
    "polygon": "POLYGON_API_KEY",
}

OPTIONAL_KEY_PROVIDERS = {"openfigi"}

ROLE_CONFIG_KEYS = {
    "market": "market",
    "asset_data": "asset_data",
    "news": "news",
    "fundamentals": "fundamentals",
    "identifiers": "identifiers",
}


class ProviderStatus(BaseModel):
    role: str
    selected_provider: str
    status: str
    live_enabled: bool = False
    requires_api_key: bool = False
    env_var: Optional[str] = None
    key_present: bool = False
    masked_key: str = "missing"
    cache_ttl_seconds: Optional[int] = None
    data_quality_mode: str = "sample"
    notes: List[str] = Field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.status in {"offline_ready", "ready_for_live_fetch", "network_optional_ready"}


class ProviderSummary(BaseModel):
    total: int
    ready: int
    missing_keys: int
    disabled_live: int
    sample_only: int
    statuses: List[ProviderStatus]


class ProviderRegistry:
    """Central provider activation and readiness inspector.

    Sprint 5 does not force live network calls. It tells Atlas whether a selected
    provider is sample-only, disabled by config, missing secrets, or ready for a
    controlled live fetch.
    """

    def __init__(self, settings: dict, env_values: Optional[Dict[str, str]] = None):
        self.settings = settings
        self.env_values = env_values if env_values is not None else load_env_file()
        cache_cfg = settings.get("cache", {})
        self.cache = JsonFileCache(cache_cfg.get("base_dir", "data/cache"))
        audit_cfg = settings.get("audit", {})
        self.audit = FetchAuditLogger(audit_cfg.get("fetch_log_path", "data/cache/fetch_audit.jsonl"))

    def statuses(self) -> List[ProviderStatus]:
        return [self.status_for(role) for role in ROLE_CONFIG_KEYS]

    def summary(self) -> ProviderSummary:
        statuses = self.statuses()
        return ProviderSummary(
            total=len(statuses),
            ready=sum(1 for status in statuses if status.is_ready),
            missing_keys=sum(1 for status in statuses if status.status == "missing_api_key"),
            disabled_live=sum(1 for status in statuses if status.status == "disabled_by_config"),
            sample_only=sum(1 for status in statuses if status.status == "offline_ready"),
            statuses=statuses,
        )

    def status_for(self, role: str) -> ProviderStatus:
        config_key = ROLE_CONFIG_KEYS.get(role, role)
        cfg = self.settings.get(config_key, {})
        provider = str(cfg.get("provider", "csv_sample")).lower()
        env_var = PROVIDER_KEY_ENV.get(provider)
        secret = get_secret(env_var, self.env_values) if env_var else None
        live_enabled = bool(cfg.get("live_providers_enabled", self.settings.get("provider_activation", {}).get("live_providers_enabled", False)))
        ttl_seconds = self._ttl_seconds(config_key, cfg)
        notes: list[str] = []

        if provider in {"csv_sample", "local_sample", "manual_sample"}:
            return ProviderStatus(
                role=role,
                selected_provider=provider,
                status="offline_ready",
                live_enabled=False,
                requires_api_key=False,
                cache_ttl_seconds=ttl_seconds,
                data_quality_mode="sample",
                notes=["Offline sample provider is active. Do not treat sample data as live facts."],
            )

        if provider == "yfinance":
            return ProviderStatus(
                role=role,
                selected_provider=provider,
                status="network_optional_ready" if live_enabled else "disabled_by_config",
                live_enabled=live_enabled,
                requires_api_key=False,
                cache_ttl_seconds=ttl_seconds,
                data_quality_mode="delayed_or_unverified",
                notes=[
                    "yfinance requires network access and may return delayed, adjusted or incomplete data.",
                    "Enable only after accepting data-quality limitations.",
                ],
            )

        if env_var is None:
            notes.append("Provider is unknown to Sprint 5 registry; keep disabled until reviewed.")
            return ProviderStatus(
                role=role,
                selected_provider=provider,
                status="unknown_provider",
                live_enabled=False,
                requires_api_key=True,
                env_var=None,
                key_present=False,
                cache_ttl_seconds=ttl_seconds,
                data_quality_mode="unknown",
                notes=notes,
            )

        key_optional = provider in OPTIONAL_KEY_PROVIDERS

        if provider == "openfigi" and not secret:
            if not live_enabled:
                return ProviderStatus(
                    role=role,
                    selected_provider=provider,
                    status="disabled_by_config",
                    live_enabled=False,
                    requires_api_key=False,
                    env_var=env_var,
                    key_present=False,
                    masked_key="optional",
                    cache_ttl_seconds=ttl_seconds,
                    data_quality_mode="key_optional_but_disabled",
                    notes=["OpenFIGI key is optional, but live_providers_enabled is false. Atlas will not call this provider."],
                )
            return ProviderStatus(
                role=role,
                selected_provider=provider,
                status="ready_for_live_fetch",
                live_enabled=True,
                requires_api_key=False,
                env_var=env_var,
                key_present=False,
                masked_key="optional",
                cache_ttl_seconds=ttl_seconds,
                data_quality_mode="live_or_delayed_provider_ready_lower_rate_limit",
                notes=["OpenFIGI API key is optional; unauthenticated use has lower rate limits. Cache/audit wrappers are required."],
            )

        if not secret:
            return ProviderStatus(
                role=role,
                selected_provider=provider,
                status="missing_api_key",
                live_enabled=live_enabled,
                requires_api_key=True,
                env_var=env_var,
                key_present=False,
                masked_key="missing",
                cache_ttl_seconds=ttl_seconds,
                data_quality_mode="missing",
                notes=[f"Set {env_var} in .env or deployment secrets before enabling this provider."],
            )

        if not live_enabled:
            return ProviderStatus(
                role=role,
                selected_provider=provider,
                status="disabled_by_config",
                live_enabled=False,
                requires_api_key=True,
                env_var=env_var,
                key_present=bool(secret),
                masked_key=mask_secret(secret),
                cache_ttl_seconds=ttl_seconds,
                data_quality_mode="key_available_but_disabled",
                notes=["API key is present, but live_providers_enabled is false. Atlas will not call this provider."],
            )

        ready_notes = ["Provider is configured and key is present. Use cache/audit wrappers for every fetch."]
        return ProviderStatus(
            role=role,
            selected_provider=provider,
            status="ready_for_live_fetch",
            live_enabled=True,
            requires_api_key=True,
            env_var=env_var,
            key_present=bool(secret),
            masked_key=mask_secret(secret),
            cache_ttl_seconds=ttl_seconds,
            data_quality_mode="live_or_delayed_provider_ready",
            notes=ready_notes,
        )

    def _ttl_seconds(self, config_key: str, cfg: dict) -> Optional[int]:
        if "cache_ttl_minutes" in cfg:
            return int(float(cfg["cache_ttl_minutes"]) * 60)
        if "cache_ttl_hours" in cfg:
            return int(float(cfg["cache_ttl_hours"]) * 3600)
        if "cache_ttl_days" in cfg:
            return int(float(cfg["cache_ttl_days"]) * 86400)
        defaults = self.settings.get("cache", {}).get("default_ttl_seconds", {})
        return defaults.get(config_key)

    def cache_stats(self) -> dict:
        return self.cache.stats()

    def audit_tail(self, limit: int = 25) -> list[dict]:
        return self.audit.tail(limit=limit)

    def log_provider_decision(self, status: ProviderStatus) -> None:
        self.audit.log(
            provider=status.selected_provider,
            resource=status.role,
            status=status.status,
            cache_hit=False,
            data_quality=status.data_quality_mode,
            message="; ".join(status.notes[:2]),
        )
