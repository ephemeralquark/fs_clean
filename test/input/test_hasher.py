"""Tests for Hasher (MD5 file hashing)."""

import os
from pathlib import Path

import pytest

import src


class TestFileMd5:
    """Validates the content hashing functionality used to detect duplicates."""

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty"
        f.touch()
        assert src.Hasher().hash(f) == "d41d8cd98f00b204e9800998ecf8427e"

    def test_known_content(self, tmp_path: Path):
        f = tmp_path / "hello"
        f.write_text("hello", encoding="utf-8")
        assert src.Hasher().hash(f) == "5d41402abc4b2a76b9719d911017c592"

    def test_large_file(self, tmp_path: Path):
        f = tmp_path / "big"
        data = os.urandom(200_000)
        f.write_bytes(data)
        first = src.Hasher().hash(f)
        second = src.Hasher().hash(f)
        assert first == second

    def test_permission_error(self, tmp_path: Path):
        f = tmp_path / "nope"
        f.touch()
        f.chmod(0o000)
        with pytest.raises(OSError):
            src.Hasher().hash(f)
        f.chmod(0o644)  # restore so cleanup works

    def test_custom_buf_size(self, tmp_path: Path):
        f = tmp_path / "chunked"
        f.write_text("hello world")
        h1 = src.Hasher().hash(f, buf_size=3)
        h2 = src.Hasher().hash(f, buf_size=65536)
        assert h1 == h2
