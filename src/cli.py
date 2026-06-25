"""Command-line interface for the duplicate file finder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .action.deleter import Deleter
from .dispatcher import Dispatcher
from .input.hasher import Hasher
from .input.scanner import Scanner
from .output.formatter import Formatter
from .processing.detector import DuplicationDetector


def cmd_parse(argv: list[str] | None = None) -> argparse.Namespace:
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
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    ns = cmd_parse(argv)

    if not ns.root.exists():
        print(f"Error: {ns.root} does not exist", file=sys.stderr)
        sys.exit(1)

    finder = Dispatcher()
    print(f"Scanning {ns.root.resolve()} ...")
    groups = finder.scan_and_find(ns.root, min_size=ns.min_size)

    if ns.fmt == "json":
        print(finder.json_output(groups))
        return

    # text mode
    print(finder.text_output(groups))

    if ns.delete:
        deleter = Deleter()
        for group in groups:
            for status, path_str in deleter.delete_group(group, dry_run=ns.dry_run):
                print(f"  {status} {path_str}")
