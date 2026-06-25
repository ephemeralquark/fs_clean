"""Duplicate file finder — scan a directory tree and identify files with identical content."""

from __future__ import annotations

from .cli import DuplicateFinder, cmd_parse, main
from .deleter import Deleter
from .detector import DuplicationDetector
from .formatter import Formatter
from .hasher import Hasher
from .models import DuplicateGroup, FileInfo
from .scanner import Scanner


__all__ = [
    "cmd_parse",
    "Deleter",
    "DuplicateFinder",
    "DuplicateGroup",
    "FileInfo",
    "Formatter",
    "Hasher",
    "Scanner",
    "main",
]
