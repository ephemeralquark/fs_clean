"""Command-line interface for the duplicate file finder."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .scanner import find_duplicates, scan
from .formatters import format_groups


def cmd_parse(args: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Find duplicate files in a directory tree.")
    p.add_argument("root", type=Path, help="Root directory to scan")
    p.add_argument("--delete", action="store_true",
                       help="Delete all but the first file in each duplicate group")
    p.add_argument("--dry-run", action="store_true",
                       help="Show what would be deleted without actually deleting")
    p.add_argument("--format", choices=["text", "json"], default="text",
                       dest="fmt", help="Output format")
    p.add_argument("--min-size", type=int, default=0,
                       help="Minimum file size in bytes to consider (default: 0)")
    return p.parse_args(args)


def main(argv: list[str] | None = None) -> None:
    ns = cmd_parse(argv)

    if not ns.root.exists():
        print(f"Error: {ns.root} does not exist", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {ns.root.resolve()} ...")
    groups = find_duplicates(ns.root)
    groups = [g for g in groups if g[0]["size"] >= ns.min_size]

    if ns.fmt == "json":
        data = []
        for g in groups:
            data.append({
                "size": g[0]["size"],
                "md5": g[0]["md5"],
                "files": [str(f["path"]) for f in g],
            })
        print(json.dumps({"groups": data, "total_groups": len(data)}, indent=2))
        return

    # text mode
    output = format_groups(groups)
    print(output)

    if ns.delete:
        print()
        for group in groups:
            for f in group[1:]:  # skip first = keep
                target = f["path"]
                action = "Would delete" if ns.dry_run else "Deleted"
                try:
                    if not ns.dry_run:
                        target.unlink()
                except OSError as exc:
                    print(f"  ERROR deleting {target}: {exc}", file=sys.stderr)
                    continue
                print(f"  {action} {target}")
