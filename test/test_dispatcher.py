"""Tests for the Dispatcher orchestrator."""

import json
from pathlib import Path

import pytest

from src.dispatcher import Dispatcher
from src.input.scanner import Scanner
from src.processing.detector import DuplicationDetector
from src.processing.models import FileInfo, DuplicateGroup
from src.output.formatter import Formatter
from src.action.deleter import Deleter


class TestDispatcher:
    """Tests Dispatcher orchestrator via dependency injection."""

    def test_text_output_format(self, tmp_path: Path):
        files = [
            FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        group = DuplicateGroup(size=5, md5="abc", files=files)
        dispatcher = Dispatcher(formatter=Formatter())
        output = dispatcher.text_output([group])
        assert "Group 1" in output
        assert "<- keep" in output

    def test_json_output_format(self, tmp_path: Path):
        files = [
            FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
        ]
        group = DuplicateGroup(size=5, md5="abc", files=files)
        dispatcher = Dispatcher(formatter=Formatter())
        output = dispatcher.json_output([group])
        data = json.loads(output)
        assert data["total_groups"] == 1

    def test_scan_and_find(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("same")
        (tmp_path / "b.txt").write_text("same")
        dispatcher = Dispatcher(
            scanner=Scanner(),
            detector=DuplicationDetector()
        )
        groups = dispatcher.scan_and_find(tmp_path)
        assert len(groups) == 1
        assert len(groups[0].files) == 2

    def test_scan_and_find_min_size(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("tiny")
        (tmp_path / "b.txt").write_text("tiny")
        (tmp_path / "c.txt").write_text("larger file content!")
        (tmp_path / "d.txt").write_text("larger file content!")
        dispatcher = Dispatcher(
            scanner=Scanner(),
            detector=DuplicationDetector()
        )
        groups = dispatcher.scan_and_find(tmp_path, min_size=20)
        assert len(groups) == 1
        assert all(g.size >= 20 for g in groups)

    def test_defaults_all_components(self):
        """When no dependencies are injected, all defaults should be used."""
        dispatcher = Dispatcher()
        assert isinstance(dispatcher.scanner, Scanner)
        assert isinstance(dispatcher.detector, DuplicationDetector)
        assert isinstance(dispatcher.formatter, Formatter)
        assert isinstance(dispatcher.deleter, Deleter)
