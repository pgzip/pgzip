"""Pytest configuration for pgzip tests."""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file path."""
    return os.path.join(temp_dir, "test.gz")
