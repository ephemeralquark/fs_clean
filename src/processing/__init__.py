"""Processing domain: domain models and duplicate detection."""

from .models import FileInfo, DuplicateGroup
from .detector import DuplicationDetector

__all__ = ["FileInfo", "DuplicateGroup", "DuplicationDetector"]
