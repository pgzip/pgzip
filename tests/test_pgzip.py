import sys
import os
import pytest
import pgzip
import gzip

DATA1 = b""""Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
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
    assert "cannot schedule new futures after shutdown" == str(excinfo.value)
