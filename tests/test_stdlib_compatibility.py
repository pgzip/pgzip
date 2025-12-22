"""Test pgzip compatibility with stdlib gzip using adapted stdlib tests."""

import array
import gzip
import io
import os
import tempfile
import unittest

import pgzip

# Test data from stdlib
data1 = b"""  int length=DEFAULTALLOC, err = Z_OK;
  PyObject *RetVal;
  int flushmode = Z_FINISH;
  unsigned long start_total_out;

"""

data2 = b"""/* zlibmodule.c -- gzip-compatible data compression */
/* See http://www.gzip.org/zlib/
/* See http://www.winimage.com/zLibDll for Windows */
"""


class UnseekableIO(io.BytesIO):
    def seekable(self):
        return False

    def tell(self):
        raise io.UnsupportedOperation

    def seek(self, *args):
        raise io.UnsupportedOperation


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.filename = os.path.join(self.temp_dir, "test.gz")

    def tearDown(self):
        if os.path.exists(self.filename):
            os.unlink(self.filename)
        os.rmdir(self.temp_dir)


class TestPgzipStdlibCompatibility(BaseTest):
    """Test that pgzip behaves identically to stdlib gzip."""

    def write_and_read_back(self, data, mode="b"):
        """Test write/read cycle with both gzip and pgzip."""
        b_data = bytes(data)

        # Test with pgzip
        with pgzip.open(self.filename, "w" + mode) as f:
            l = f.write(data)
        self.assertEqual(l, len(b_data))

        # Verify pgzip file can be read by stdlib gzip
        with gzip.open(self.filename, "r" + mode) as f:
            self.assertEqual(f.read(), b_data)

        # Verify pgzip can read its own files
        with pgzip.open(self.filename, "r" + mode) as f:
            self.assertEqual(f.read(), b_data)

    def test_write(self):
        """Test basic write functionality."""
        with pgzip.open(self.filename, "wb") as f:
            f.write(data1 * 50)
            f.flush()
            f.fileno()
            if hasattr(os, "fsync"):
                os.fsync(f.fileno())
            f.close()

        # Test multiple close() calls
        f.close()

        # Verify with stdlib gzip
        with gzip.open(self.filename, "rb") as f:
            self.assertEqual(f.read(), data1 * 50)

    def test_write_memoryview(self):
        """Test write with memoryview input."""
        self.write_and_read_back(memoryview(data1 * 50))

    def test_write_bytearray(self):
        """Test write with bytearray input."""
        self.write_and_read_back(bytearray(data1 * 50))

    def test_write_array(self):
        """Test write with array input."""
        self.write_and_read_back(array.array("B", data1 * 50))

    def test_read(self):
        """Test basic read functionality."""
        # Create file with stdlib gzip
        with gzip.open(self.filename, "wb") as f:
            f.write(data1)

        # Read with pgzip
        with pgzip.open(self.filename, "rb") as f:
            self.assertEqual(f.read(), data1)

    def test_read1(self):
        """Test read1 method."""
        # Create file with stdlib gzip
        with gzip.open(self.filename, "wb") as f:
            f.write(data1 * 50)

        # Test read1 with pgzip
        with pgzip.open(self.filename, "rb") as f:
            d = f.read1()
            self.assertTrue(len(d) > 0)
            self.assertTrue(len(d) <= len(data1 * 50))

    def test_io_on_closed_object(self):
        """Test operations on closed file objects."""
        f = pgzip.open(self.filename, "wb")
        f.close()

        with self.assertRaises(ValueError):
            f.write(b"data")
        with self.assertRaises(ValueError):
            f.flush()

    def test_append(self):
        """Test append mode."""
        # Write initial data with pgzip
        with pgzip.open(self.filename, "wb") as f:
            f.write(data1)

        # Append more data with pgzip
        with pgzip.open(self.filename, "ab") as f:
            f.write(data2)

        # Verify with stdlib gzip
        with gzip.open(self.filename, "rb") as f:
            self.assertEqual(f.read(), data1 + data2)

    def test_many_append(self):
        """Test multiple append operations."""
        # Multiple appends
        for i in range(10):
            with pgzip.open(self.filename, "ab") as f:
                f.write(data1)

        # Verify with stdlib gzip
        with gzip.open(self.filename, "rb") as f:
            self.assertEqual(f.read(), data1 * 10)

    def test_buffered_reader(self):
        """Test buffered reading."""
        # Create file with stdlib gzip
        with gzip.open(self.filename, "wb") as f:
            f.write(data1 * 50)

        # Test buffered reading with pgzip
        with pgzip.open(self.filename, "rb") as f:
            # Read in chunks
            chunks = []
            while True:
                chunk = f.read(100)
                if not chunk:
                    break
                chunks.append(chunk)

            self.assertEqual(b"".join(chunks), data1 * 50)

    def test_readline(self):
        """Test readline functionality."""
        lines = [b"line1\n", b"line2\n", b"line3"]
        test_data = b"".join(lines)

        # Write with pgzip
        with pgzip.open(self.filename, "wb") as f:
            f.write(test_data)

        # Read lines with pgzip
        with pgzip.open(self.filename, "rb") as f:
            self.assertEqual(f.readline(), lines[0])
            self.assertEqual(f.readline(), lines[1])
            self.assertEqual(f.readline(), lines[2])
            self.assertEqual(f.readline(), b"")

    def test_readlines(self):
        """Test readlines functionality."""
        lines = [b"line1\n", b"line2\n", b"line3"]
        test_data = b"".join(lines)

        # Write with pgzip
        with pgzip.open(self.filename, "wb") as f:
            f.write(test_data)

        # Read all lines with pgzip
        with pgzip.open(self.filename, "rb") as f:
            self.assertEqual(f.readlines(), lines)

    def test_iteration(self):
        """Test file iteration."""
        lines = [b"line1\n", b"line2\n", b"line3\n"]
        test_data = b"".join(lines)

        # Write with pgzip
        with pgzip.open(self.filename, "wb") as f:
            f.write(test_data)

        # Iterate with pgzip
        with pgzip.open(self.filename, "rb") as f:
            result_lines = list(f)
            self.assertEqual(result_lines, lines)

    def test_text_mode(self):
        """Test text mode operations."""
        text_data = "Hello, 世界!\nLine 2\nLine 3"

        # Write in text mode with pgzip
        with pgzip.open(self.filename, "wt", encoding="utf-8") as f:
            f.write(text_data)

        # Read in text mode with pgzip
        with pgzip.open(self.filename, "rt", encoding="utf-8") as f:
            self.assertEqual(f.read(), text_data)

        # Verify with stdlib gzip
        with gzip.open(self.filename, "rt", encoding="utf-8") as f:
            self.assertEqual(f.read(), text_data)

    def test_compression_levels(self):
        """Test different compression levels."""
        for level in range(10):
            filename = f"{self.filename}.{level}"

            # Write with pgzip at different compression levels
            with pgzip.open(filename, "wb", compresslevel=level) as f:
                f.write(data1 * 100)

            # Verify with stdlib gzip
            with gzip.open(filename, "rb") as f:
                self.assertEqual(f.read(), data1 * 100)

            os.unlink(filename)

    def test_cross_compatibility(self):
        """Test that files created by gzip can be read by pgzip and vice versa."""
        # File created by stdlib gzip
        gzip_file = self.filename + ".gzip"
        with gzip.open(gzip_file, "wb") as f:
            f.write(data1 * 100)

        # Read with pgzip
        with pgzip.open(gzip_file, "rb") as f:
            gzip_data = f.read()

        # File created by pgzip
        pgzip_file = self.filename + ".pgzip"
        with pgzip.open(pgzip_file, "wb") as f:
            f.write(data1 * 100)

        # Read with stdlib gzip
        with gzip.open(pgzip_file, "rb") as f:
            pgzip_data = f.read()

        # Both should be identical
        self.assertEqual(gzip_data, pgzip_data)
        self.assertEqual(gzip_data, data1 * 100)

        os.unlink(gzip_file)
        os.unlink(pgzip_file)


if __name__ == "__main__":
    unittest.main()
