"""Tests for Hasher (MD5 file hashing)."""

import os
from pathlib import Path

import pytest

import dupes


class TestFileMd5:
    """
    Validates the content hashing functionality (file_md5) used by the utility
    to determine if files are duplicates. This class ensures the MD5 hash correctly
    reflects the file's actual content, covering edge cases such as empty files,
    files with specific known content, and proper handling of file read permission errors.
    """

    def test_empty_file(self, tmp_path: Path):
        """Verifies that the MD5 hash for an empty file is correct."""
        f = tmp_path / "empty"
        f.touch()
        assert dupes.file_md5(f) == "d41d8cd98f00b204e9800998ecf8427e"

    def test_known_content(self, tmp_path: Path):
        """Verifies the MD5 hash for a standard known string ('hello')."""
        f = tmp_path / "hello"
        f.write_text("hello", encoding="utf-8")
        assert dupes.file_md5(f) == "5d41402abc4b2a76b9719d911017c592"

    def test_large_file(self, tmp_path: Path):
        """
        Tests hashing consistency and correctness for large files,
        simulating a multi-block read scenario.
        """
        f = tmp_path / "big"
        data = os.urandom(200_000)
        f.write_bytes(data)
        expected = dupes.file_md5(tmp_path / "big")
        # Read twice with different instances should match
        assert dupes.file_md5(f) == expected

    def test_permission_error(self, tmp_path: Path):
        """
        Ensures the utility gracefully handles files where read permissions are denied.
        It should raise an OSError.
        """
        f = tmp_path / "nope"
        f.touch()
        f.chmod(0o000)
        with pytest.raises(OSError):
            dupes.file_md5(f)
        f.chmod(0o644)  # restore so cleanup works
