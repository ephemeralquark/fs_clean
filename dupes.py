#!/usr/bin/env python3
"""Duplicate file finder — scan a directory tree and identify files with identical content."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


# ---------- hashing ----------

def file_md5(path: Path, *, buf_size: int = 65536) -> str:
    """Return hex digest of a file's content, reading in chunks."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


# ---------- scanning ----------

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
                f["md5"] = file_md5(f["path"])
            except OSError:
                continue
            by_hash[f["md5"]].append(f)

        for digest, members in by_hash.items():
            if len(members) >= 2:
                members[0]["md5"] = digest  # keep digest on first entry
                dupes.append(members)

    return dupes


# ---------- formatting ----------

def _human(n: int) -> str:
    """Return a human-readable byte string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def format_groups(groups: list[list[dict]]) -> str:
    lines: list[str] = []
    total_waste = 0
    for i, group in enumerate(groups, 1):
        waste = group[0]["size"] * (len(group) - 1)
        total_waste += waste
        lines.append(f"\nGroup {i} ({_human(group[0]['size'])} each, {len(group)} copies, "
                      f"save {_human(waste)}):")
        for idx, f in enumerate(group):
            marker = "  <- keep" if idx == 0 else ""
            lines.append(f"  {f['path']}{marker}")
    lines.append("")
    lines.append(f"{'='*60}")
    lines.append(f"Found {len(groups)} group(s), {sum(len(g) for g in groups)} file(s) total, "
                 f"{_human(total_waste)} recoverable")
    return "\n".join(lines)


# ---------- CLI ----------

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


if __name__ == "__main__":
    main()
