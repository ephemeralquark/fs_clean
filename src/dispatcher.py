"""Orchestrator: scans a directory, detects duplicates, and delegates formatting / deletion to their own domain classes."""

from __future__ import annotations

from pathlib import Path

from .action.deleter import Deleter
from .input.hasher import Hasher
from .input.scanner import Scanner
from .output.formatter import Formatter
from .processing.detector import DuplicationDetector


class Dispatcher:
    """Top-level dispatcher: scans a directory, detects duplicates,
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
