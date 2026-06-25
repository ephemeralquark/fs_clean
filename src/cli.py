"""Command-line interface for the duplicate file finder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .deleter import Deleter
from .detector import DuplicationDetector
from .formatter import Formatter
from .hasher import Hasher
from .scanner import Scanner


class DuplicateFinder:
    """Top-level orchestrator: scans a directory, detects duplicates,
    and delegates formatting / deletion to their own domain classes."""

    def __init__(
        self,
        scanner: Scanner | None = None,
        detector: DuplicationDetector | None = None,
        formatter: Formatter | None = None,
        deleter: Deleter | None = None,
    ) -> None:
        self.scanner = scanner if scanner is not None else Scanner()
        self.detector = detector if detector is not None else DuplicationDetector()
        self.formatter = formatter if formatter is not None else Formatter()
        self.deleter = deleter if deleter is not None else Deleter()

    def scan_and_find(self, root: Path, *, min_size: int = 0) -> list:
        """Scan *root* and return duplicate groups filtered by *min_size*."""
        files = self.scanner.scan(root)
        groups = self.detector.find_duplicates(files)
        if min_size > 0:
            groups = [g for g in groups if g.size >= min_size]
        return groups

    def text_output(self, groups) -> str:
        """Format *groups* as human-readable text."""
        return self.formatter.format_groups(groups)

    def json_output(self, groups) -> str:
        """Format *groups* as JSON."""
        return self.formatter.format_groups_json(groups)


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

    finder = DuplicateFinder()
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
