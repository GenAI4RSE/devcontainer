"""CLI integration tests using click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from devcc.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCreate:
    def test_python_claude_code(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(
            main, ["create", "-l", "python", "-a", "claude-code", "-o", str(out)]
        )
        assert result.exit_code == 0, result.output
        assert (out / "devcontainer.json").exists()
        data = json.loads((out / "devcontainer.json").read_text())
        assert data["name"] == "Python + Claude Code"

    def test_no_agent(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(main, ["create", "-l", "rust", "-o", str(out)])
        assert result.exit_code == 0, result.output
        data = json.loads((out / "devcontainer.json").read_text())
        assert data["name"] == "Rust"

    def test_version_override(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(main, ["create", "-l", "python:3.11", "-o", str(out)])
        assert result.exit_code == 0, result.output
        data = json.loads((out / "devcontainer.json").read_text())
        assert data["features"]["ghcr.io/devcontainers/features/python:1"]["version"] == "3.11"

    def test_multi_lang(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(
            main, ["create", "-l", "python,node", "-a", "claude-code", "-o", str(out)]
        )
        assert result.exit_code == 0, result.output
        data = json.loads((out / "devcontainer.json").read_text())
        assert "Python" in data["name"]
        assert "Node.js" in data["name"]

    def test_invalid_language(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(main, ["create", "-l", "cobol", "-o", str(out)])
        assert result.exit_code != 0

    def test_missing_language_shows_help(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["create", "-o", str(tmp_path)])
        assert result.exit_code == 0
        assert "Usage:" in result.output


class TestBatch:
    def test_generates_36_templates(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["batch", "-o", str(tmp_path)])
        assert result.exit_code == 0, result.output
        dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
        assert len(dirs) == 36


class TestListLangs:
    def test_lists_all_languages(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["list-langs"])
        assert result.exit_code == 0
        assert "python" in result.output
        assert "node" in result.output
        assert "rust" in result.output
        assert "r" in result.output
        assert "julia" in result.output
        assert "c-cpp-fortran" in result.output


class TestListAgents:
    def test_lists_all_agents(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["list-agents"])
        assert result.exit_code == 0
        assert "claude-code" in result.output
        assert "codex" in result.output
        assert "copilot" in result.output
        assert "gemini" in result.output
        assert "cursor" in result.output


class TestValidate:
    def test_valid_templates(self, runner: CliRunner, tmp_path: Path) -> None:
        # Generate then validate
        runner.invoke(main, ["batch", "-o", str(tmp_path)])
        result = runner.invoke(main, ["validate", str(tmp_path)])
        assert result.exit_code == 0

    def test_invalid_directory(self, runner: CliRunner, tmp_path: Path) -> None:
        bad = tmp_path / "bad"
        bad.mkdir()
        result = runner.invoke(main, ["validate", str(tmp_path)])
        assert result.exit_code != 0
