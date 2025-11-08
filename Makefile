.PHONY: help install install-dev test test-cov lint format type-check clean run

help:		## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:	## Install the package
	pip install -e .

install-dev:	## Install the package with development dependencies
	pip install -e ".[dev]"

test:		## Run tests
	pytest

test-cov:	## Run tests with coverage
	pytest --cov=src/media_manager --cov-report=html --cov-report=term

lint:		## Run linting
	ruff check src/ tests/

format:		## Format code
	black src/ tests/
	ruff check --fix src/ tests/

type-check:	## Run type checking
	mypy src/

clean:		## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run:		## Run the application
	python -m src.media_manager.main

check: lint type-check test	## Run all quality checks

all: clean install-dev format lint type-check test	## Run full development pipeline