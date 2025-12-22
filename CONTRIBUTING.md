# Contributing to pgzip

Thank you for your interest in contributing to pgzip! This guide will help you get started.

## Development Setup

This project uses [Hatch](https://hatch.pypa.io/) for development environment management.

### Prerequisites

- Python 3.10+
- [Hatch](https://hatch.pypa.io/) (`pip install hatch`)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/pgzip/pgzip.git
cd pgzip

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
hatch run test
```

## Development Commands

### Testing

```bash
# Run tests (current Python version)
hatch run test

# Run tests with coverage
hatch run cov

# Test all Python versions (3.10-3.14)
hatch run all:test

# Test specific Python version
hatch run all.py3.10:test
hatch run all.py3.11:test
hatch run all.py3.12:test
hatch run all.py3.13:test
hatch run all.py3.14:test
```

### Code Quality

```bash
# Check code style
hatch run lint:check

# Fix code style
hatch run lint:fix
```

### Building

```bash
# Build package
hatch build
```

### Release

```bash
# Full release check (test all versions + lint + build)
hatch run release
```

## Making Changes

1. **Fork** the repository
2. **Create a branch** for your changes
3. **Make your changes** with tests
4. **Run the full test suite** (`hatch run release`)
5. **Submit a pull request**

## Code Style

- Code is formatted with [Black](https://black.readthedocs.io/)
- Imports are sorted with [isort](https://pycqa.github.io/isort/)
- Security checks with [Bandit](https://bandit.readthedocs.io/)
- Pre-commit hooks enforce these automatically

## Testing

- All new features should include tests
- Tests are written using [pytest](https://pytest.org/)
- Aim for good test coverage of new code

## Questions?

Feel free to open an issue for questions or discussion!
