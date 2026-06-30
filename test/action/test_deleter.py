"""Tests for Deleter (intelligent duplicate file deletion)."""

from __future__ import annotations

import pytest
from pathlib import Path

from src.action.deleter import Deleter
from src.processing.models import DuplicateGroup, FileInfo
from src.utils.file_heuristics import calculate_heuristic_score, passes_filter


# -- Heuristic scoring tests ------------------------------------------------

class TestCalculateHeuristicScore:
    """Verify that the scoring function ranks files as expected."""

    def test_version_number(self):
        score_v2 = calculate_heuristic_score(Path("photo_v2.jpg"))
        score_v1 = calculate_heuristic_score(Path("photo_v1.jpg"))
        assert score_v2 > score_v1  # v2 beats v1

    def test_older_version_has_lower_score(self):
        files = [
            Path("release_v3_final.png"),
            Path("release_v2.png"),
            Path("release_v1.png"),
            Path("release.png"),
        ]
        ranked = sorted(files, key=calculate_heuristic_score, reverse=True)
        assert ranked == files  # highest version/release first

    def test_iso_date_increases_score(self):
        score_dated = calculate_heuristic_score(Path("photo_2024-01-15.jpg"))
        score_undated = calculate_heuristic_score(Path("photo_copy.jpg"))
        assert score_dated > score_undated

    def test_release_words_boost_score(self):
        score_release = calculate_heuristic_score(Path("image_release.jpg"))
        score_normal = calculate_heuristic_score(Path("image_copy.jpg"))
        assert score_release > score_normal

    def test_all_equal_scores(self):
        scores = [calculate_heuristic_score(Path(f"dup{i}.jpg")) for i in range(3)]
        assert all(s == scores[0] for s in scores)  # no pattern -> all equal


class TestPassesFilter:
    """Verify type filtering works correctly."""

    def test_media_filter(self):
        assert passes_filter(Path("vid.mp4"), "media") is True
        assert passes_filter(Path("img.jpg"), "media") is True
        assert passes_filter(Path("code.py"), "media") is False

    def test_code_filter(self):
        assert passes_filter(Path("main.py"), "code") is True
        assert passes_filter(Path("script.js"), "code") is True
        assert passes_filter(Path("pic.jpg"), "code") is False

    def test_none_passes_all(self):
        assert passes_filter(Path("anything.xyz"), None) is True

    def test_unknown_filter_passes_all(self):
        assert passes_filter(Path("file.txt"), "unknown") is True


# -- Deleter delete_group tests ----------------------------------------------

