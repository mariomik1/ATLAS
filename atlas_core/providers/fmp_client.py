from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache


class FmpClient:
    """Small FMP REST client with cache and audit hooks.

    The client intentionally exposes a narrow JSON GET surface for Atlas provider
    adapters. It does not know about Atlas domain models; normalization happens
    in the calling provider.
    """

    base_url = "https://financialmodelingprep.com/stable"

    def __init__(
        self,
        *,
        api_key: str | None,
        cache: JsonFileCache | None = None,
        audit: FetchAuditLogger | None = None,
        ttl_seconds: int | float = 604800,
        live_enabled: bool = False,
        stale_allowed: bool = True,
        timeout: float = 12.0,
    ):
        self.api_key = api_key
        self.cache = cache or JsonFileCache("data/cache")
        self.audit = audit or FetchAuditLogger("data/cache/fetch_audit.jsonl")
        self.ttl_seconds = ttl_seconds
        self.live_enabled = live_enabled
        self.stale_allowed = stale_allowed
        self.timeout = timeout

    @property
    def ready(self) -> bool:
        return bool(self.live_enabled and self.api_key)

    def get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, namespace: str, resource: str) -> Any:
        params = dict(params or {})
        cache_key = self._cache_key(endpoint, params)
        cached = self.cache.get(namespace, cache_key, ttl_seconds=self.ttl_seconds)
        if cached.hit and cached.payload is not None:
            self.audit.log(
                provider="fmp",
                resource=resource,
                status="cache_hit",
                cache_hit=True,
                data_quality="live_or_delayed_cache",
                message=f"Loaded cached FMP payload for {endpoint}.",
            )
            return cached.payload

        if not self.ready:
            raise RuntimeError("FMP provider is disabled or FMP_API_KEY is missing.")

        stale_payload = cached.payload if cached.expired and cached.payload is not None else None
        try:
            payload = self._http_get_json(endpoint, params)
        except Exception as exc:
            if stale_payload is not None and self.stale_allowed:
                self.audit.log(
                    provider="fmp",
                    resource=resource,
                    status="provider_failed_stale_cache_used",
                    cache_hit=True,
                    data_quality="partial",
                    message=f"FMP fetch failed; stale cache used: {type(exc).__name__}: {exc}",
                )
                return stale_payload
            self.audit.log(
                provider="fmp",
                resource=resource,
                status="provider_fetch_failed",
                cache_hit=False,
                data_quality="missing",
                message=f"FMP fetch failed: {type(exc).__name__}: {exc}",
            )
            raise

        self.cache.set(namespace, cache_key, payload, metadata={"provider": "fmp", "endpoint": endpoint, "params": self._safe_params(params)})
        self.audit.log(
            provider="fmp",
            resource=resource,
            status="provider_fetch_success",
            cache_hit=False,
            data_quality="live_or_delayed",
            message=f"Fetched and cached FMP payload for {endpoint}.",
        )
        return payload

    def _http_get_json(self, endpoint: str, params: Dict[str, Any]) -> Any:
        url = self._build_url(endpoint, params)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "Atlas/0.6B"})
        with urlopen(request, timeout=self.timeout) as response:  # nosec - controlled URLs only
            body = response.read().decode("utf-8")
        return json.loads(body)

    def _build_url(self, endpoint: str, params: Dict[str, Any]) -> str:
        endpoint = endpoint.lstrip("/")
        merged = {k: v for k, v in params.items() if v is not None and v != ""}
        merged["apikey"] = self.api_key
        return f"{self.base_url}/{endpoint}?{urlencode(merged)}"

    def _cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        safe = self._safe_params(params)
        return f"{endpoint}:{json.dumps(safe, sort_keys=True)}"

    @staticmethod
    def _safe_params(params: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in params.items() if k.lower() not in {"apikey", "api_key"}}
