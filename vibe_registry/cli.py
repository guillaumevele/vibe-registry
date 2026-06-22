"""CLI: `vibe-registry` and the `vibe-install` headline alias."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, engine, manifest

_BANNER = "vibe-registry — COMMUNITY skills/plugins for vibe (none are official Mistral)"


def _vibe_home() -> Path:
    return Path.home() / ".vibe"


def _cmd_list(entries, installed):
    print(_BANNER + "\n")
    for e in entries:
        mark = "•" if e.id in installed else " "
        key = f"  [needs {e.needs_key}]" if e.needs_key else ""
        flag = "official" if e.official else "community"
        print(f" {mark} {e.id:20} {e.kind:5} {flag:9} {e.summary}{key}")
    print("\n• = installed   |   `vibe install <name>`   |   `vibe-registry uninstall <name>`")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vibe-registry", description=_BANNER)
    parser.add_argument("--version", action="version", version=f"vibe-registry {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list the registry (• = installed)")
    s = sub.add_parser("search", help="search the registry"); s.add_argument("query")
    i = sub.add_parser("install", help="install an entry by name")
    i.add_argument("name"); i.add_argument("--dry-run", action="store_true")
    u = sub.add_parser("uninstall", help="remove an installed entry"); u.add_argument("name")
    sub.add_parser("installed", help="list what is installed")

    args = parser.parse_args(argv)
    home = _vibe_home()
    entries = manifest.load()
    index = manifest.by_id(entries)
    installed = engine.installed_ids(home)

    if args.command == "list":
        _cmd_list(entries, installed)
        return 0
    if args.command == "search":
        q = args.query.lower()
        _cmd_list([e for e in entries if q in e.id.lower() or q in e.summary.lower()], installed)
        return 0
    if args.command == "installed":
        print("\n".join(sorted(installed)) or "(nothing installed via vibe-registry)")
        return 0
    if args.command == "install":
        entry = index.get(args.name)
        if not entry:
            print(f"vibe-registry: unknown entry {args.name!r} (try `vibe-registry list`)", file=sys.stderr)
            return 1
        print(engine.install(home, entry, dry_run=args.dry_run))
        return 0
    if args.command == "uninstall":
        print(engine.uninstall(home, args.name))
        return 0
    return 2


def main_install(argv: list[str] | None = None) -> int:
    """`vibe-install <name>` headline alias for `vibe-registry install <name>`."""
    return main(["install", *(argv if argv is not None else sys.argv[1:])])


if __name__ == "__main__":
    raise SystemExit(main())
