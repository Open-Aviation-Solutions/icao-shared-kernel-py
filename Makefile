.DEFAULT_GOAL := help

VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MATURIN := $(VENV)/bin/maturin

.PHONY: help dev venv build test lint fmt fmt-check check

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/python:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip maturin pytest

venv: $(VENV)/bin/python ## Create the local dev virtualenv (maturin + pytest)

dev: venv ## Build the extension and install it into the dev virtualenv
	$(MATURIN) develop

build: ## Compile the Rust crate (no Python install step)
	cargo build

test: dev ## Run the pytest suite against the built extension
	$(PYTEST)

lint: ## Lint with clippy, treating warnings as errors
	cargo clippy --all-targets -- -D warnings

fmt: ## Format the code
	cargo fmt

fmt-check: ## Check formatting without modifying files
	cargo fmt --check

check: lint fmt-check test ## Run all checks: lint, format check, tests
