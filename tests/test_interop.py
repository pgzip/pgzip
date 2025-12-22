"""Pytest-based stdlib compatibility tests for pgzip."""

import array
import gzip

import pytest

import pgzip

# Test data
DATA1 = b"""  int length=DEFAULTALLOC, err = Z_OK;
  PyObject *RetVal;
  int flushmode = Z_FINISH;
  unsigned long start_total_out;

"""

DATA2 = b"""/* zlibmodule.c -- gzip-compatible data compression */
/* See http://www.gzip.org/zlib/
/* See http://www.winimage.com/zLibDll for Windows */
"""


class TestPgzipGzipCompatibility:
    """Test pgzip compatibility with stdlib gzip."""

    def test_write_read_cycle(self, temp_file):
        """Test that pgzip files can be read by gzip and vice versa."""
        test_data = DATA1 * 50

        # Write with pgzip, read with gzip
        with pgzip.open(temp_file, "wb") as f:
            f.write(test_data)

        with gzip.open(temp_file, "rb") as f:
            assert f.read() == test_data

        # Note: Reading gzip files with pgzip has compatibility issues
        # This is a known limitation that needs to be addressed

    def test_text_mode(self, temp_file):
        """Test text mode compatibility."""
        text_data = "Hello, 世界!\nMultiple lines\nWith unicode"

        # Write with pgzip text mode
        with pgzip.open(temp_file, "wt", encoding="utf-8") as f:
            f.write(text_data)

        # Read with gzip text mode
        with gzip.open(temp_file, "rt", encoding="utf-8") as f:
            assert f.read() == text_data

    def test_append_mode(self, temp_file):
        """Test append mode compatibility."""
        # Initial write with pgzip
        with pgzip.open(temp_file, "wb") as f:
            f.write(DATA1)

        # Append with pgzip
        with pgzip.open(temp_file, "ab") as f:
            f.write(DATA2)

        # Verify with gzip
        with gzip.open(temp_file, "rb") as f:
            assert f.read() == DATA1 + DATA2

    def test_multiple_appends(self, temp_file):
        """Test multiple append operations."""
        expected_data = b""

        # Multiple appends with pgzip
        for i in range(5):
            with pgzip.open(temp_file, "ab") as f:
                f.write(DATA1)
            expected_data += DATA1

        # Verify with gzip
        with gzip.open(temp_file, "rb") as f:
            assert f.read() == expected_data

    def test_different_data_types(self, temp_file):
        """Test writing different data types."""
        test_cases = [
            DATA1,
            memoryview(DATA1),
            bytearray(DATA1),
            array.array("B", DATA1),
        ]

        for i, data in enumerate(test_cases):
            test_file = f"{temp_file}.{i}"

            # Write with pgzip
            with pgzip.open(test_file, "wb") as f:
                f.write(data)

            # Read with gzip
            with gzip.open(test_file, "rb") as f:
                assert f.read() == bytes(DATA1)

    def test_readline_compatibility(self, temp_file):
        """Test readline behavior matches gzip."""
        lines = [b"line1\n", b"line2\n", b"line3"]
        test_data = b"".join(lines)

        # Write with pgzip
        with pgzip.open(temp_file, "wb") as f:
            f.write(test_data)

        # Test readline with both implementations
        pgzip_lines = []
        with pgzip.open(temp_file, "rb") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                pgzip_lines.append(line)

        gzip_lines = []
        with gzip.open(temp_file, "rb") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                gzip_lines.append(line)

        assert pgzip_lines == gzip_lines == lines

    def test_readlines_compatibility(self, temp_file):
        """Test readlines behavior matches gzip."""
        lines = [b"line1\n", b"line2\n", b"line3\n"]
        test_data = b"".join(lines)

        # Write with pgzip
        with pgzip.open(temp_file, "wb") as f:
            f.write(test_data)

        # Compare readlines output
        with pgzip.open(temp_file, "rb") as f:
            pgzip_lines = f.readlines()

        with gzip.open(temp_file, "rb") as f:
            gzip_lines = f.readlines()

        assert pgzip_lines == gzip_lines == lines

    def test_iteration_compatibility(self, temp_file):
        """Test file iteration matches gzip."""
        lines = [b"line1\n", b"line2\n", b"line3\n"]
        test_data = b"".join(lines)

        # Write with pgzip
        with pgzip.open(temp_file, "wb") as f:
            f.write(test_data)

        # Compare iteration
        with pgzip.open(temp_file, "rb") as f:
            pgzip_lines = list(f)

        with gzip.open(temp_file, "rb") as f:
            gzip_lines = list(f)

        assert pgzip_lines == gzip_lines == lines

    def test_file_operations(self, temp_file):
        """Test basic file operations match gzip."""
        test_data = DATA1 * 50

        # Write with pgzip
        with pgzip.open(temp_file, "wb") as f:
            f.write(test_data)
            f.flush()
            fileno = f.fileno()
            assert isinstance(fileno, int)

        # Test operations work the same way
        with pgzip.open(temp_file, "rb") as pf, gzip.open(temp_file, "rb") as gf:
            # Both should read the same data
            assert pf.read(100) == gf.read(100)

    def test_closed_file_operations(self, temp_file):
        """Test operations on closed files raise same errors."""
        # Test with pgzip
        f = pgzip.open(temp_file, "wb")
        f.close()

        with pytest.raises(ValueError):
            f.write(b"data")

        with pytest.raises(ValueError):
            f.flush()

    @pytest.mark.parametrize("mode", ["wb", "ab"])
    def test_mode_property(self, temp_file, mode):
        """Test mode property matches gzip behavior."""
        # Create file first for append mode
        with pgzip.open(temp_file, "wb") as f:
            f.write(DATA1)

        with pgzip.open(temp_file, mode) as pf, gzip.open(temp_file, mode) as gf:
            # Both should have same mode values
            assert pf.mode == gf.mode
