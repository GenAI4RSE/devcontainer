"""Tests for the generator module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from devcc.generator import (
    build_setup_script,
    deep_merge,
    generate,
    generate_batch,
    resolve_custom_keys,
)

APT_FEATURE_KEY = "ghcr.io/devcontainers-extra/features/apt-get-packages:1"
NODE_FEATURE_KEY = "ghcr.io/devcontainers/features/node:1"


class TestDeepMerge:
    def test_scalar_overwrite(self) -> None:
        base = {"image": "ubuntu:22.04"}
        overlay = {"image": "ubuntu:24.04"}
        result = deep_merge(base, overlay)
        assert result["image"] == "ubuntu:24.04"

    def test_object_recursive_merge(self) -> None:
        base = {"features": {"a": {"v": 1}}}
        overlay = {"features": {"b": {"v": 2}}}
        result = deep_merge(base, overlay)
        assert result["features"] == {"a": {"v": 1}, "b": {"v": 2}}

    def test_object_key_conflict_overwrites(self) -> None:
        base = {"features": {"a": {"v": 1}}}
        overlay = {"features": {"a": {"v": 2}}}
        result = deep_merge(base, overlay)
        assert result["features"]["a"]["v"] == 2

    def test_array_concat_dedup(self) -> None:
        base = {"mounts": ["vol-a", "vol-b"]}
        overlay = {"mounts": ["vol-b", "vol-c"]}
        result = deep_merge(base, overlay)
        assert result["mounts"] == ["vol-a", "vol-b", "vol-c"]

    def test_new_keys_added(self) -> None:
        base = {"a": 1}
        overlay = {"b": 2}
        result = deep_merge(base, overlay)
        assert result == {"a": 1, "b": 2}

    def test_does_not_mutate_base(self) -> None:
        base: dict[str, Any] = {"features": {"a": {"v": 1}}}
        overlay: dict[str, Any] = {"features": {"a": {"v": 2}}}
        deep_merge(base, overlay)
        assert base["features"]["a"]["v"] == 1

    def test_multiple_overlays(self) -> None:
        base = {"a": 1}
        o1 = {"b": 2}
        o2 = {"c": 3}
        result = deep_merge(base, o1, o2)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_nested_array_in_object(self) -> None:
        base = {"customizations": {"vscode": {"extensions": ["ext-a"]}}}
        overlay = {"customizations": {"vscode": {"extensions": ["ext-b"]}}}
        result = deep_merge(base, overlay)
        assert result["customizations"]["vscode"]["extensions"] == ["ext-a", "ext-b"]

    def test_empty_overlay(self) -> None:
        base = {"a": 1, "b": [1, 2]}
        result = deep_merge(base, {})
        assert result == base

    def test_empty_base(self) -> None:
        overlay = {"a": 1}
        result = deep_merge({}, overlay)
        assert result == {"a": 1}


class TestResolveCustomKeys:
    def _base_merged(self) -> dict[str, Any]:
        """Minimal merged dict simulating base + language."""
        return {
            "name": "",
            "features": {
                APT_FEATURE_KEY: {"packages": "jq,vim,bat,autojump"},
            },
            "postCreateCommand": {"zsh-custom": "bash .devcontainer/zsh-custom.sh"},
            "mounts": [
                "source=devcc-bashhistory-${devcontainerId},target=/commandhistory,type=volume"
            ],
            "containerEnv": {},
            "customizations": {"vscode": {"extensions": []}},
            "_id": "python",
            "_name": "Python",
        }

    def test_extra_apt_packages_appended(self) -> None:
        merged = self._base_merged()
        lang_frags = [
            {
                "_id": "c-cpp-fortran",
                "_name": "C",
                "_extra_apt_packages": ["gcc", "gdb"],
                "_default_version": "latest",
                "_feature_key": "x",
                "_version_param": "version",
            }
        ]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert result["features"][APT_FEATURE_KEY]["packages"] == "jq,vim,bat,autojump,gcc,gdb"

    def test_no_extra_apt_packages(self) -> None:
        merged = self._base_merged()
        lang_frags = [
            {
                "_id": "python",
                "_name": "Python",
                "_extra_apt_packages": [],
                "_default_version": "3.12",
                "_feature_key": "x",
                "_version_param": "version",
            }
        ]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert result["features"][APT_FEATURE_KEY]["packages"] == "jq,vim,bat,autojump"

    def test_agent_install_command(self) -> None:
        merged = self._base_merged()
        agent_frags = [
            {
                "_id": "claude-code",
                "_name": "Claude Code",
                "_install_command": "curl install.sh | bash",
                "_config_dir": "/home/neo/.claude",
                "_requires_node": False,
            }
        ]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert result["postCreateCommand"]["claude-code"] == "curl install.sh | bash"

    def test_agent_config_dir_mount_and_env(self) -> None:
        merged = self._base_merged()
        agent_frags = [
            {
                "_id": "claude-code",
                "_name": "Claude Code",
                "_install_command": "install",
                "_config_dir": "/home/neo/.claude",
                "_requires_node": False,
            }
        ]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert any("/home/neo/.claude" in m for m in result["mounts"])
        assert result["containerEnv"]["CLAUDE_CODE_CONFIG_DIR"] == "/home/neo/.claude"

    def test_requires_node_injects_feature(self) -> None:
        merged = self._base_merged()
        agent_frags = [
            {
                "_id": "codex",
                "_name": "Codex",
                "_install_command": "npm i codex",
                "_config_dir": "/home/neo/.codex",
                "_requires_node": True,
            }
        ]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert NODE_FEATURE_KEY in result["features"]
        assert result["features"][NODE_FEATURE_KEY]["version"] == "22"

    def test_requires_node_skips_when_node_lang_present(self) -> None:
        merged = self._base_merged()
        merged["features"][NODE_FEATURE_KEY] = {"version": "20"}
        agent_frags = [
            {
                "_id": "codex",
                "_name": "Codex",
                "_install_command": "npm i codex",
                "_config_dir": "/home/neo/.codex",
                "_requires_node": True,
            }
        ]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert result["features"][NODE_FEATURE_KEY]["version"] == "20"

    def test_version_override(self) -> None:
        merged = self._base_merged()
        feature_key = "ghcr.io/devcontainers/features/python:1"
        merged["features"][feature_key] = {"version": "3.12"}
        lang_frags = [
            {
                "_id": "python",
                "_name": "Python",
                "_extra_apt_packages": [],
                "_default_version": "3.12",
                "_feature_key": feature_key,
                "_version_param": "version",
            }
        ]
        result = resolve_custom_keys(merged, lang_frags, [], {"python": "3.11"})
        assert result["features"][feature_key]["version"] == "3.11"

    def test_name_lang_only(self) -> None:
        merged = self._base_merged()
        lang_frags = [
            {
                "_id": "python",
                "_name": "Python",
                "_extra_apt_packages": [],
                "_default_version": "3.12",
                "_feature_key": "x",
                "_version_param": "v",
            }
        ]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert result["name"] == "Python"

    def test_name_lang_and_agent(self) -> None:
        merged = self._base_merged()
        lang_frags = [
            {
                "_id": "python",
                "_name": "Python",
                "_extra_apt_packages": [],
                "_default_version": "3.12",
                "_feature_key": "x",
                "_version_param": "v",
            }
        ]
        agent_frags = [
            {
                "_id": "cc",
                "_name": "Claude Code",
                "_install_command": "x",
                "_config_dir": "/x",
                "_requires_node": False,
            }
        ]
        result = resolve_custom_keys(merged, lang_frags, agent_frags, {})
        assert result["name"] == "Python + Claude Code"

    def test_all_custom_keys_stripped(self) -> None:
        merged = self._base_merged()
        merged["_extra_field"] = "should be removed"
        lang_frags = [
            {
                "_id": "python",
                "_name": "Python",
                "_extra_apt_packages": [],
                "_default_version": "3.12",
                "_feature_key": "x",
                "_version_param": "v",
            }
        ]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert not any(k.startswith("_") for k in result)

    def test_multi_agent(self) -> None:
        merged = self._base_merged()
        agent_frags = [
            {
                "_id": "claude-code",
                "_name": "Claude Code",
                "_install_command": "curl install",
                "_config_dir": "/home/neo/.claude",
                "_requires_node": False,
            },
            {
                "_id": "codex",
                "_name": "Codex",
                "_install_command": "npm i codex",
                "_config_dir": "/home/neo/.codex",
                "_requires_node": True,
            },
        ]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert "claude-code" in result["postCreateCommand"]
        assert "codex" in result["postCreateCommand"]
        assert result["containerEnv"]["CLAUDE_CODE_CONFIG_DIR"] == "/home/neo/.claude"
        assert result["containerEnv"]["CODEX_CONFIG_DIR"] == "/home/neo/.codex"
        assert NODE_FEATURE_KEY in result["features"]


class TestBuildSetupScript:
    def test_no_agents(self) -> None:
        script = build_setup_script([])
        assert "chown -R neo:neo /commandhistory" in script
        assert "/home/neo/.claude" not in script

    def test_with_agent(self) -> None:
        agent_frags = [
            {
                "_id": "claude-code",
                "_name": "Claude Code",
                "_install_command": "x",
                "_config_dir": "/home/neo/.claude",
                "_requires_node": False,
            }
        ]
        script = build_setup_script(agent_frags)
        assert "chown -R neo:neo /home/neo/.claude" in script

    def test_multiple_agents(self) -> None:
        agent_frags = [
            {
                "_id": "claude-code",
                "_name": "CC",
                "_install_command": "x",
                "_config_dir": "/home/neo/.claude",
                "_requires_node": False,
            },
            {
                "_id": "codex",
                "_name": "Codex",
                "_install_command": "x",
                "_config_dir": "/home/neo/.codex",
                "_requires_node": True,
            },
        ]
        script = build_setup_script(agent_frags)
        assert "chown -R neo:neo /home/neo/.claude" in script
        assert "chown -R neo:neo /home/neo/.codex" in script


class TestGenerate:
    def test_python_claude_code(self, tmp_output: Path) -> None:
        result = generate([("python", None)], ["claude-code"], tmp_output)
        assert result == tmp_output
        assert (tmp_output / "devcontainer.json").exists()
        assert (tmp_output / "common-setup.sh").exists()
        assert (tmp_output / "zsh-custom.sh").exists()
        data = json.loads((tmp_output / "devcontainer.json").read_text())
        assert data["name"] == "Python + Claude Code"
        assert "ghcr.io/devcontainers/features/python:1" in data["features"]
        assert "claude-code" in data["postCreateCommand"]
        assert not any(k.startswith("_") for k in data)

    def test_no_agent(self, tmp_output: Path) -> None:
        generate([("rust", None)], [], tmp_output)
        data = json.loads((tmp_output / "devcontainer.json").read_text())
        assert data["name"] == "Rust"
        assert "postCreateCommand" in data
        assert len(data["postCreateCommand"]) == 1  # only zsh-custom
        setup = (tmp_output / "common-setup.sh").read_text()
        assert "/home/neo/.claude" not in setup

    def test_version_override(self, tmp_output: Path) -> None:
        generate([("python", "3.11")], [], tmp_output)
        data = json.loads((tmp_output / "devcontainer.json").read_text())
        assert data["features"]["ghcr.io/devcontainers/features/python:1"]["version"] == "3.11"

    def test_node_dedup(self, tmp_output: Path) -> None:
        generate([("node", "20")], ["codex"], tmp_output)
        data = json.loads((tmp_output / "devcontainer.json").read_text())
        # Language version takes precedence — injection skipped entirely
        assert data["features"]["ghcr.io/devcontainers/features/node:1"]["version"] == "20"

    def test_unknown_language_raises(self, tmp_output: Path) -> None:
        with pytest.raises(ValueError, match="Unknown languages ID"):
            generate([("nonexistent", None)], [], tmp_output)

    def test_unknown_agent_raises(self, tmp_output: Path) -> None:
        with pytest.raises(ValueError, match="Unknown agents ID"):
            generate([("python", None)], ["nonexistent"], tmp_output)

    def test_json_formatting(self, tmp_output: Path) -> None:
        generate([("python", None)], [], tmp_output)
        text = (tmp_output / "devcontainer.json").read_text()
        assert text.endswith("\n")
        # 2-space indent: second line should start with 2 spaces
        lines = text.splitlines()
        assert lines[1].startswith("  ")
        assert not lines[1].startswith("    ")


class TestGenerateBatch:
    def test_generates_36_directories(self, tmp_output: Path) -> None:
        paths = generate_batch(tmp_output)
        assert len(paths) == 36
        # Each should have the 3 output files
        for p in paths:
            assert (p / "devcontainer.json").exists()
            assert (p / "common-setup.sh").exists()
            assert (p / "zsh-custom.sh").exists()

    def test_directory_naming(self, tmp_output: Path) -> None:
        generate_batch(tmp_output)
        assert (tmp_output / "python").exists()
        assert (tmp_output / "python-claude-code").exists()
        assert (tmp_output / "c-cpp-fortran-codex").exists()
