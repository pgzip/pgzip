"""Tests for the pgzip CLI module."""

import gzip
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCLI:
    """Test the pgzip command-line interface."""

    def test_help(self):
        """Test --help flag."""
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout
        assert "Input file or '-' for stdin" in result.stdout

    def test_compress_file(self, tmp_path):
        """Test compressing a file."""
        # Create test input file
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World! " * 1000
        input_file.write_bytes(test_data)

        output_file = tmp_path / "test.txt.gz"

        # Compress using CLI
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", str(input_file), "-o", str(output_file)],
            capture_output=True,
        )
        assert result.returncode == 0
        assert output_file.exists()

        # Verify compressed data can be decompressed
        with gzip.open(output_file, "rb") as f:
            decompressed = f.read()
        assert decompressed == test_data

    def test_compress_auto_output(self, tmp_path):
        """Test compressing with automatic output filename."""
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World! " * 1000
        input_file.write_bytes(test_data)

        # Compress using CLI (auto output name)
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", str(input_file)],
            capture_output=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0

        output_file = tmp_path / "test.txt.gz"
        assert output_file.exists()

    def test_decompress_file(self, tmp_path):
        """Test decompressing a file."""
        # Create compressed test file
        test_data = b"Hello, World! " * 1000
        input_file = tmp_path / "test.txt.gz"
        with gzip.open(input_file, "wb") as f:
            f.write(test_data)

        output_file = tmp_path / "test.txt"

        # Decompress using CLI
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pgzip",
                "-d",
                str(input_file),
                "-o",
                str(output_file),
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        assert output_file.exists()
        assert output_file.read_bytes() == test_data

    def test_decompress_auto_output(self, tmp_path):
        """Test decompressing with automatic output filename."""
        test_data = b"Hello, World! " * 1000
        input_file = tmp_path / "test.txt.gz"
        with gzip.open(input_file, "wb") as f:
            f.write(test_data)

        # Decompress using CLI (auto output name)
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", "-d", str(input_file)],
            capture_output=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0

        output_file = tmp_path / "test.txt"
        assert output_file.exists()
        assert output_file.read_bytes() == test_data

    def test_stdin_stdout(self):
        """Test reading from stdin and writing to stdout."""
        test_data = b"Hello, World! " * 100

        # Compress via stdin/stdout
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", "-", "-o", "-"],
            input=test_data,
            capture_output=True,
        )
        assert result.returncode == 0

        # Verify compressed data by writing to temp file and reading back
        import tempfile

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(result.stdout)
            tmp.flush()
            tmp.seek(0)

            with gzip.open(tmp.name, "rb") as f:
                decompressed = f.read()
            assert decompressed == test_data

    def test_compression_levels(self, tmp_path):
        """Test different compression levels."""
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World! " * 1000
        input_file.write_bytes(test_data)

        for level in [0, 1, 6, 9]:
            output_file = tmp_path / f"test_level_{level}.txt.gz"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pgzip",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-l",
                    str(level),
                ],
                capture_output=True,
            )
            assert result.returncode == 0
            assert output_file.exists()

    def test_threads_option(self, tmp_path):
        """Test threads option."""
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World! " * 1000
        input_file.write_bytes(test_data)

        output_file = tmp_path / "test.txt.gz"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pgzip",
                str(input_file),
                "-o",
                str(output_file),
                "-t",
                "2",
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        assert output_file.exists()

    def test_filename_option(self, tmp_path):
        """Test custom filename option."""
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World! " * 1000
        input_file.write_bytes(test_data)

        output_file = tmp_path / "test.txt.gz"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pgzip",
                str(input_file),
                "-o",
                str(output_file),
                "-f",
                "custom.txt",
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        assert output_file.exists()

    def test_same_input_output_error(self, tmp_path):
        """Test error when input and output are the same file."""
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World!"
        input_file.write_bytes(test_data)

        result = subprocess.run(
            [sys.executable, "-m", "pgzip", str(input_file), "-o", str(input_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Input and output cannot be the same file" in result.stderr

    def test_invalid_compression_level(self):
        """Test invalid compression level."""
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", "-", "-l", "10"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr

    def test_nonexistent_input_file(self):
        """Test error with nonexistent input file."""
        result = subprocess.run(
            [sys.executable, "-m", "pgzip", "nonexistent.txt"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "FileNotFoundError" in result.stderr

    def test_keyboard_interrupt(self, tmp_path):
        """Test KeyboardInterrupt handling."""
        # This is harder to test directly, but we can at least verify
        # the main function exists and can be imported
        from pgzip.__main__ import main

        assert callable(main)

    def test_blocksize_option(self, tmp_path):
        """Test blocksize option."""
        input_file = tmp_path / "test.txt"
        test_data = b"Hello, World! " * 1000
        input_file.write_bytes(test_data)

        output_file = tmp_path / "test.txt.gz"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pgzip",
                str(input_file),
                "-o",
                str(output_file),
                "-b",
                "50000",
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        assert output_file.exists()
