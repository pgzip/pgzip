"""Run stdlib gzip tests against pgzip by monkey-patching."""

import gzip
import os
import tempfile

import pytest

import pgzip


class StdlibTestRunner:
    """Run stdlib gzip tests against pgzip implementation."""

    def __init__(self):
        self.original_gzip = None

    def patch_gzip_module(self):
        """Replace gzip module functions with pgzip equivalents."""
        self.original_gzip = {
            "open": gzip.open,
            "GzipFile": gzip.GzipFile,
            "compress": gzip.compress,
            "decompress": gzip.decompress,
        }

        # Monkey patch gzip module
        gzip.open = pgzip.open
        gzip.GzipFile = pgzip.PgzipFile
        gzip.compress = pgzip.compress
        gzip.decompress = pgzip.decompress

    def restore_gzip_module(self):
        """Restore original gzip module."""
        if self.original_gzip:
            gzip.open = self.original_gzip["open"]
            gzip.GzipFile = self.original_gzip["GzipFile"]
            gzip.compress = self.original_gzip["compress"]
            gzip.decompress = self.original_gzip["decompress"]


# Test data from stdlib
data1 = b"""  int length=DEFAULTALLOC, err = Z_OK;
  PyObject *RetVal;
  int flushmode = Z_FINISH;
  unsigned long start_total_out;

"""


@pytest.fixture
def monkey_patched_gzip():
    """Fixture to monkey patch gzip module for tests."""
    runner = StdlibTestRunner()
    runner.patch_gzip_module()
    yield
    runner.restore_gzip_module()


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    temp_dir = tempfile.mkdtemp()
    filename = os.path.join(temp_dir, "test.gz")
    yield filename
    if os.path.exists(filename):
        os.unlink(filename)
    os.rmdir(temp_dir)


class TestStdlibMonkeyPatched:
    """Test stdlib gzip functionality with pgzip monkey-patched in."""

    def test_write(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_write"""
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1 * 50)
            f.flush()
            f.fileno()
            if hasattr(os, "fsync"):
                os.fsync(f.fileno())
            f.close()

        # Test multiple close() calls
        f.close()

    def test_read(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_read"""
        # Write first
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1 * 50)

        # Then read
        with gzip.GzipFile(temp_file, "rb") as f:
            d = f.read()
        assert d == data1 * 50

    def test_append(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_append"""
        # Write initial data
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1 * 50)

        # Append more data
        with gzip.GzipFile(temp_file, "ab") as f:
            f.write(data1)

        # Read and verify
        with gzip.GzipFile(temp_file, "rb") as f:
            d = f.read()
        assert d == (data1 * 50) + data1

    def test_many_append(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_many_append"""
        for i in range(10):
            with gzip.GzipFile(temp_file, "ab") as f:
                f.write(data1)

        with gzip.GzipFile(temp_file, "rb") as f:
            d = f.read()
        assert d == data1 * 10

    def test_buffered_reader(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_buffered_reader"""
        # Write test data
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1 * 50)

        # Read in chunks
        with gzip.GzipFile(temp_file, "rb") as f:
            bufsize = 8192
            d1 = f.read(bufsize)
            d2 = f.read(bufsize)
            d3 = f.read(bufsize)
        assert d1 + d2 + d3 == data1 * 50

    def test_readline(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_readline"""
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1)

        with gzip.GzipFile(temp_file, "rb") as f:
            line_length = 0
            while True:
                L = f.readline()
                if not L:
                    break
                line_length += len(L)
        assert line_length == len(data1)

    def test_readlines(self, monkey_patched_gzip, temp_file):
        """Adapted from stdlib test_gzip.py TestGzip.test_readlines"""
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1)

        with gzip.GzipFile(temp_file, "rb") as f:
            L = f.readlines()
        assert b"".join(L) == data1

    def test_seek_read(self, monkey_patched_gzip, temp_file):
        """Test seek and read operations"""
        with gzip.GzipFile(temp_file, "wb") as f:
            f.write(data1 * 50)

        with gzip.GzipFile(temp_file, "rb") as f:
            f.seek(10)
            d = f.read(10)
            assert len(d) == 10

    def test_mode(self, monkey_patched_gzip, temp_file):
        """Test file mode property"""
        with gzip.GzipFile(temp_file, "wb") as f:
            assert f.mode == gzip.WRITE

        with gzip.GzipFile(temp_file, "rb") as f:
            assert f.mode == gzip.READ
