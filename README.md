# vibe-registry

> [!WARNING]
> Archived on 2026-07-13. Do not install this project.
> Version 0.1.0 can remove existing `mcp_servers` entries when run with
> Python 3.9 or 3.10, and can rewrite an invalid TOML configuration instead
> of failing closed. No supported release is available.
>
> Plugin and marketplace support for Mistral Vibe is being developed
> [upstream in pull request #514](https://github.com/mistralai/mistral-vibe/pull/514).

This repository preserves an early community registry experiment for
[Mistral Vibe](https://github.com/mistralai/mistral-vibe). It was never published
to PyPI and has no supported release or installation path.

## Why it was archived

- On Python 3.9 or 3.10, which the package metadata declares compatible, the
  prototype can destructively rewrite a user's existing MCP server list. Its
  TOML surgery tests are skipped below Python 3.11. Malformed TOML can also
  reach a destructive rewrite path.
- Its advertised `vibe install` command is not provided by the package.
- Backup creation does not make the uninstall path a complete restoration.
- Source references in the experimental index are not all version-pinned.
- The official Vibe repository now has an active, substantially broader plugin
  and marketplace implementation in [pull request #514](https://github.com/mistralai/mistral-vibe/pull/514).

The code remains available for historical inspection only. Do not run it against
a real `~/.vibe/config.toml`.

## License

MIT © Guillaume Vele
