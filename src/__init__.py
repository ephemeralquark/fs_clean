"""fs_clean — find and remove duplicate files."""

from .cli import DuplicateFinder, cmd_parse, main

__all__ = ["DuplicateFinder", "cmd_parse", "main"]
