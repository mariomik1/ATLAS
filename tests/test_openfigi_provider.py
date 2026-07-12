from __future__ import annotations

from atlas_core.enums import DataQualityLevel
from atlas_core.providers.openfigi_provider import OpenFigiIdentifierProvider
from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache


def test_openfigi_search_fetches_and_caches(tmp_path):
    calls = []

    def fake_fetch(url: str, headers, payload):
        calls.append((url, payload))
        assert url.endswith("/v3/search")
        return {
            "data": [
                {
                    "figi": "BBG000BPH459",
                    "ticker": "MSFT",
                    "name": "MICROSOFT CORP",
                    "exchCode": "US",
                    "securityType2": "Common Stock",
                    "marketSector": "Equity",
                }
            ]
        }

    provider = OpenFigiIdentifierProvider(
        live_enabled=True,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
    )
    provider._http_post_json = lambda endpoint, payload: fake_fetch(provider.base_url + endpoint, {}, payload)

    result = provider.search("Microsoft")
    result_cached = provider.search("Microsoft")

    assert result.matches[0].symbol == "MSFT"
    assert result.matches[0].figi == "BBG000BPH459"
    assert result.data_quality.level == DataQualityLevel.DELAYED
    assert result_cached.matches[0].symbol == "MSFT"
    assert len(calls) == 1


def test_openfigi_isin_mapping_payload(tmp_path):
    seen_payload = {}

    def fake_fetch(url: str, headers, payload):
        seen_payload.update({"url": url, "payload": payload})
        return [
            {
                "data": [
                    {
                        "figi": "BBG000BPH459",
                        "ticker": "MSFT",
                        "name": "MICROSOFT CORP",
                        "exchCode": "US",
                        "securityType2": "Common Stock",
                    }
                ]
            }
        ]

    provider = OpenFigiIdentifierProvider(
        live_enabled=True,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
    )
    provider._http_post_json = lambda endpoint, payload: fake_fetch(provider.base_url + endpoint, {}, payload)

    result = provider.search("US5949181045")

    assert seen_payload["url"].endswith("/v3/mapping")
    assert seen_payload["payload"][0]["idType"] == "ID_ISIN"
    assert result.matches[0].match_type == "isin"


def test_openfigi_disabled_uses_fallback(tmp_path):
    provider = OpenFigiIdentifierProvider(
        live_enabled=False,
        cache=JsonFileCache(tmp_path / "cache"),
        audit=FetchAuditLogger(tmp_path / "audit.jsonl"),
    )

    result = provider.search("Visa")

    assert result.matches
    assert result.matches[0].symbol == "V"
    assert result.data_quality.level == DataQualityLevel.SAMPLE
