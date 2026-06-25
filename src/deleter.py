"""File deletion for duplicate file groups."""

from __future__ import annotations

import sys

from .models import DuplicateGroup


class Deleter:
    """Removes files from duplicate groups.

    For each group the first file is kept; all remaining are candidates
    for deletion.  The caller decides via *dry_run* whether to actually
    touch the filesystem.
    """

    def delete_group(self, group: DuplicateGroup, *, dry_run: bool = False) -> list[tuple[str, str]]:
        """Delete every file in *group* except the first.

        Returns a list of ``(status_str, path_str)`` tuples where
        *status_str* is ``"Would delete"`` or ``"Deleted"`` on success,
        or ``"ERROR"`` when deletion fails.
        """
        results: list[tuple[str, str]] = []
        for f in group.files[1:]:
            path_str = str(f.path)
            if dry_run:
                results.append(("Would delete", path_str))
            else:
                try:
                    f.path.unlink()
                    results.append(("Deleted", path_str))
                except OSError as exc:
                    print(f"  ERROR deleting {path_str}: {exc}", file=sys.stderr)
                    results.append(("ERROR", path_str))
        return results

    def list_deletions(self, group: DuplicateGroup) -> list[str]:
        """Return paths that *would* be deleted from *group*."""
        return [str(f.path) for f in group.files[1:]]
