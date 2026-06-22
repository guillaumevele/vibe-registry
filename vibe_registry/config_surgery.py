"""Idempotent, reversible edits to ~/.vibe config — generalized from
vibe-orchestra's install.py, with the one fix the design pass reproduced.

The bug in the original: it dedups mcp_servers by a HARDCODED name tuple, so a
foreign/community server (the whole point of a registry) survives the filter AND
gets re-appended — a duplicate on the second install. Here the caller passes the
exact set of names IT manages (read from the lockfile), so passing the full
desired set is genuinely idempotent for any name, ours or community.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def _toml_val(v) -> str:
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_val(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {_toml_val(x)}" for k, x in v.items()) + " }"
    return _toml_val(str(v))


def _render_mcp(servers: list[dict]) -> str:
    if not servers:
        return "mcp_servers = []  # vibe-registry-managed"
    rows = ["  { " + ", ".join(f"{k} = {_toml_val(v)}" for k, v in s.items()) + " },"
            for s in servers]
    return "mcp_servers = [  # vibe-registry-managed\n" + "\n".join(rows) + "\n]"


def _inline_array_span(text: str, key: str):
    m = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\[", text)
    if not m:
        return None
    i = text.index("[", m.start())
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "[":
            depth += 1
        elif text[j] == "]":
            depth -= 1
            if depth == 0:
                return (m.start(), j + 1)
    return None


def set_mcp_servers(text: str, managed: list[dict], managed_names) -> str:
    """Return config text with the `managed` servers present, deduped by
    `managed_names` (the names this caller owns). Pass the FULL desired managed set
    each time; any server whose name is in managed_names is replaced, the user's
    own servers are preserved, and the result is idempotent for any name."""
    managed_names = set(managed_names) | {s["name"] for s in managed}
    try:
        existing = (tomllib.loads(text).get("mcp_servers", []) or []) if tomllib else []
    except tomllib.TOMLDecodeError:
        existing = []
    preserved = [s for s in existing if s.get("name") not in managed_names]
    merged = preserved + list(managed)
    rendered = _render_mcp(merged)

    text = re.sub(r"(?ms)^\[\[mcp_servers\]\].*?(?=^\[|\Z)", "", text)
    span = _inline_array_span(text, "mcp_servers")
    if span:
        return text[:span[0]] + rendered + text[span[1]:]
    m = re.search(r"(?m)^\[", text)
    if m:
        return text[:m.start()] + rendered + "\n\n" + text[m.start():]
    return text.rstrip() + "\n" + rendered + "\n"


def set_marker_block(text: str, mark: str, body: str) -> str:
    text = strip_marker_block(text, mark)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + f"\n# >>> {mark} >>>\n{body.rstrip()}\n# <<< {mark} <<<\n"


def strip_marker_block(text: str, mark: str) -> str:
    start, end = f"# >>> {mark} >>>", f"# <<< {mark} <<<"
    out, skip = [], False
    for ln in text.splitlines(keepends=True):
        if ln.strip() == start:
            skip = True
            continue
        if ln.strip() == end:
            skip = False
            continue
        if not skip:
            out.append(ln)
    return "".join(out)


def backup(p: Path) -> None:
    bak = p.with_suffix(p.suffix + ".registry-bak")
    if p.exists() and not bak.exists():
        shutil.copy2(p, bak)
