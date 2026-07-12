from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import parse, request


@dataclass
class JsonHttpResponse:
    status_code: int
    payload: Any
    url: str


class JsonHttpClient:
    """Tiny JSON HTTP client used by live provider adapters.

    The class exists mainly to keep provider code deterministic and testable:
    tests can inject a fake client with the same ``get_json``/``post_json``
    methods without allowing real network calls.
    """

    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    def get_json(self, url: str, params: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> JsonHttpResponse:
        full_url = self._url_with_params(url, params or {})
        req = request.Request(full_url, headers=dict(headers or {}), method="GET")
        with request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec B310 - explicit provider URL, user-configured live mode
            status_code = int(getattr(response, "status", 200))
            body = response.read().decode("utf-8")
        return JsonHttpResponse(status_code=status_code, payload=json.loads(body), url=full_url)

    def post_json(
        self,
        url: str,
        payload: Any,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> JsonHttpResponse:
        full_url = self._url_with_params(url, params or {})
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            full_url,
            data=body,
            headers={"Content-Type": "application/json", **dict(headers or {})},
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec B310 - explicit provider URL, user-configured live mode
            status_code = int(getattr(response, "status", 200))
            raw = response.read().decode("utf-8")
        return JsonHttpResponse(status_code=status_code, payload=json.loads(raw), url=full_url)

    @staticmethod
    def _url_with_params(url: str, params: Mapping[str, Any]) -> str:
        clean_params = {k: v for k, v in params.items() if v is not None}
        if not clean_params:
            return url
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{parse.urlencode(clean_params)}"
