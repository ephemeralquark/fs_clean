"""File hashing utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path


class Hasher:
    """Compute MD5 hashes of file contents."""

    @staticmethod
    def file_md5(path: Path, *, buf_size: int = 65536) -> str:
        """Return hex digest of a file's content, reading in chunks."""
        h = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(buf_size):
                h.update(chunk)
        return h.hexdigest()


file_md5 = Hasher.file_md5
