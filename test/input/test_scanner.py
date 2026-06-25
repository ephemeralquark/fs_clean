"""Tests for Scanner (directory traversal)."""

from pathlib import Path

from src.input.scanner import Scanner


class TestScan:
    """Tests Scanner.scan()."""

    def test_empty_dir(self, tmp_path: Path):
        scanner = Scanner()
        assert scanner.scan(tmp_path) == []

    def test_files(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("x")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.txt").write_text("y")
        results = Scanner().scan(tmp_path)
        assert len(results) == 2
        paths = {r.path for r in results}
        assert (tmp_path / "a.txt").resolve() in paths
        assert (tmp_path / "sub" / "b.txt").resolve() in paths

    def test_skip_hidden(self, tmp_path: Path):
        (tmp_path / ".hidden_file").write_text("x")
        hidden_dir = tmp_path / ".hidden_dir"
        hidden_dir.mkdir()
        (hidden_dir / "inside.txt").write_text("y")
        (tmp_path / "visible.txt").write_text("z")
        results = Scanner().scan(tmp_path)
        assert len(results) == 1
        assert (tmp_path / "visible.txt").resolve() in {r.path for r in results}

    def test_skip_sizes(self, tmp_path: Path):
        (tmp_path / "zero.txt").write_text("")
        (tmp_path / "nonzero.txt").write_text("hello")
        scanner = Scanner()
        results = scanner.scan(tmp_path, skip_sizes={0})
        assert len(results) == 1
        assert results[0].path.name == "nonzero.txt"

    def test_metadata(self, tmp_path: Path):
        f = tmp_path / "meta.txt"
        f.write_text("data")
        info = Scanner().scan(tmp_path)[0]
        assert info.size == 4
        assert isinstance(info.mtime, float)
