#
# vim:ft=make
# Makefile
#
# Standard Makefile for pgzip project, based on template.
# Using hatch and uv for environment and dependency management.

.DEFAULT_GOAL := help
.PHONY: test help install lint format cov release clean clean-envs sync-python-versions

_GREEN=$(shell tput setaf 2)
_BLUE=$(shell tput setaf 4)
_RED=$(shell tput setaf 1)
_RESET=$(shell tput sgr0)
_BOLD=$(shell tput bold)

COMMIT := $(shell git rev-parse HEAD 2>/dev/null || echo "unknown")
SHORTCOMMIT := $(shell git rev-parse HEAD 2>/dev/null | cut -c-7 || echo "unknown")

help:  ## these help instructions
	@sed -rn 's/^([a-zA-Z0-9_-]+):.* ## (.*)$$/"\1" "\2"/p' < $(MAKEFILE_LIST)|xargs printf "$(_GREEN)make %-20s$(_RESET) # %s\n"

hidden: # undocumented, single '#' allows for comments on internal usage only tasks
	@true

install: ## Install dependencies using uv via hatch
	hatch env create default

lint: ## Runs linting checks (black, isort, bandit)
	hatch run lint:check

format: ## Formats code using black and isort
	hatch run lint:fix

test: hidden ## Run tests using pytest
	hatch run test

cov: ## Run tests with coverage report
	hatch run cov

release: ## Run tests, linting, and build the package
	hatch run release

sync-python-versions: ## Update tool.hatch.envs.all.matrix in pyproject.toml
	hatch run sync-python-versions

clean-envs: ## Remove all Hatch virtual environments
	hatch env prune

clean: clean-envs ## Remove build artifacts and caches
	rm -rf dist/ .pytest_cache/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
