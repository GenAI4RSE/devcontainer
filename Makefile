.PHONY: generate validate test lint format clean

generate:
	uv run devcc batch

validate:
	uv run devcc validate

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

clean:
	rm -rf templates/ .devcontainer/ dist/ __pycache__ src/devcc/__pycache__ tests/__pycache__ .pytest_cache .ruff_cache
