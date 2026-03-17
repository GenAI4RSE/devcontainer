"""Tests for the validator module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from devcc.validator import validate_devcontainer_json, validate_directory, validate_batch


def _write_valid_template(d: Path) -> dict[str, Any]:
    """Write a minimal valid template to directory d. Returns the JSON data."""
    data: dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.base.schema.json",
        "name": "Python",
        "image": "ubuntu:24.04",
    }
    d.mkdir(parents=True, exist_ok=True)
    (d / "devcontainer.json").write_text(json.dumps(data, indent=2) + "\n")
    (d / "common-setup.sh").write_text("#!/bin/bash\n")
    (d / "zsh-custom.sh").write_text("#!/bin/bash\n")
    return data


class TestValidateDevcontainerJson:
    def test_valid_minimal(self) -> None:
        data = {"name": "Test", "image": "ubuntu:24.04"}
        errors = validate_devcontainer_json(data)
        assert errors == []

    def test_leftover_custom_keys(self) -> None:
        data = {"name": "Test", "image": "ubuntu:24.04", "_id": "leftover"}
        errors = validate_devcontainer_json(data)
        assert any("_id" in e for e in errors)

    def test_empty_name(self) -> None:
        data = {"name": "", "image": "ubuntu:24.04"}
        errors = validate_devcontainer_json(data)
        assert any("name" in e.lower() for e in errors)

    def test_schema_violation(self) -> None:
        data = {"name": "Test", "image": 123}  # image must be string
        errors = validate_devcontainer_json(data)
        assert len(errors) > 0


class TestValidateDirectory:
    def test_valid_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "template"
        _write_valid_template(d)
        errors = validate_directory(d)
        assert errors == []

    def test_missing_devcontainer_json(self, tmp_path: Path) -> None:
        d = tmp_path / "template"
        d.mkdir()
        (d / "common-setup.sh").write_text("#!/bin/bash\n")
        (d / "zsh-custom.sh").write_text("#!/bin/bash\n")
        errors = validate_directory(d)
        assert any("devcontainer.json" in e for e in errors)

    def test_missing_setup_script(self, tmp_path: Path) -> None:
        d = tmp_path / "template"
        _write_valid_template(d)
        (d / "common-setup.sh").unlink()
        errors = validate_directory(d)
        assert any("common-setup.sh" in e for e in errors)

    def test_missing_zsh_script(self, tmp_path: Path) -> None:
        d = tmp_path / "template"
        _write_valid_template(d)
        (d / "zsh-custom.sh").unlink()
        errors = validate_directory(d)
        assert any("zsh-custom.sh" in e for e in errors)


class TestValidateBatch:
    def test_valid_batch(self, tmp_path: Path) -> None:
        for name in ["python", "rust"]:
            _write_valid_template(tmp_path / name)
        result = validate_batch(tmp_path)
        assert all(errors == [] for errors in result.values())

    def test_batch_with_errors(self, tmp_path: Path) -> None:
        _write_valid_template(tmp_path / "good")
        bad = tmp_path / "bad"
        bad.mkdir()
        # missing all files
        result = validate_batch(tmp_path)
        assert result["good"] == []
        assert len(result["bad"]) > 0
