"""Directory scanning for duplicate file detection."""

from __future__ import annotations

import os
from pathlib import Path

from .models import FileInfo


class Scanner:
    """Walks a directory tree and collects file metadata."""

    def __init__(self, *, skip_hidden: bool = True) -> None:
        self.skip_hidden = skip_hidden

    def scan(self, root: Path, *, skip_sizes: set[int] | None = None) -> list[FileInfo]:
        """Walk *root* and return file metadata dicts.

        Skips hidden files/dirs (names starting with '.') by default.
        Optional *skip_sizes* filters out files of given sizes.
        """
        skip_sizes = skip_sizes or set()
        files: list[FileInfo] = []
        for dirpath, dirnames, filenames in os.walk(root):
            if self.skip_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]

            for name in filenames:
                if self.skip_hidden and name.startswith("."):
                    continue
                full = Path(dirpath) / name
                try:
                    st = full.stat()
                except OSError:
                    continue
                if st.st_size in skip_sizes:
                    continue
                files.append(
                    FileInfo(path=full, size=st.st_size, mtime=st.st_mtime)
                )
        return files
