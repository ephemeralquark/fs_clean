"""Duplicate detection logic using FileInfo and Hasher."""

from __future__ import annotations

from collections import defaultdict

from .models import DuplicateGroup, FileInfo
from ..input.hasher import Hasher


class DuplicationDetector:
    """Finds groups of duplicate files by size pre-filtering then content hashing.

    Accepts a *hasher* via dependency injection so the caller controls the
    hashing strategy (useful for testing with mocks).  Defaults to :class:`Hasher`.
    """

    def __init__(self, *, hasher: Hasher | None = None) -> None:
        self._hasher = hasher if hasher is not None else Hasher()

    def find_duplicates(self, files: list[FileInfo]) -> list[DuplicateGroup]:
        """Return groups of duplicate *FileInfo* objects (2+ members each)."""
        by_size = defaultdict(list)
        for f in files:
            by_size[f.size].append(f)

        dupes: list[DuplicateGroup] = []
        for size, group in by_size.items():
            if len(group) < 2:
                continue
            by_hash = defaultdict(list)
            for f in group:
                try:
                    digest = self._hasher.hash(f.path)
                except OSError:
                    continue
                by_hash[digest].append(f)

            for digest, members in by_hash.items():
                if len(members) >= 2:
                    dupes.append(DuplicateGroup(size=size, md5=digest, files=members))
        return dupes
