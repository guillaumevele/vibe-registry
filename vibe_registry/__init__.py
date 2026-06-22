"""vibe-registry — a community skill/plugin registry + installer for Mistral vibe.

vibe ships no marketplace (discussion #497 is unshipped). This is the missing
ecosystem layer: install curated vibe skills / agents / MCP servers by name,
idempotently and reversibly, into ~/.vibe. Community, not official; entries that
need a key are listed but never auto-wired.
"""
from __future__ import annotations

from .engine import install, installed_ids, plan, uninstall
from .manifest import Entry, by_id, load

__version__ = "0.1.0"

__all__ = [
    "load", "by_id", "Entry",
    "install", "uninstall", "installed_ids", "plan",
    "__version__",
]
