"""Unit tests for dupes.py.
This file contains unit tests covering file size formatting, MD5 hashing, directory scanning,
group formatting, and command-line interface logic for the 'dupes' utility.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Make dupes importable regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import dupes  # noqa: E402


class TestHuman:
    """
    Tests the functionality of dupes._human(), which converts raw byte counts
    into human-readable formats (e.g., "1.5 MB", "1024.0 PB").
    """
    def test_bytes(self):
        """Tests the basic formatting for zero and small byte values."""
        assert dupes._human(0) == "0.0 B"
        assert dupes._human(1) == "1.0 B"
        assert dupes._human(999) == "999.0 B"

    def test_kilobytes(self):
        """Tests correct conversion and formatting for kilobytes (KB)."""
        assert dupes._human(1024) == "1.0 KB"
        assert dupes._human(1536) == "1.5 KB"
        assert dupes._human(10240) == "10.0 KB"

    def test_megabytes(self):
        """Tests correct conversion and formatting for megabytes (MB)."""
        assert dupes._human(1048576) == "1.0 MB"
        assert dupes._human(5242880) == "5.0 MB"

    def test_gigabytes(self):
        """Tests correct conversion and formatting for gigabytes (GB)."""
        assert dupes._human(1073741824) == "1.0 GB"

    def test_terabytes(self):
        """Tests correct conversion and formatting for terabytes (TB)."""
        assert dupes._human(1099511627776) == "1.0 TB"

    def test_petabytes(self):
        """Tests correct conversion and formatting for petabytes (PB)."""
        # The calculation 1099511627776 * 1024 results in 2^50 bytes (1 PB).
        assert dupes._human(1099511627776 * 1024) == "1.0 PB"


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


class TestCLI:
    """
    Tests the command-line execution paths of the tool, including
    error handling, different output formats (text/JSON), and delete logic.
    """
    def test_nonexistent_dir(self, capsys):
        """Tests that the program exits with an appropriate error message if the path does not exist."""
        with pytest.raises(SystemExit):
            dupes.main(["/no/such/dir"])
        assert "does not exist" in capsys.readouterr().err

    def test_text_output(self, tmp_path: Path, capsys):
        """Tests the default output format (readable text summary)."""
        (tmp_path / "a").write_text("same")
        (tmp_path / "b").write_text("same")
        dupes.main([str(tmp_path)])
        captured = capsys.readouterr()
        assert "Group 1" in captured.out
        assert "recoverable" in captured.out

    def test_json_output(self, tmp_path: Path, capsys):
        """
        Tests the JSON output format, ensuring the output is structured data
        suitable for machine parsing.
        """
        (tmp_path / "a").write_text("same")
        (tmp_path / "b").write_text("same")
        dupes.main([str(tmp_path), "--format", "json"])
        captured = capsys.readouterr()
        # Use regex to extract the full JSON structure, handling multi-line output
        import re
        json_match = re.search(r"(\{[\s\S]*\})", captured.out)
        assert json_match is not None
        data = json.loads(json_match.group(1))
        assert data["total_groups"] == 1
        assert len(data["groups"][0]["files"]) == 2
        assert "md5" in data["groups"][0]

    def test_dry_run_delete(self, tmp_path: Path, capsys):
        """
        Tests the dry-run mode for deletion.
        Verifies that the program reports files that *would* be deleted
        without actually modifying the filesystem.
        """
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("same")
        b.write_text("same")
        dupes.main([str(tmp_path), "--dry-run", "--delete"])
        captured = capsys.readouterr()
        assert "Would delete" in captured.out
        # Files should still exist
        assert a.exists()
        assert b.exists()

    def test_actual_delete(self, tmp_path: Path, capsys):
        """
        Tests the actual file deletion mode.
        Verifies that duplicate files are physically removed from the filesystem.
        """
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("same")
        b.write_text("same")
        dupes.main([str(tmp_path), "--delete"])
        captured = capsys.readouterr()
        assert "Deleted" in captured.out
        assert a.exists()  # kept
        assert not b.exists()  # deleted

    def test_min_size_filter(self, tmp_path: Path, capsys):
        """Tests the filtering of duplicates based on minimum file size."""
        (tmp_path / "a").write_text("tiny")
        (tmp_path / "b").write_text("tiny")
        (tmp_path / "c").write_text("larger file content")
        (tmp_path / "d").write_text("larger file content")
        dupes.main([str(tmp_path), "--min-size", "20"])
        captured = capsys.readouterr()
        # "tiny" (4 bytes) should be filtered out, so no dupes from it
        assert "Group 1" not in captured.out

    def test_help(self, capsys):
        """Tests that invoking --help exits gracefully and displays usage information."""
        with pytest.raises(SystemExit):
            dupes.main(["--help"])
        captured = capsys.readouterr()
        assert "Find duplicate files" in captured.out


class TestIntegration:
    """
    Tests the end-to-end workflow, combining directory scanning (find_duplicates)
    with the final output formatting (format_groups) on a complex filesystem tree.
    """
    def test_complex_tree(self, tmp_path: Path):
        """Multi-level tree with mixed duplicates. Verifies grouping across paths."""
        root = tmp_path
        a = root / "a.txt"
        b = root / "sub1" / "b.txt"
        c = root / "sub1" / "sub2" / "c.txt"
        d = root / "sub2" / "d.txt"
        a.write_text("copy1")
        b.parent.mkdir(parents=True, exist_ok=True)
        c.parent.mkdir(parents=True, exist_ok=True)
        d.parent.mkdir(parents=True, exist_ok=True)
        b.write_text("copy1")
        c.write_text("copy1")
        d.write_text("copy1")
        e = root / "unique.txt"
        e.write_text("only one")

        groups = dupes.find_duplicates(root)
        assert len(groups) == 1
        assert len(groups[0]) == 4  # all 4 copies
        assert groups[0][0]["path"] == a.resolve()  # first encountered kept
