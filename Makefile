.PHONY: generate validate test

generate:
	uv run devcc batch

validate:
	uv run devcc validate

test:
	uv run pytest
