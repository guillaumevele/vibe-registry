"""Install / uninstall a registry entry into ~/.vibe — idempotently and
reversibly, deduping correctly for ANY name via the lockfile."""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import config_surgery as cs
from . import lockfile
from .manifest import Entry

MARK = "vibe-registry"


def _default_fetch(entry: Entry) -> str:
    """Ensure the entry's command is available. pypi -> uv tool install."""
    src = entry.source
    if src.get("type") == "pypi" and _has("uv"):
        spec = src["ref"]
        subprocess.run(["uv", "tool", "install", spec], capture_output=True, check=False)
        return f"uv tool install {spec}"
    if src.get("type") == "npx":
        return "lazy (npx -y on first run)"
    return "no fetch"


def _has(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


def plan(entry: Entry) -> str:
    if entry.needs_key:
        return (f"{entry.id}: COMMUNITY, needs ${entry.needs_key} — would be LISTED, "
                f"not auto-wired. Add it yourself once the key is set.")
    servers = ", ".join(s["name"] for s in entry.server_specs) or "(none)"
    return (f"{entry.id} ({entry.kind}, {'official' if entry.official else 'community'}): "
            f"fetch {entry.source.get('type','-')} {entry.source.get('ref','')}; "
            f"wire mcp_servers [{servers}] into ~/.vibe/config.toml")


def install(vibe_home: Path, entry: Entry, *, fetch_fn=None, dry_run: bool = False) -> str:
    if entry.needs_key:
        return (f"{entry.id} needs ${entry.needs_key}: listed, NOT auto-wired (no secret "
                f"is ever stored or asked). Add its server to ~/.vibe/config.toml yourself.")
    if dry_run:
        return "DRY RUN — would:\n  " + plan(entry)

    fetch_fn = fetch_fn or _default_fetch
    fetched = fetch_fn(entry)

    lock = lockfile.read(vibe_home)
    lock[entry.id] = {
        "kind": entry.kind, "official": entry.official,
        "mcp_servers": [s["name"] for s in entry.server_specs],
        "server_specs": entry.server_specs,
    }
    # Recompute the FULL desired managed set from the lockfile and apply it; this
    # is idempotent for ANY name (the dedup bug fix).
    config = vibe_home / "config.toml"
    cs.backup(config)
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        cs.set_mcp_servers(text, lockfile.all_managed_servers(lock),
                           lockfile.managed_server_names(lock)),
        encoding="utf-8")
    lockfile.write(vibe_home, lock)
    _refresh_marker(vibe_home, lock)
    return f"installed {entry.id} ({fetched}); wired {len(entry.server_specs)} server(s)."


def uninstall(vibe_home: Path, entry_id: str) -> str:
    lock = lockfile.read(vibe_home)
    if entry_id not in lock:
        return f"{entry_id} is not installed."
    removed = lock.pop(entry_id)
    # The removed entry's server names must still be FILTERED out, even though
    # they are no longer in the lock — otherwise an uninstalled server lingers.
    managed_names = lockfile.managed_server_names(lock) | set(removed.get("mcp_servers", []))
    config = vibe_home / "config.toml"
    if config.exists():
        cs.backup(config)
        config.write_text(
            cs.set_mcp_servers(config.read_text(encoding="utf-8"),
                               lockfile.all_managed_servers(lock), managed_names),
            encoding="utf-8")
    lockfile.write(vibe_home, lock)
    _refresh_marker(vibe_home, lock)
    return f"uninstalled {entry_id}."


def installed_ids(vibe_home: Path) -> set:
    return set(lockfile.read(vibe_home).keys())


def _refresh_marker(vibe_home: Path, lock: dict) -> None:
    agents_md = vibe_home / "AGENTS.md"
    base = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""
    if not lock:
        agents_md.parent.mkdir(parents=True, exist_ok=True)
        agents_md.write_text(cs.strip_marker_block(base, MARK), encoding="utf-8")
        return
    cs.backup(agents_md)
    names = ", ".join(sorted(lock))
    body = (f"Installed via vibe-registry (COMMUNITY, not official Mistral): {names}. "
            f"Run `vibe-registry list` to inspect; `vibe-registry uninstall <name>` to remove.")
    agents_md.parent.mkdir(parents=True, exist_ok=True)
    agents_md.write_text(cs.set_marker_block(base, MARK, body), encoding="utf-8")
