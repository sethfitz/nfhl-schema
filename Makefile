# Tasks for this repository. `make help` lists them; README.md#development says when
# to reach for each.

PY_SCRIPTS := $(shell grep -l '^\#!/usr/bin/env -S uv run python' scripts/*)

.DEFAULT_GOAL := help
.PHONY: help sync check test test-fast lint format models docs snapshot report rules fixtures

help: ## List the tasks
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/' | expand -t 12

sync: ## Install the dev environment
	uv sync --dev

check: test lint ## Everything CI would run: tests, types, lint, formatting

test: ## Run the tests, including the ~30s PDF extraction
	uv run pytest

test-fast: ## Run the tests, skipping the PDF extraction
	uv run pytest -m "not slow"

lint: ## Type-check the package and scripts; check lint and formatting
	uv run mypy .
	for f in $(PY_SCRIPTS); do uv run mypy --strict "$$f" || exit 1; done
	uv run ruff check .
	uv run ruff format --check .

format: ## Apply ruff's formatting and safe fixes
	uv run ruff format .
	uv run ruff check --fix .

models: ## Rewrite src/nfhl/models/ from spec/
	./scripts/generate-models

docs: models ## Rewrite docs/ from the models
	./scripts/generate-docs

snapshot: ## Refresh spec/ from FEMA (SNAPSHOT_ARGS=--skip-observed is fast)
	./scripts/snapshot-spec $(SNAPSHOT_ARGS)

report: ## Print published values the reference does not allow
	./scripts/report-observed

rules: ## Count the rows breaking each rule, each on its own (RULES_ARGS=--live)
	./scripts/count-broken-rules $(RULES_ARGS)

fixtures: ## Refetch the real-feature test fixture
	./scripts/fetch-fixtures
