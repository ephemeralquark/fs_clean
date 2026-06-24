"""Output formatting for duplicate file groups."""

from __future__ import annotations


def _human(n: float) -> str:
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
