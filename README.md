# vibe-registry

**A community skill/plugin registry + installer for [Mistral vibe](https://github.com/mistralai/mistral-vibe).**
`vibe install <name>` wires curated vibe skills, agents, and MCP servers into
`~/.vibe` — idempotently and reversibly.

[![CI](https://github.com/guillaumevele/vibe-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/guillaumevele/vibe-registry/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)

---

## Why

vibe ships **no marketplace** — skills are local files in `~/.vibe/skills/`, and
plugin discovery is an open, unshipped request
([discussion #497](https://github.com/mistralai/mistral-vibe/discussions/497)).
Claude Code and OpenCode have rich registries; vibe's equivalent is empty. This is
that missing ecosystem layer — first, and deliberately **community, not official**.

```bash
pip install vibe-registry
vibe-registry list                 # • = installed, [needs KEY] flagged, COMMUNITY header
vibe install context7              # fetch + wire into ~/.vibe/config.toml
vibe-registry uninstall context7   # reverse it
```

## Honest by construction

- **Community, not official.** Every entry is flagged `community`; nothing claims
  to be official Mistral. The CLI says so on every `list`.
- **Keys are never auto-wired.** An entry that needs a secret (github, supabase,
  `mistral-mcp`) is **listed but not installed** — the CLI prints the env var to
  set and stops. No secret is ever stored or asked for.
- **Reversible, with backups.** Every write to `~/.vibe/config.toml` /
  `AGENTS.md` is preceded by a `*.registry-bak` backup and confined to a managed
  region; `uninstall` restores it.
- **Supply-chain posture (v1).** The index pins each source; `--dry-run` shows
  exactly what will run before anything touches `~/.vibe`. There is no sandboxing
  of third-party MCP servers — show-before-run + pinned refs is the v1 mitigation,
  stated plainly. Review a community source before installing it.

## The one real piece of engineering

The installer generalizes [vibe-orchestra](https://github.com/guillaumevele/vibe-orchestra)'s
proven, reversible install surgery — and fixes a bug reproduced in it: that
installer dedups `mcp_servers` by a **hardcoded** name tuple, so a *foreign*
server (the whole point of a registry) survives the filter and **duplicates on the
second install**. vibe-registry records what each entry created in a lockfile
(`~/.vibe/registry/installed.json`) and dedups by **that** — so installing any
entry twice is a no-op, and `uninstall` removes exactly what was added while
preserving the user's own servers. This is proven by a test:
`test_double_install_of_a_foreign_entry_yields_one`.

## Add an entry

Send a PR adding to `vibe_registry/index.json`: `{id, kind, summary,
official:false, source, needs_key, wiring:{mcp_servers:[...]}}`. Keep it honest —
`official` stays false, and anything needing a key carries no auto-wiring.

## License

MIT © Guillaume Vele
