"""Tests for the generator module."""

from __future__ import annotations

from typing import Any

import pytest

from devcc.generator import deep_merge


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


APT_FEATURE_KEY = "ghcr.io/devcontainers-extra/features/apt-get-packages:1"
NODE_FEATURE_KEY = "ghcr.io/devcontainers/features/node:1"


class TestResolveCustomKeys:
    def _base_merged(self) -> dict[str, Any]:
        """Minimal merged dict simulating base + language."""
        return {
            "name": "",
            "features": {
                APT_FEATURE_KEY: {"packages": "jq,vim,bat,autojump"},
            },
            "postCreateCommand": {"zsh-custom": "bash .devcontainer/zsh-custom.sh"},
            "mounts": ["source=devcc-bashhistory-${devcontainerId},target=/commandhistory,type=volume"],
            "containerEnv": {},
            "customizations": {"vscode": {"extensions": []}},
            "_id": "python",
            "_name": "Python",
        }

    def test_extra_apt_packages_appended(self) -> None:
        merged = self._base_merged()
        lang_frags = [{"_id": "c-cpp-fortran", "_name": "C", "_extra_apt_packages": ["gcc", "gdb"],
                        "_default_version": "latest", "_feature_key": "x", "_version_param": "version"}]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert result["features"][APT_FEATURE_KEY]["packages"] == "jq,vim,bat,autojump,gcc,gdb"

    def test_no_extra_apt_packages(self) -> None:
        merged = self._base_merged()
        lang_frags = [{"_id": "python", "_name": "Python", "_extra_apt_packages": [],
                        "_default_version": "3.12", "_feature_key": "x", "_version_param": "version"}]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert result["features"][APT_FEATURE_KEY]["packages"] == "jq,vim,bat,autojump"

    def test_agent_install_command(self) -> None:
        merged = self._base_merged()
        agent_frags = [{"_id": "claude-code", "_name": "Claude Code",
                         "_install_command": "curl install.sh | bash",
                         "_config_dir": "/home/neo/.claude", "_requires_node": False}]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert result["postCreateCommand"]["claude-code"] == "curl install.sh | bash"

    def test_agent_config_dir_mount_and_env(self) -> None:
        merged = self._base_merged()
        agent_frags = [{"_id": "claude-code", "_name": "Claude Code",
                         "_install_command": "install", "_config_dir": "/home/neo/.claude",
                         "_requires_node": False}]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert any("/home/neo/.claude" in m for m in result["mounts"])
        assert result["containerEnv"]["CLAUDE_CODE_CONFIG_DIR"] == "/home/neo/.claude"

    def test_requires_node_injects_feature(self) -> None:
        merged = self._base_merged()
        agent_frags = [{"_id": "codex", "_name": "Codex", "_install_command": "npm i codex",
                         "_config_dir": "/home/neo/.codex", "_requires_node": True}]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert NODE_FEATURE_KEY in result["features"]
        assert result["features"][NODE_FEATURE_KEY]["version"] == "22"

    def test_requires_node_skips_when_node_lang_present(self) -> None:
        merged = self._base_merged()
        merged["features"][NODE_FEATURE_KEY] = {"version": "20"}
        agent_frags = [{"_id": "codex", "_name": "Codex", "_install_command": "npm i codex",
                         "_config_dir": "/home/neo/.codex", "_requires_node": True}]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert result["features"][NODE_FEATURE_KEY]["version"] == "20"

    def test_version_override(self) -> None:
        merged = self._base_merged()
        feature_key = "ghcr.io/devcontainers/features/python:1"
        merged["features"][feature_key] = {"version": "3.12"}
        lang_frags = [{"_id": "python", "_name": "Python", "_extra_apt_packages": [],
                        "_default_version": "3.12", "_feature_key": feature_key,
                        "_version_param": "version"}]
        result = resolve_custom_keys(merged, lang_frags, [], {"python": "3.11"})
        assert result["features"][feature_key]["version"] == "3.11"

    def test_name_lang_only(self) -> None:
        merged = self._base_merged()
        lang_frags = [{"_id": "python", "_name": "Python", "_extra_apt_packages": [],
                        "_default_version": "3.12", "_feature_key": "x", "_version_param": "v"}]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert result["name"] == "Python"

    def test_name_lang_and_agent(self) -> None:
        merged = self._base_merged()
        lang_frags = [{"_id": "python", "_name": "Python", "_extra_apt_packages": [],
                        "_default_version": "3.12", "_feature_key": "x", "_version_param": "v"}]
        agent_frags = [{"_id": "cc", "_name": "Claude Code", "_install_command": "x",
                         "_config_dir": "/x", "_requires_node": False}]
        result = resolve_custom_keys(merged, lang_frags, agent_frags, {})
        assert result["name"] == "Python + Claude Code"

    def test_all_custom_keys_stripped(self) -> None:
        merged = self._base_merged()
        merged["_extra_field"] = "should be removed"
        lang_frags = [{"_id": "python", "_name": "Python", "_extra_apt_packages": [],
                        "_default_version": "3.12", "_feature_key": "x", "_version_param": "v"}]
        result = resolve_custom_keys(merged, lang_frags, [], {})
        assert not any(k.startswith("_") for k in result)

    def test_multi_agent(self) -> None:
        merged = self._base_merged()
        agent_frags = [
            {"_id": "claude-code", "_name": "Claude Code", "_install_command": "curl install",
             "_config_dir": "/home/neo/.claude", "_requires_node": False},
            {"_id": "codex", "_name": "Codex", "_install_command": "npm i codex",
             "_config_dir": "/home/neo/.codex", "_requires_node": True},
        ]
        result = resolve_custom_keys(merged, [], agent_frags, {})
        assert "claude-code" in result["postCreateCommand"]
        assert "codex" in result["postCreateCommand"]
        assert result["containerEnv"]["CLAUDE_CODE_CONFIG_DIR"] == "/home/neo/.claude"
        assert result["containerEnv"]["CODEX_CONFIG_DIR"] == "/home/neo/.codex"
        assert NODE_FEATURE_KEY in result["features"]
