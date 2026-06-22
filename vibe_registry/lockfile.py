"""The lockfile: what each installed registry entry created. This is the data
that replaces vibe-orchestra's hardcoded name tuple, making dedup correct for any
entry (ours or community)."""
from __future__ import annotations

import json
from pathlib import Path


def _path(vibe_home: Path) -> Path:
    return vibe_home / "registry" / "installed.json"


def read(vibe_home: Path) -> dict:
    p = _path(vibe_home)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def write(vibe_home: Path, lock: dict) -> None:
    p = _path(vibe_home)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")


def managed_server_names(lock: dict) -> set:
    """Every mcp_server name owned by the registry across all installed entries."""
    names = set()
    for entry in lock.values():
        names.update(entry.get("mcp_servers", []))
    return names


def all_managed_servers(lock: dict) -> list:
    """The full desired set of managed server tables, recomputed from the lock —
    passing this whole list to set_mcp_servers is idempotent by construction."""
    servers = []
    for entry in lock.values():
        servers.extend(entry.get("server_specs", []))
    return servers
