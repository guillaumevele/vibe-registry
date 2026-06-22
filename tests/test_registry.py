"""Registry tests. The dedup fix is the headline: a FOREIGN entry installed twice
must yield ONE config entry. Needs tomllib (3.11+); fetch is faked (no network)."""
from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.version_info < (3, 11), reason="needs tomllib")

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

from vibe_registry import engine, manifest

_NOOP = lambda entry: "noop (fetch faked)"


def _c7():
    return manifest.Entry(
        id="context7", kind="mcp", summary="docs",
        source={"type": "npx", "ref": "@upstash/context7-mcp"},
        wiring={"mcp_servers": [{"name": "context7", "transport": "stdio",
                                 "command": "npx", "args": ["-y", "@upstash/context7-mcp"]}]})


def _servers(config):
    return [s["name"] for s in tomllib.loads(config.read_text())["mcp_servers"]]


def test_double_install_of_a_foreign_entry_yields_one(tmp_path):
    # THE fix: vibe-orchestra dedups by a hardcoded tuple, so a foreign name
    # duplicated on the 2nd install. The registry dedups by the lockfile, for any name.
    config = tmp_path / "config.toml"
    config.write_text('active_model = "x"\n'
                      'mcp_servers = [ { name = "mine", transport = "stdio", command = "c" } ]\n'
                      '[tools.bash]\ndefault_timeout = 300\n')
    engine.install(tmp_path, _c7(), fetch_fn=_NOOP)
    engine.install(tmp_path, _c7(), fetch_fn=_NOOP)        # twice
    names = _servers(config)
    assert names.count("context7") == 1                   # no duplicate
    assert "mine" in names                                # user's server preserved
    assert tomllib.loads(config.read_text())["tools"]["bash"]["default_timeout"] == 300


def test_uninstall_removes_managed_and_keeps_user(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('mcp_servers = [ { name = "mine", transport = "stdio", command = "c" } ]\n')
    engine.install(tmp_path, _c7(), fetch_fn=_NOOP)
    assert "context7" in _servers(config)
    engine.uninstall(tmp_path, "context7")
    names = _servers(config)
    assert "context7" not in names and "mine" in names    # reversible, user untouched
    assert engine.installed_ids(tmp_path) == set()


def test_needs_key_entry_is_listed_not_wired(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text("mcp_servers = []\n")
    gh = manifest.Entry(id="github", kind="mcp", summary="vcs",
                        needs_key="GITHUB_PERSONAL_ACCESS_TOKEN",
                        source={"type": "npx", "ref": "x"}, wiring={"mcp_servers": []})
    msg = engine.install(tmp_path, gh, fetch_fn=_NOOP)
    assert "not auto-wired" in msg.lower() and "GITHUB_PERSONAL_ACCESS_TOKEN" in msg
    assert engine.installed_ids(tmp_path) == set()        # nothing wired, no secret touched


def test_install_two_uninstall_one(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('mcp_servers = [ { name = "mine", transport = "stdio", command = "c" } ]\n')
    seq = manifest.Entry(id="sequential-thinking", kind="mcp", summary="reason",
                         source={"type": "npx", "ref": "b"},
                         wiring={"mcp_servers": [{"name": "sequential-thinking",
                                                  "transport": "stdio", "command": "npx",
                                                  "args": ["-y", "b"]}]})
    engine.install(tmp_path, _c7(), fetch_fn=_NOOP)
    engine.install(tmp_path, seq, fetch_fn=_NOOP)
    engine.uninstall(tmp_path, "context7")
    names = _servers(config)
    assert "context7" not in names and "sequential-thinking" in names and "mine" in names


def test_dry_run_touches_nothing(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text("mcp_servers = []\n")
    msg = engine.install(tmp_path, _c7(), fetch_fn=_NOOP, dry_run=True)
    assert "DRY RUN" in msg
    assert engine.installed_ids(tmp_path) == set() and _servers(config) == []


def test_seed_index_loads_and_is_honest():
    entries = manifest.load()
    assert len(entries) >= 6
    assert all(e.official is False for e in entries)               # nothing claims official
    for e in entries:
        if e.needs_key:
            assert e.wiring.get("mcp_servers", []) == []           # keyed entries never carry wiring
