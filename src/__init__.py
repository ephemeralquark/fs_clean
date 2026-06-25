"""fs_clean — find and remove duplicate files."""

from .cli import cmd_parse, main
from .dispatcher import Dispatcher

__all__ = ["Dispatcher", "cmd_parse", "main"]
