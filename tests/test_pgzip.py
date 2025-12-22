import gzip
import os

import pytest

import pgzip

# The Zen of Python as test data
DATA1 = b"""The Zen of Python, by Tim Peters

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""


def test_write_wb(tmpdir):
    filename = os.path.join(tmpdir, "test.gz")
    with pgzip.open(filename, "wb", compresslevel=6) as f1:
        f1.write(DATA1 * 50)
        # Try flush and fileno.
        f1.flush()
        f1.fileno()
        if hasattr(os, "fsync"):
            os.fsync(f1.fileno())
        f1.close()
    f1.close()

    assert os.path.exists(filename)
    with gzip.open(filename, "rb") as f2:
        file_content = f2.read()
    assert file_content == DATA1 * 50


def test_read_rb(tmpdir):
    filename = os.path.join(tmpdir, "test.gz")
    with gzip.open(filename, "wb") as f1:
        f1.write(DATA1 * 500)

    with pgzip.open(filename, "rb") as f2:
        file_content = f2.read()
    assert file_content == DATA1 * 500


def test_pool_close(tmpdir):
    filename = os.path.join(tmpdir, "test.gz")
    fh = pgzip.open(filename, "wb", compresslevel=6, thread=4, blocksize=128)
    fh.write(DATA1 * 500)
    assert not fh.pool._shutdown
    fh.close()
    assert fh.fileobj is None
    assert fh.myfileobj is None
    assert fh.pool_result == []
    assert fh.pool._shutdown
    with pytest.raises(RuntimeError) as excinfo:
        fh.pool.submit(print, ("x",))
    assert str(excinfo.value) == "cannot schedule new futures after shutdown"


def test_compress_function():
    """Test pgzip.compress() function."""
    data = DATA1 * 100

    # Test basic compression
    compressed = pgzip.compress(data)
    assert isinstance(compressed, bytes)
    assert len(compressed) < len(data)  # Should be smaller

    # Verify it's valid gzip
    decompressed = gzip.decompress(compressed)
    assert decompressed == data

    # Test with different compression levels
    for level in [0, 1, 6, 9]:
        compressed = pgzip.compress(data, compresslevel=level)
        decompressed = gzip.decompress(compressed)
        assert decompressed == data

    # Test with threading parameters
    compressed = pgzip.compress(data, thread=2, blocksize=1024)
    decompressed = gzip.decompress(compressed)
    assert decompressed == data


def test_decompress_function():
    """Test pgzip.decompress() function."""
    data = DATA1 * 100

    # Create compressed data with stdlib gzip
    compressed = gzip.compress(data)

    # Test basic decompression
    decompressed = pgzip.decompress(compressed)
    assert decompressed == data

    # Test with threading parameters
    decompressed = pgzip.decompress(compressed, thread=2, blocksize=1024)
    assert decompressed == data


def test_thread_parameter_values(tmpdir):
    """Test different thread parameter values."""
    filename = os.path.join(tmpdir, "test.gz")
    data = DATA1 * 100

    # Test various thread values
    for threads in [None, 0, 1, 2, 4]:
        with pgzip.open(filename, "wb", thread=threads) as f:
            f.write(data)

        # Verify file is readable
        with gzip.open(filename, "rb") as f:
            assert f.read() == data


def test_blocksize_parameter_values(tmpdir):
    """Test different blocksize parameter values."""
    filename = os.path.join(tmpdir, "test.gz")
    data = DATA1 * 200

    # Test various block sizes
    for blocksize in [1024, 8192, 65536, 1024 * 1024]:
        with pgzip.open(filename, "wb", blocksize=blocksize) as f:
            f.write(data)

        # Verify file is readable
        with gzip.open(filename, "rb") as f:
            assert f.read() == data


def test_large_data_performance(tmpdir):
    """Test with larger data to verify threading benefit."""
    filename = os.path.join(tmpdir, "test.gz")
    # Use larger data to see threading effects
    large_data = DATA1 * 10000

    # Test with multiple threads
    with pgzip.open(filename, "wb", thread=4, blocksize=64 * 1024) as f:
        f.write(large_data)

    # Verify correctness
    with gzip.open(filename, "rb") as f:
        assert f.read() == large_data


def test_empty_file(tmpdir):
    """Test handling of empty files."""
    filename = os.path.join(tmpdir, "empty.gz")

    # Write empty file
    with pgzip.open(filename, "wb") as f:
        pass

    # Read empty file
    with pgzip.open(filename, "rb") as f:
        assert f.read() == b""


def test_single_byte_operations(tmpdir):
    """Test single byte read/write operations."""
    filename = os.path.join(tmpdir, "single.gz")

    # Write single byte
    with pgzip.open(filename, "wb") as f:
        f.write(b"x")

    # Read single byte
    with pgzip.open(filename, "rb") as f:
        assert f.read() == b"x"
