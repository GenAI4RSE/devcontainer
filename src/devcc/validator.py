"""Validator: official schema + devcc-specific checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from devcc.dimensions import get_data_path


def _load_schema() -> dict[str, Any]:
    """Load the bundled devcontainer JSON schema."""
    schema_path = get_data_path() / "schema" / "devContainer.base.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def validate_devcontainer_json(data: dict[str, Any]) -> list[str]:
    """Validate a parsed devcontainer.json dict. Returns list of error strings."""
    errors: list[str] = []

    # Layer 1: Official schema validation
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    for error in validator.iter_errors(data):
        errors.append(f"Schema: {error.message}")

    # Layer 2: devcc-specific checks
    custom_keys = [k for k in data if k.startswith("_")]
    for key in custom_keys:
        errors.append(f"Leftover custom key: {key}")

    name = data.get("name", "")
    if not name:
        errors.append("Field 'name' is empty or missing")

    return errors


def validate_directory(path: Path) -> list[str]:
    """Validate a generated template directory. Returns list of error strings."""
    errors: list[str] = []

    json_path = path / "devcontainer.json"
    if not json_path.exists():
        errors.append(f"Missing: {json_path}")
    else:
        with open(json_path) as f:
            data = json.load(f)
        errors.extend(validate_devcontainer_json(data))

    for script in ["system-setup.sh", "zsh-custom.sh"]:
        if not (path / script).exists():
            errors.append(f"Missing: {path / script}")

    return errors


def validate_batch(templates_dir: Path) -> dict[str, list[str]]:
    """Validate all subdirectories in a templates directory."""
    results: dict[str, list[str]] = {}
    for subdir in sorted(templates_dir.iterdir()):
        if subdir.is_dir():
            results[subdir.name] = validate_directory(subdir)
    return results
