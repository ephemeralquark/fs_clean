"""Tests for Formatter (human-readable sizes, group formatting)."""

from pathlib import Path

import dupes


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