class TestDeleteGroup:
    """Tests for the new heuristic-based deletion logic."""

    @pytest.fixture
    def deleter(self):
        return Deleter()

    @pytest.fixture
    def simple_group(self, tmp_path: Path) -> DuplicateGroup:
        """Three files with identical content, no naming patterns."""
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("hello")
        (tmp_path / "c.txt").write_text("hello")
        files = [
            FileInfo(path=tmp_path / "a.txt", size=5, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=5, mtime=2.0),
            FileInfo(path=tmp_path / "c.txt", size=5, mtime=3.0),
        ]
        return DuplicateGroup(size=5, md5="abc", files=files)

    def test_dry_run(self, deleter: Deleter, simple_group: DuplicateGroup):
        results = deleter.delete_group(simple_group, dry_run=True)
        assert len(results) == 2
        assert all(status == "Would delete" for status, _ in results)

    def test_live_delete(self, deleter: Deleter, tmp_path: Path):
        (tmp_path / "a.txt").write_text("data")
        (tmp_path / "b.txt").write_text("data")
        (tmp_path / "c.txt").write_text("data")
        files = [
            FileInfo(path=tmp_path / "a.txt", size=4, mtime=1.0),
            FileInfo(path=tmp_path / "b.txt", size=4, mtime=2.0),
            FileInfo(path=tmp_path / "c.txt", size=4, mtime=3.0),
        ]
        group = DuplicateGroup(size=4, md5="xyz", files=files)

        results = deleter.delete_group(group, dry_run=False)
        assert len(results) == 2
        assert all(status == "Deleted" for status, _ in results)
        # Only one file should remain
        remaining = [f for f in files if f.path.exists()]
        assert len(remaining) == 1

    def test_higher_version_kept(self, deleter: Deleter, tmp_path: Path):
        """File with 'v2' in the name should be kept over v1 and bare copy."""
        (tmp_path / "photo_v1.jpg").write_bytes(b"img")
        (tmp_path / "photo_v2.jpg").write_bytes(b"img")
        (tmp_path / "photo_copy.jpg").write_bytes(b"img")
        files = [
            FileInfo(path=tmp_path / "photo_v1.jpg", size=3, mtime=1.0),
            FileInfo(path=tmp_path / "photo_v2.jpg", size=3, mtime=2.0),
            FileInfo(path=tmp_path / "photo_copy.jpg", size=3, mtime=3.0),
        ]
        group = DuplicateGroup(size=3, md5="img", files=files)

        results = deleter.delete_group(group, dry_run=True)
        deleted_paths = {path for _, path in results}
        assert str(tmp_path / "photo_v2.jpg") not in deleted_paths  # kept!
        assert str(tmp_path / "photo_v1.jpg") in deleted_paths
        assert str(tmp_path / "photo_copy.jpg") in deleted_paths

    def test_filter_media_only(self, deleter: Deleter, tmp_path: Path):
        """Media filter should ignore code files entirely."""
        (tmp_path / "img.mp4").write_bytes(b"video")
        (tmp_path / "img_copy.mp4").write_bytes(b"video")
        # Same hash for the two media files; Python is a different file
        (tmp_path / "code.py").write_text("code")
        code_file = FileInfo(path=tmp_path / "code.py", size=4, mtime=1.0)

        group = DuplicateGroup(
            size=5, md5="vid",
            files=[
                FileInfo(path=tmp_path / "img.mp4", size=5, mtime=1.0),
                FileInfo(path=tmp_path / "img_copy.mp4", size=5, mtime=2.0),
                code_file,
            ],
        )

        # With media filter, only the two mp4 files are candidates
        results = deleter.delete_group(group, dry_run=True, filter_type="media")
        assert len(results) == 1
        # The Python file should NOT be in the results
        deleted_paths = {path for _, path in results}
        assert str(tmp_path / "code.py") not in deleted_paths

    def test_filter_all_code_filtered_out(self, deleter: Deleter, tmp_path: Path):
        """If filter removes all members from a group, nothing happens."""
        (tmp_path / "img.jpg").write_bytes(b"pic")
        (tmp_path / "img_copy.jpg").write_bytes(b"pic")
        code_file = FileInfo(path=tmp_path / "main.py", size=4, mtime=1.0)

        group = DuplicateGroup(
            size=5, md5="pic",
            files=[
                FileInfo(path=tmp_path / "img.jpg", size=5, mtime=1.0),
                code_file,
                FileInfo(path=tmp_path / "img_copy.jpg", size=5, mtime=3.0),
            ],
        )

        # Filter for code -> only 1 candidate (main.py) -> nothing to delete
        results = deleter.delete_group(group, dry_run=True, filter_type="code")
        assert len(results) == 0

    def test_early_exit_single_candidate(self, deleter: Deleter):
        """Edge case: group with only one file -> no-op."""
        files = [FileInfo(path=Path("/tmp/single.txt"), size=10, mtime=1.0)]
        group = DuplicateGroup(size=10, md5="z", files=files)
        results = deleter.delete_group(group, dry_run=True)
        assert results == []


class TestListDeletions:
    """Regression test for the deprecated helper."""

    def test_returns_all_but_first(self):
        group = DuplicateGroup(
            size=10, md5="abc",
            files=[FileInfo(path=Path("/a"), size=10, mtime=1.0),
                   FileInfo(path=Path("/b"), size=10, mtime=2.0),
                   FileInfo(path=Path("/c"), size=10, mtime=3.0)],
        )
        deleter = Deleter()
        paths = deleter.list_deletions(group)
        assert paths == ["/b", "/c"]
