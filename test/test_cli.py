"""Tests for CLI (command-line interface)."""

import json
import os
import re
from pathlib import Path

import pytest

import dupes


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
