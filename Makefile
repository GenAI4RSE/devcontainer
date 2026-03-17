.PHONY: help test lint format clean
.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

test: ## Run tests
	uv run pytest

lint: ## Lint source and tests
	uv run ruff check src/ tests/

format: ## Format source and tests
	uv run ruff format src/ tests/

clean: ## Remove generated and cache files
	rm -rf templates/ .devcontainer/ dist/ __pycache__ src/devcc/__pycache__ tests/__pycache__ .pytest_cache .ruff_cache
