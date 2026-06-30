"""File deletion for duplicate file groups."""

from __future__ import annotations

import sys
from pathlib import Path

from ..processing.models import DuplicateGroup
from ..utils.file_heuristics import calculate_heuristic_score, passes_filter


class Deleter:
    """Removes files from duplicate groups.

    For each group the file with the highest heuristic score is kept (canonical);
    all others are candidates for deletion.  The caller decides via *dry_run*
    whether to actually touch the filesystem.
    """

    def delete_group(
        self,
        group: DuplicateGroup,
        *,
        dry_run: bool = False,
        filter_type: str | None = None,
    ) -> list[tuple[str, str]]:
        """Delete every duplicate in *group* except the highest-scoring file.

        Parameters
        ----------
        group :
            A DuplicateGroup from the scanning pipeline.
        dry_run :
            If ``True`` only record what would be deleted without touching files.
        filter_type :
            Optionally restrict which members are considered as candidates
            (e.g. ``"media"``, ``"code"``).  Non-matching members are left alone.

        Returns
        -------
        list[tuple[str, str]]
            List of ``(status_str, path_str)`` tuples where *status_str* is
            ``"Would delete"`` or ``"Deleted"`` on success, or ``"ERROR"``
            when deletion fails.
        """
        # --- 1. Filter candidates (if requested) ---
        if filter_type is not None:
            candidates = [f for f in group.files if passes_filter(f.path, filter_type)]
        else:
            candidates = list(group.files)

        # If filtering leaves 0 or 1 candidate, there is nothing to delete
        if len(candidates) <= 1:
            return []

        # --- 2. Score each candidate and find the canonical (highest score) ---
        scored = [(calculate_heuristic_score(f.path), f) for f in candidates]
        # Sort descending by score; ties broken by original order (stable sort)
        scored.sort(key=lambda x: x[0], reverse=True)

        canonical_file = scored[0][1]
        files_to_delete = [f for s, f in scored if f is not canonical_file]

        # --- 3. Delete (or record) ---
        results: list[tuple[str, str]] = []
        for f in files_to_delete:
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
        """Return paths that *would* be deleted from *group*.

        .. deprecated::
            Uses the old index-based strategy. Prefer :meth:`delete_group` instead.
        """
        return [str(f.path) for f in group.files[1:]]
