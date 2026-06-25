"""Output formatting for duplicate file groups."""

from __future__ import annotations


class Formatter:
    """Formats duplicate-group data into human-readable or JSON output."""

    @staticmethod
    def _human(n: float) -> str:
        """Return a human-readable byte string."""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(n) < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    def format_groups(self, groups) -> str:
        """Return a multi-line text representation of *groups*.

        Each group is expected to support ``size``, ``md5``, and ``files``
        attributes (e.g. :class:`~dupes.models.DuplicateGroup`).
        """
        lines: list[str] = []
        total_waste = 0
        for i, group in enumerate(groups, 1):
            waste = group.size * (len(group.files) - 1)
            total_waste += waste
            lines.append(f"\nGroup {i} ({self._human(group.size)} each, "
                         f"{len(group.files)} copies, "
                         f"save {self._human(waste)}):")
            for idx, f in enumerate(group.files):
                marker = "  <- keep" if idx == 0 else ""
                lines.append(f"  {f.path}{marker}")
        total_files = sum(len(g.files) for g in groups)
        lines.append("")
        lines.append(f"{'='*60}")
        lines.append(f"Found {len(groups)} group(s), {total_files} file(s) total, "
                     f"{self._human(total_waste)} recoverable")
        return "\n".join(lines)

    def format_groups_json(self, groups):
        """Return a JSON string representation of *groups*."""
        import json
        data = []
        for group in groups:
            files = [str(f.path) for f in group.files]
            data.append({
                "size": group.size,
                "md5": group.md5,
                "files": files,
            })
        return json.dumps({"groups": data, "total_groups": len(data)}, indent=2)
