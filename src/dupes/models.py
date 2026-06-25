"""Domain models for duplicate file detection."""

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileInfo:
    """Immutable descriptor for a single file's metadata."""
    path: Path
    size: int
    mtime: float

    def __post_init__(self) -> None:
        if not self.path.is_absolute():
            object.__setattr__(self, "path", self.path.resolve())


DuplicateGroup = namedtuple("DuplicateGroup", ("size", "md5", "files"))
