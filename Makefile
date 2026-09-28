.PHONY: help install dev test lint type-check clean eval

help:  ## Show this help message
	@echo "OlaiSearch - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -e ".[dev]"
	pre-commit install

dev:  ## Start development server (API only for now)
	python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Run tests
	pytest

lint:  ## Run linters (ruff + black)
	ruff check backend/ tests/
	black --check backend/ tests/

format:  ## Format code
	ruff check --fix backend/ tests/
	black backend/ tests/

type-check:  ## Run type checker
	mypy backend/

clean:  ## Clean generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage

eval:  ## Run all evaluation scripts
	@echo "Running evaluation scripts..."
	@echo "TODO: Implement eval scripts in M3+"

list-models:  ## List available models from OmniRoute
	python scripts/list_models.py
