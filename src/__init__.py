"""fs_clean — find and remove duplicate files."""

from .cli import DuplicateFinder, cmd_parse, main
from .deleter import Deleter
from .detector import DuplicationDetector
from .formatter import Formatter
from .hasher import Hasher
from .models import DuplicateGroup, FileInfo
from .scanner import Scanner

__all__ = [
    "Deleter", "DuplicateFinder", "DuplicationDetector",
    "FileInfo", "DuplicateGroup", "Formatter", "Hasher",
    "Scanner", "cmd_parse", "main",
]
