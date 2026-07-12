from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from atlas_core.config_loader import PROJECT_ROOT


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_key(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:60]
    cleaned = cleaned.strip("_") or "cache_key"
    return f"{cleaned}_{digest}.json"


@dataclass
class CacheResult:
    hit: bool
    expired: bool
    path: Path
    payload: Any = None
    metadata: Dict[str, Any] | None = None
    age_seconds: float | None = None
    issue: str | None = None


class JsonFileCache:
    """Small JSON file cache used by provider adapters.

    The cache is deliberately simple: one JSON envelope per provider/resource
    key. This keeps Sprint 5 transparent and easy to inspect before moving to
    DuckDB/SQLite in a later sprint.
    """

    def __init__(self, base_dir: str | Path = "data/cache"):
        base = Path(base_dir)
        if not base.is_absolute():
            base = PROJECT_ROOT / base
        self.base_dir = base
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, namespace: str, key: str) -> Path:
        namespace_dir = self.base_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)
        return namespace_dir / _safe_key(key)

    def set(self, namespace: str, key: str, payload: Any, metadata: Optional[Dict[str, Any]] = None) -> Path:
        path = self.path_for(namespace, key)
        envelope = {
            "created_at": _utc_now().isoformat(),
            "namespace": namespace,
            "key": key,
            "metadata": metadata or {},
            "payload": payload,
        }
        path.write_text(json.dumps(envelope, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return path

    def get(self, namespace: str, key: str, ttl_seconds: int | float | None = None) -> CacheResult:
        path = self.path_for(namespace, key)
        if not path.exists():
            return CacheResult(hit=False, expired=False, path=path, issue="cache_miss")
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return CacheResult(hit=False, expired=False, path=path, issue=f"invalid_json: {exc}")
        created_raw = envelope.get("created_at")
        age_seconds: float | None = None
        expired = False
        if created_raw:
            created = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_seconds = (_utc_now() - created).total_seconds()
            if ttl_seconds is not None and age_seconds > float(ttl_seconds):
                expired = True
        return CacheResult(
            hit=not expired,
            expired=expired,
            path=path,
            payload=envelope.get("payload"),
            metadata=envelope.get("metadata", {}),
            age_seconds=age_seconds,
            issue="expired" if expired else None,
        )

    def stats(self) -> Dict[str, Any]:
        files = list(self.base_dir.glob("**/*.json"))
        total_bytes = sum(path.stat().st_size for path in files if path.exists())
        namespaces = sorted({path.parent.name for path in files})
        return {"files": len(files), "total_bytes": total_bytes, "namespaces": namespaces}

    def iter_entries(self) -> Iterable[Path]:
        return self.base_dir.glob("**/*.json")


class FetchAuditLogger:
    """Append-only JSONL log for provider fetches and cache decisions."""

    def __init__(self, path: str | Path = "data/cache/fetch_audit.jsonl"):
        log_path = Path(path)
        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = log_path

    def log(
        self,
        *,
        provider: str,
        resource: str,
        status: str,
        cache_hit: bool = False,
        data_quality: str = "unknown",
        message: str = "",
    ) -> None:
        record = {
            "timestamp": _utc_now().isoformat(),
            "provider": provider,
            "resource": resource,
            "status": status,
            "cache_hit": cache_hit,
            "data_quality": data_quality,
            "message": message,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def tail(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        records = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
