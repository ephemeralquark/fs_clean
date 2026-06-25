"""File content hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path


class Hasher:
    """Computes MD5 hex digests for file contents."""

    def hash(self, path: Path, *, buf_size: int = 65536) -> str:
        """Return the MD5 hex digest of *path*."""
        h = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(buf_size):
                h.update(chunk)
        return h.hexdigest()
