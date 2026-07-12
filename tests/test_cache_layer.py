from atlas_core.utils.cache import FetchAuditLogger, JsonFileCache


def test_json_file_cache_set_get_and_expiry(tmp_path):
    cache = JsonFileCache(tmp_path / "cache")
    cache.set("news", "MSFT/latest", {"items": [1]}, metadata={"provider": "sample"})

    fresh = cache.get("news", "MSFT/latest", ttl_seconds=3600)
    assert fresh.hit is True
    assert fresh.expired is False
    assert fresh.payload == {"items": [1]}
    assert fresh.metadata["provider"] == "sample"

    expired = cache.get("news", "MSFT/latest", ttl_seconds=-1)
    assert expired.hit is False
    assert expired.expired is True


def test_fetch_audit_logger_tail(tmp_path):
    audit = FetchAuditLogger(tmp_path / "audit.jsonl")
    audit.log(provider="fmp", resource="fundamentals:MSFT", status="disabled_by_config", message="test")

    rows = audit.tail(limit=5)
    assert len(rows) == 1
    assert rows[0]["provider"] == "fmp"
    assert rows[0]["status"] == "disabled_by_config"
