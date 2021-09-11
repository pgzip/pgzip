import sys
import os
import pytest
import mgzip
import gzip

DATA1 = b""""Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
"""


def test_write_wb(tmpdir):

    filename = os.path.join(tmpdir, "test.gz")
    with mgzip.open(filename, "wb", compresslevel=6) as f1:
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

    with mgzip.open(filename, "rb") as f2:
        file_content = f2.read()
    assert file_content == DATA1 * 500


def test_pool_close(tmpdir):

    filename = os.path.join(tmpdir, "test.gz")
    fh = mgzip.open(filename, "wb", compresslevel=6, thread=4, blocksize=128)
    fh.write(DATA1 * 500)
    if sys.version_info >= (3, 8):
        assert (
            repr(fh.pool) == "<multiprocessing.pool.ThreadPool state=RUN pool_size=4>"
        )
    fh.close()
    assert fh.fileobj is None
    assert fh.myfileobj is None
    assert fh.pool_result == []
    if sys.version_info >= (3, 8):
        assert (
            repr(fh.pool) == "<multiprocessing.pool.ThreadPool state=CLOSE pool_size=4>"
        )
    if sys.version_info >= (3, 7):
        with pytest.raises(ValueError) as excinfo:
            fh.pool.apply(print, ("x",))
        assert "Pool not running" in str(excinfo.value)
    else:
        with pytest.raises(AssertionError) as excinfo:
            fh.pool.apply(print, ("x",))
        assert "" == str(excinfo.value)
