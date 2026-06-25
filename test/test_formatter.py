"""Tests for Formatter (output rendering)."""

from pathlib import Path

import src


class TestHuman:
    """Tests Formatter._human() byte-to-human conversion."""

    def test_bytes(self):
        f = src.Formatter()._human
        assert f(0) == "0.0 B"
        assert f(1) == "1.0 B"
        assert f(999) == "999.0 B"

    def test_kilobytes(self):
        f = src.Formatter()._human
        assert f(1024) == "1.0 KB"
        assert f(1536) == "1.5 KB"
        assert f(10240) == "10.0 KB"

    def test_megabytes(self):
        f = src.Formatter()._human
        assert f(1048576) == "1.0 MB"
        assert f(5242880) == "5.0 MB"

    def test_gigabytes(self):
        f = src.Formatter()._human
        assert f(1073741824) == "1.0 GB"

    def test_terabytes(self):
        f = src.Formatter()._human
        assert f(1099511627776) == "1.0 TB"

    def test_petabytes(self):
        f = src.Formatter()._human
        assert f(1099511627776 * 1024) == "1.0 PB"


class TestFormatGroups:
    """Tests Formatter.format_groups() end-to-end output."""

    def test_text_output(self, tmp_path: Path):
        files = [
            src.FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            src.FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        group = src.DuplicateGroup(size=5, md5="abc", files=files)
        output = src.Formatter().format_groups([group])
        assert "Group 1" in output
        assert "(5.0 B each, 2 copies" in output
        assert "recoverable" in output

    def test_json_output(self, tmp_path: Path):
        import json
        files = [
            src.FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            src.FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        group = src.DuplicateGroup(size=5, md5="abc", files=files)
        output = src.Formatter().format_groups_json([group])
        data = json.loads(output)
        assert data["total_groups"] == 1
        assert len(data["groups"][0]["files"]) == 2
        assert data["groups"][0]["md5"] == "abc"
