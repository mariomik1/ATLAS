from atlas_core.providers.status import ProviderRegistry


def _settings(tmp_path, provider="csv_sample", live=False):
    return {
        "market": {"provider": "csv_sample", "cache_ttl_hours": 12},
        "asset_data": {"provider": "csv_sample", "cache_ttl_hours": 24},
        "news": {"provider": provider, "cache_ttl_minutes": 120, "live_providers_enabled": live},
        "fundamentals": {"provider": "csv_sample", "cache_ttl_hours": 168},
        "identifiers": {"provider": "local_sample", "cache_ttl_days": 30},
        "cache": {"base_dir": str(tmp_path / "cache")},
        "audit": {"fetch_log_path": str(tmp_path / "fetch_audit.jsonl")},
        "provider_activation": {"live_providers_enabled": False},
    }


def test_provider_registry_marks_sample_providers_ready(tmp_path):
    registry = ProviderRegistry(_settings(tmp_path), env_values={})
    summary = registry.summary()

    assert summary.total == 5
    assert summary.ready == 5
    assert summary.sample_only == 5
    assert summary.missing_keys == 0


def test_provider_registry_requires_key_for_live_provider(tmp_path):
    registry = ProviderRegistry(_settings(tmp_path, provider="marketaux", live=True), env_values={})
    status = registry.status_for("news")

    assert status.selected_provider == "marketaux"
    assert status.status == "missing_api_key"
    assert status.env_var == "MARKETAUX_API_KEY"


def test_provider_registry_detects_disabled_provider_with_key(tmp_path):
    registry = ProviderRegistry(_settings(tmp_path, provider="marketaux", live=False), env_values={"MARKETAUX_API_KEY": "secret123456"})
    status = registry.status_for("news")

    assert status.status == "disabled_by_config"
    assert status.key_present is True
    assert status.masked_key.endswith("3456")


def test_provider_registry_ready_when_key_and_live_enabled(tmp_path):
    registry = ProviderRegistry(_settings(tmp_path, provider="marketaux", live=True), env_values={"MARKETAUX_API_KEY": "secret123456"})
    status = registry.status_for("news")

    assert status.status == "ready_for_live_fetch"
    assert status.is_ready is True


def test_provider_registry_writes_audit_decision(tmp_path):
    registry = ProviderRegistry(_settings(tmp_path, provider="marketaux", live=True), env_values={})
    status = registry.status_for("news")
    registry.log_provider_decision(status)

    rows = registry.audit_tail(limit=3)
    assert rows[-1]["provider"] == "marketaux"
    assert rows[-1]["status"] == "missing_api_key"


def test_provider_registry_allows_openfigi_without_key_when_live_enabled(tmp_path):
    settings = _settings(tmp_path)
    settings["identifiers"] = {"provider": "openfigi", "cache_ttl_days": 30, "live_providers_enabled": True}
    registry = ProviderRegistry(settings, env_values={})

    status = registry.status_for("identifiers")

    assert status.selected_provider == "openfigi"
    assert status.status == "ready_for_live_fetch"
    assert status.requires_api_key is False
    assert "lower rate" in " ".join(status.notes).lower()
