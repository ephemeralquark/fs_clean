"""Directory scanning and duplicate detection."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

from .hashers import Hasher


def scan(root: Path, *, skip_hidden: bool = True, skip_sizes: set[int] | None = None) -> list[dict]:
    """Walk *root* and return a list of file dicts: {path, size, mtime}.

    Skips hidden files/dirs (names starting with '.') by default.
    Optional *skip_sizes* filters out files of given sizes (e.g. zero-byte files).
    """
    skip_sizes = skip_sizes or set()
    files: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune hidden directories in-place so os.walk descends no further
        if skip_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for name in filenames:
            if skip_hidden and name.startswith("."):
                continue
            full = Path(dirpath) / name
            try:
                st = full.stat()
            except OSError:
                continue
            if st.st_size in skip_sizes:
                continue
            files.append({
                "path": full,
                "size": st.st_size,
                "mtime": st.st_mtime,
            })
    return files


def find_duplicates(root: Path) -> list[list[dict]]:
    """Return groups of duplicate files (each group has 2+ entries)."""
    # 1) group by size (fast pre-filter)
    by_size = defaultdict(list)
    for f in scan(root):
        by_size[f["size"]].append(f)

    # 2) for groups with 2+ same-size files, hash to confirm
    dupes: list[list[dict]] = []
    for size, group in by_size.items():
        if len(group) < 2:
            continue
        by_hash = defaultdict(list)
        for f in group:
            try:
                f["md5"] = Hasher.file_md5(f["path"])
            except OSError:
                continue
            by_hash[f["md5"]].append(f)

        for digest, members in by_hash.items():
            if len(members) >= 2:
                members[0]["md5"] = digest  # keep digest on first entry
                dupes.append(members)

    return dupes
