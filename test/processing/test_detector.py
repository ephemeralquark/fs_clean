"""Tests for DuplicationDetector (duplicate detection algorithm)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.processing.detector import DuplicationDetector
from src.processing.models import FileInfo, DuplicateGroup


class TestFindDuplicates:
    """Tests the core duplicate-detection algorithm."""

    def test_no_duplicates(self, tmp_path: Path):
        files = [
            FileInfo(path=tmp_path / "a.txt", size=10, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=20, mtime=2.0),
            FileInfo(path=tmp_path / "c.txt", size=30, mtime=3.0),
        ]
        groups = DuplicationDetector().find_duplicates(files)
        assert groups == []

    def test_same_size_different_content(self, tmp_path: Path):
        files = [
            FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        # Different content → different hashes → no duplicates
        groups = DuplicationDetector().find_duplicates(files)
        assert groups == []

    def test_same_content(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("hello")
        files = [
            FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        groups = DuplicationDetector().find_duplicates(files)
        assert len(groups) == 1
        assert len(groups[0].files) == 2

    def test_multiple_groups(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("group1")
        (tmp_path / "b.txt").write_text("group1")
        (tmp_path / "c.txt").write_text("group2")
        (tmp_path / "d.txt").write_text("group2")
        files = [
            FileInfo(path=tmp_path / "a.txt", size=6, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=6, mtime=2.0),
            FileInfo(path=tmp_path / "c.txt", size=6, mtime=3.0),
            FileInfo(path=tmp_path / "d.txt", size=6, mtime=4.0),
        ]
        groups = DuplicationDetector().find_duplicates(files)
        assert len(groups) == 2

    def test_three_way_duplicate(self, tmp_path: Path):
        for name in ("a.txt", "b.txt", "c.txt"):
            (tmp_path / name).write_text("triple")
        files = [
            FileInfo(path=tmp_path / n, size=6, mtime=float(i))
            for i, n in enumerate(["a.txt", "b.txt", "c.txt"], 1)
        ]
        groups = DuplicationDetector().find_duplicates(files)
        assert len(groups) == 1
        assert len(groups[0].files) == 3

    def test_oserror_during_hashing(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("data")
        (tmp_path / "b.txt").write_text("data")
        files = [
            FileInfo(path=tmp_path / "a.txt", size=4, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=4, mtime=2.0),
        ]
        # Make b.txt unreadable so hashing will OSError
        (tmp_path / "b.txt").chmod(0o000)
        groups = DuplicationDetector().find_duplicates(files)
        assert groups == []  # skipped due to error
        (tmp_path / "b.txt").chmod(0o644)  # restore for cleanup

    def test_custom_hasher(self):
        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "abc123"
        detector = DuplicationDetector(hasher=mock_hasher)
        files = [
            FileInfo(path=Path("/x"), size=10, mtime=1.0),
            FileInfo(path=Path("/y"), size=10, mtime=2.0),
        ]
        groups = detector.find_duplicates(files)
        assert len(groups) == 1
        assert mock_hasher.hash.call_count == 2

    def test_size_pre_filtering(self, tmp_path: Path):
        files = [
            FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
            FileInfo(path=tmp_path / "c.txt", size=100, mtime=3.0),
        ]
        groups = DuplicationDetector().find_duplicates(files)
        assert len(groups) == 0  # c.txt filtered by size alone


class TestDuplicateGroup:
    """Tests DuplicateGroup named tuple."""

    def test_fields(self):
        group = DuplicateGroup(size=10, md5="abc", files=["a", "b"])
        assert group.size == 10
        assert group.md5 == "abc"
        assert group.files == ["a", "b"]  # namedtuple preserves original list

    def test_access_by_index(self):
        group = DuplicateGroup(size=10, md5="abc", files=[Path("/x")])
        assert group[0] == 10
        assert group[1] == "abc"
        assert len(group.files) == 1

    def test_unpacking(self):
        group = DuplicateGroup(size=10, md5="abc", files=[Path("/x")])
        size, md5, files = group
        assert size == 10
        assert md5 == "abc"
        assert len(files) == 1
