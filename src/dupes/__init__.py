"""Duplicate file finder — scan a directory tree and identify files with identical content."""

from __future__ import annotations

from .hasher import file_md5
from .scanner import scan, find_duplicates
from .formatters import _human, format_groups
from .cli import cmd_parse, main

__all__ = [
    "file_md5",
    "scan",
    "find_duplicates",
    "_human",
    "format_groups",
    "cmd_parse",
    "main",
]
