# Development Documentation

This document provides a technical overview of the `pgzip` project for developers and contributors.

## Architecture Overview

`pgzip` is a multi-threaded implementation of the Python `gzip` module. It achieves significant performance gains by parallelizing compression and decompression using a custom block indexing format.

### Key Components

- **`PgzipFile`**: Inherits from `gzip.GzipFile`. It manages the high-level interface for reading and writing GZIP files.
- **`_MultiGzipReader`**: Inherits from `gzip._GzipReader`. It handles parallel decompression by reading individual GZIP members and decompressing them using a `ThreadPoolExecutor`.
- **`_compress_func` & `_decompress_func`**: Internal functions that handle the core `zlib` operations for individual data blocks.
- **`ThreadPoolExecutor`**: Used to manage concurrent execution of compression and decompression tasks.

## Development Workflow

We use [Hatch](https://hatch.pypa.io/) and [uv](https://github.com/astral-sh/uv) for environment and dependency management. A `Makefile` is provided for convenience.

### Setup

```bash
# Install dependencies
make install
```

### Common Commands

- **Run Tests**: `make test`
- **Check Linting**: `make lint`
- **Format Code**: `make format`
- **Check Coverage**: `make cov`
- **Build Package**: `make release`
- **Cleanup**: `make clean`

## The 'Indexed Gzip' (IG) Format

`pgzip` uses a custom GZIP extension to support efficient indexing and parallelization. This is implemented using the `FEXTRA` field as defined in [RFC 1952](https://www.ietf.org/rfc/rfc1952.txt).

### Extra Field Structure (SID: 'IG')

When `pgzip` writes a file, it includes an extra subfield in each GZIP member's header:

| Field       | Size    | Description                                 |
| ----------- | ------- | ------------------------------------------- |
| SI1, SI2    | 2 bytes | Subfield ID, always `b"IG"`                 |
| LEN         | 2 bytes | Length of subfield body, always 4           |
| MEMBER SIZE | 4 bytes | Total size of the current compressed member |

This allow `pgzip` to quickly skip through members without decompressing them, enabling parallel decompression and random access (via indexing).

## Project Structure

- `pgzip/pgzip.py`: The core implementation.
- `pgzip/__main__.py`: CLI entry point.
- `tests/`: Comprehensive test suite covering compatibility, CLI, and interop.
- `Makefile`: Standard development tasks.

## Coding Standards

- Follow **PEP 8** naming conventions (`snake_case` for variables and functions).
- Use **Type Hints** for all new public-facing APIs.
- Ensure all changes are covered by tests in the `tests/` directory.
- Run `make format` before committing.
