"""Tests for CLI (command-line interface)."""

import json
import re
from pathlib import Path

import pytest

import src


class TestCLI:
    """Tests the command-line execution paths of the tool."""

    def test_nonexistent_dir(self, capsys):
        with pytest.raises(SystemExit):
            src.main(["/no/such/dir"])
        assert "does not exist" in capsys.readouterr().err

    def test_text_output(self, tmp_path: Path, capsys):
        (tmp_path / "a").write_text("same")
        (tmp_path / "b").write_text("same")
        src.main([str(tmp_path)])
        captured = capsys.readouterr()
        assert "Group 1" in captured.out
        assert "recoverable" in captured.out

    def test_json_output(self, tmp_path: Path, capsys):
        (tmp_path / "a").write_text("same")
        (tmp_path / "b").write_text("same")
        src.main([str(tmp_path), "--format", "json"])
        captured = capsys.readouterr()
        json_match = re.search(r"(\{[\s\S]*\})", captured.out)
        assert json_match is not None
        data = json.loads(json_match.group(1))
        assert data["total_groups"] == 1
        assert len(data["groups"][0]["files"]) == 2
        assert "md5" in data["groups"][0]

    def test_dry_run_delete(self, tmp_path: Path, capsys):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("same")
        b.write_text("same")
        src.main([str(tmp_path), "--dry-run", "--delete"])
        captured = capsys.readouterr()
        assert "Would delete" in captured.out
        assert a.exists()
        assert b.exists()

    def test_actual_delete(self, tmp_path: Path, capsys):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.write_text("same")
        b.write_text("same")
        src.main([str(tmp_path), "--delete"])
        captured = capsys.readouterr()
        assert "Deleted" in captured.out
        assert a.exists()  # kept
        assert not b.exists()  # deleted

    def test_min_size_filter(self, tmp_path: Path, capsys):
        (tmp_path / "a").write_text("tiny")
        (tmp_path / "b").write_text("tiny")
        (tmp_path / "c").write_text("larger file content")
        (tmp_path / "d").write_text("larger file content")
        src.main([str(tmp_path), "--min-size", "20"])
        captured = capsys.readouterr()
        assert "Group 1" not in captured.out

    def test_help(self, capsys):
        with pytest.raises(SystemExit):
            src.main(["--help"])
        captured = capsys.readouterr()
        assert "Find duplicate files" in captured.out


class TestDuplicateFinder:
    """Tests DuplicateFinder orchestrator via dependency injection."""

    def test_text_output_format(self, tmp_path: Path):
        files = [
            src.FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            src.FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        group = src.DuplicateGroup(size=5, md5="abc", files=files)
        finder = src.DuplicateFinder(formatter=src.Formatter())
        output = finder.text_output([group])
        assert "Group 1" in output
        assert "<- keep" in output

    def test_json_output_format(self, tmp_path: Path):
        files = [
            src.FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            src.FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        group = src.DuplicateGroup(size=5, md5="abc", files=files)
        finder = src.DuplicateFinder(formatter=src.Formatter())
        output = finder.json_output([group])
        data = json.loads(output)
        assert data["total_groups"] == 1


class TestDeleter:
    """Tests Deleter domain class."""

    def test_list_deletions(self, tmp_path: Path):
        files = [
            src.FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            src.FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
            src.FileInfo(path=tmp_path / "c.txt", size=5, mtime=3.0),
        ]
        group = src.DuplicateGroup(size=5, md5="abc", files=files)
        deleter = src.Deleter()
        result = deleter.list_deletions(group)
        assert len(result) == 2
        assert str(tmp_path / "b.txt") in result
        assert str(tmp_path / "c.txt") in result

    def test_dry_run_delete(self, tmp_path: Path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("same")
        b.write_text("same")
        files = [
            src.FileInfo(path=a, size=4, mtime=1.0),
            src.FileInfo(path=b, size=4, mtime=2.0),
        ]
        group = src.DuplicateGroup(size=4, md5="abc", files=files)
        deleter = src.Deleter()
        result = deleter.delete_group(group, dry_run=True)
        assert len(result) == 1
        assert result[0][0] == "Would delete"
        assert a.exists()
        assert b.exists()

    def test_actual_delete(self, tmp_path: Path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        c = tmp_path / "c.txt"
        a.write_text("same")
        b.write_text("same")
        c.write_text("same")
        files = [
            src.FileInfo(path=a, size=4, mtime=1.0),
            src.FileInfo(path=b, size=4, mtime=2.0),
            src.FileInfo(path=c, size=4, mtime=3.0),
        ]
        group = src.DuplicateGroup(size=4, md5="abc", files=files)
        deleter = src.Deleter()
        result = deleter.delete_group(group, dry_run=False)
        assert len(result) == 2
        assert all(r[0] == "Deleted" for r in result)
        assert a.exists()
        assert not b.exists()
        assert not c.exists()


class TestIntegration:
    """End-to-end workflow combining scanning and duplicate detection."""

    def test_complex_tree(self, tmp_path: Path):
        root = tmp_path
        (root / "a.txt").write_text("copy1")
        (root / "sub1" / "b.txt").parent.mkdir(parents=True, exist_ok=True)
        (root / "sub1" / "b.txt").write_text("copy1")
        (root / "sub1" / "sub2" / "c.txt").parent.mkdir(parents=True, exist_ok=True)
        (root / "sub1" / "sub2" / "c.txt").write_text("copy1")
        (root / "sub2" / "d.txt").parent.mkdir(parents=True, exist_ok=True)
        (root / "sub2" / "d.txt").write_text("copy1")
        (root / "unique.txt").write_text("only one")

        scanner = src.Scanner()
        detector = src.DuplicationDetector()
        files = scanner.scan(root)
        groups = detector.find_duplicates(files)

        assert len(groups) == 1
        assert len(groups[0].files) == 4
        expected_paths = {
            root / "a.txt",
            root / "sub1" / "b.txt",
            root / "sub1" / "sub2" / "c.txt",
            root / "sub2" / "d.txt",
        }
        actual_paths = {f.path for f in groups[0].files}
        assert expected_paths == actual_paths


class TestFileInfo:
    """Tests FileInfo model."""

    def test_frozen(self, tmp_path: Path):
        info = src.FileInfo(path=Path(tmp_path), size=10, mtime=1.0)
        with pytest.raises(Exception):
            info.path = Path("/tmp/y")  # pyright: ignore[reportAttributeAccessIssue]

    def test_resolves_relative_path(self):
        abs_path = Path.cwd() / "x.txt"
        info = src.FileInfo(path=Path("x.txt"), size=10, mtime=1.0)
        assert info.path == abs_path
