"""Load the registry manifest (registry/index.json) — the curated index of vibe
skills/agents/MCP servers you can install by name."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT = Path(__file__).resolve().parent / "index.json"


@dataclass(frozen=True)
class Entry:
    id: str
    kind: str               # "mcp" | "skill" | "agent"
    summary: str
    official: bool = False  # honest: none of these are official Mistral
    source: dict = field(default_factory=dict)   # {type: pypi|npx|git|builtin, ref, sha}
    needs_key: str = ""     # env var; if set, listed but never auto-wired
    wiring: dict = field(default_factory=dict)    # {mcp_servers: [..]}
    homepage: str = ""

    @property
    def server_specs(self) -> list:
        return self.wiring.get("mcp_servers", [])


def load(path: Path | None = None) -> list:
    data = json.loads(Path(path or _DEFAULT).read_text(encoding="utf-8"))
    return [Entry(**e) for e in data["entries"]]


def by_id(entries: list) -> dict:
    return {e.id: e for e in entries}
