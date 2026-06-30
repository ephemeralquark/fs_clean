"""File-type filtering and heuristic scoring for canonical file selection."""

from __future__ import annotations

import re
from pathlib import Path


# Heuristic scoring
_VERSION_RE = re.compile(r"(?:v|ver|version)(\d+(?:\.\d+)*)", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_FINAL_RELEASE_WORDS = {"final", "release", "prod", "stable", "latest"}
_MEDIA_EXTS = {".mp4", ".mov", ".avi", ".mp3", ".wav", ".jpg", ".jpeg", ".png",
              ".gif", ".webp", ".svg", ".pdf"}
_CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
              ".c", ".cpp", ".h", ".rb", ".php", ".swift", ".kt", ".scala"}


def calculate_heuristic_score(path: Path) -> int:
    """Return a numeric score for *path* — higher means more likely the canonical copy."""
    stem = path.stem.lower()
    name = path.name.lower()
    ext = path.suffix.lower()
    score = 0

    # Version numbers: v2, v1.3.4, ver_3
    for m in _VERSION_RE.finditer(name):
        version_str = m.group(1)
        parts = [int(p) for p in version_str.split(".")]
        weight = sum(part * (10 ** (len(parts) - 1 - i)) for i, part in enumerate(parts))
        score += weight

    # ISO dates: 2024-01-15
    date_matches = _ISO_DATE_RE.findall(name)
    score += 30 * len(date_matches)

    # Release/final/stable indicators
    stem_words = re.split(r"[-_. ]+", stem)
    for word in stem_words:
        if word in _FINAL_RELEASE_WORDS and not word.isdigit():
            score += 40

    # Standalone digit sequences (not part of a version pattern)
    bare_numbers = re.findall(r"(?<![vV])(\d{2,})(?!\.\d)", name)
    for num_str in bare_numbers:
        if int(num_str) > 1:
            score += 5

    # Slight preference for media/code extensions
    if ext in _MEDIA_EXTS or ext in _CODE_EXTS:
        score += 1

    return score


_FILTER_MAP = {
    "media": _MEDIA_EXTS,
    "code": _CODE_EXTS,
}


def passes_filter(path: Path, filter_type: str | None) -> bool:
    """Return whether *path* matches *filter_type*."""
    if filter_type is None:
        return True
    allowed_exts = _FILTER_MAP.get(filter_type)
    if allowed_exts is None:
        return True
    return path.suffix.lower() in allowed_exts
