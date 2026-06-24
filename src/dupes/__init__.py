"""Duplicate file finder — scan a directory tree and identify files with identical content."""

from .hashers import Hasher
from .hashers import file_md5 as _file_md5  # type: ignore[misc] # noqa: F401

from .scanner import scan, find_duplicates
from .formatters import _human, format_groups, Formatter
from .cli import cmd_parse, main

# Module-level re-exports for backwards compatibility
file_md5 = _file_md5

__all__ = [
    "Hasher",
    "Formatter",
    "file_md5",
    "scan",
    "find_duplicates",
    "_human",
    "format_groups",
    "cmd_parse",
    "main",
]
