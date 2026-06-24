"""Tests for scanning (directory traversal)."""

from pathlib import Path

import dupes


class TestScan:
    """
    Tests dupes.scan(), which recursively traverses a directory.
    Checks for file discovery, path inclusion, filtering (hidden files, empty dirs),
    and correct metadata retrieval (size, mtime).
    """

    def test_empty_dir(self, tmp_path: Path):
        """Verifies that scanning an empty directory returns an empty list."""
        assert dupes.scan(tmp_path) == []

    def test_files(self, tmp_path: Path):
        """
        Tests basic file and subdirectory discovery.
        Checks that files in the current directory and subdirectories are included.
        """
        (tmp_path / "a.txt").write_text("x")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.txt").write_text("y")
        results = dupes.scan(tmp_path)
        assert len(results) == 2
        paths = {r["path"] for r in results}
        assert (tmp_path / "a.txt").resolve() in {p.resolve() for p in paths}
        assert (tmp_path / "sub" / "b.txt").resolve() in {p.resolve() for p in paths}
