# devcc Package Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pip-installable Python package (`devcc`) that generates devcontainer templates from composable JSON fragments using a dimension system.

**Architecture:** Fragment JSON files under `src/devcc/data/` are deep-merged by the generator, with custom `_`-prefixed keys resolved into final devcontainer.json fields. A `DimensionConfig` registry makes the system extensible without core logic changes.

**Tech Stack:** Python >= 3.11, uv, click, jsonschema, pytest, hatchling

**Spec:** `.dev/spec/260317-spec-devcc-package.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package metadata, dependencies, entry point |
| `Makefile` | Dev shortcuts (generate, validate, test) |
| `src/devcc/__init__.py` | Package marker, version |
| `src/devcc/__main__.py` | `python -m devcc` support |
| `src/devcc/dimensions.py` | `DimensionConfig` dataclass, `DIMENSIONS` list, fragment loading |
| `src/devcc/generator.py` | `deep_merge`, `resolve_custom_keys`, `generate`, `generate_batch` |
| `src/devcc/validator.py` | Schema validation (official + devcc checks) |
| `src/devcc/cli.py` | Click CLI group: create, batch, list-langs, list-agents, validate |
| `src/devcc/data/base/base.json` | Shared base fragment |
| `src/devcc/data/languages/*.json` | 6 language fragments |
| `src/devcc/data/agents/*.json` | 5 agent fragments |
| `src/devcc/data/shared/common-setup.sh` | Base template for setup script |
| `src/devcc/data/shared/zsh-custom.sh` | Static zsh customization script |
| `src/devcc/data/schema/devContainer.base.schema.json` | Bundled official schema |
| `tests/conftest.py` | Shared fixtures |
| `tests/test_generator.py` | Unit tests for merge + resolve + generate |
| `tests/test_validator.py` | Unit tests for validation |
| `tests/test_cli.py` | Integration tests with CliRunner |

---

### Task 1: Package Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `src/devcc/__init__.py`
- Create: `src/devcc/__main__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/devcc/data/{base,languages,agents,shared,schema} tests
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "devcc"
version = "0.1.0"
description = "Generate devcontainer templates for AI coding agents"
requires-python = ">=3.11"
dependencies = ["click", "jsonschema"]

[project.scripts]
devcc = "devcc.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/devcc"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[dependency-groups]
dev = ["pytest"]
```

- [ ] **Step 3: Create src/devcc/__init__.py**

```python
"""devcc — Generate devcontainer templates for AI coding agents."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create src/devcc/__main__.py**

```python
"""Allow running as `python -m devcc`."""

from devcc.cli import main

main()
```

- [ ] **Step 5: Create Makefile**

```makefile
.PHONY: generate validate test

generate:
	uv run devcc batch

validate:
	uv run devcc validate

test:
	uv run pytest
```

- [ ] **Step 6: Run uv sync**

Run: `uv sync`
Expected: Installs dependencies, creates `uv.lock`. The `devcc` entry point won't work yet (cli.py doesn't exist), but the package should install.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml Makefile src/devcc/__init__.py src/devcc/__main__.py uv.lock
git commit -m "feat: scaffold devcc package with pyproject.toml and uv"
```

---

### Task 2: Fragment Data Files

**Files:**
- Create: `src/devcc/data/base/base.json`
- Create: `src/devcc/data/languages/{python,node,rust,r,julia,c-cpp-fortran}.json`
- Create: `src/devcc/data/agents/{claude-code,codex,copilot,gemini,cursor}.json`
- Create: `src/devcc/data/shared/common-setup.sh`
- Create: `src/devcc/data/shared/zsh-custom.sh`
- Create: `src/devcc/data/schema/devContainer.base.schema.json`

- [ ] **Step 1: Create base fragment**

Write `src/devcc/data/base/base.json`:

```json
{
  "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.base.schema.json",
  "image": "ubuntu:24.04",
  "init": true,
  "features": {
    "ghcr.io/devcontainers/features/common-utils:2": {
      "username": "neo",
      "userUid": "automatic",
      "userGid": "automatic",
      "configureZshAsDefaultShell": true
    },
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers-extra/features/apt-get-packages:1": {
      "packages": "jq,vim,bat,autojump"
    }
  },
  "onCreateCommand": {
    "system-setup": "bash .devcontainer/common-setup.sh"
  },
  "postCreateCommand": {
    "zsh-custom": "bash .devcontainer/zsh-custom.sh"
  },
  "waitFor": "postCreateCommand",
  "customizations": {
    "vscode": {
      "extensions": []
    }
  },
  "containerUser": "neo",
  "remoteUser": "neo",
  "mounts": [
    "source=devcc-bashhistory-${devcontainerId},target=/commandhistory,type=volume"
  ],
  "containerEnv": {
    "HISTFILE": "/commandhistory/.zsh_history",
    "GIT_DELTA_VERSION": "0.18.2",
    "POWERLEVEL9K_DISABLE_GITSTATUS": "true",
    "LANG": "en_US.UTF-8",
    "LC_ALL": "en_US.UTF-8",
    "DEVCONTAINER": "true",
    "EDITOR": "vim",
    "VISUAL": "vim",
    "TZ": "${localEnv:TZ:Europe/Amsterdam}"
  },
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=delegated",
  "workspaceFolder": "/workspace"
}
```

- [ ] **Step 2: Create language fragments**

Write `src/devcc/data/languages/python.json`:
```json
{
  "_id": "python",
  "_name": "Python",
  "_default_version": "3.12",
  "_feature_key": "ghcr.io/devcontainers/features/python:1",
  "_version_param": "version",
  "_extra_apt_packages": [],
  "features": {
    "ghcr.io/devcontainers/features/python:1": { "version": "3.12" }
  },
  "customizations": { "vscode": { "extensions": ["ms-python.python"] } }
}
```

Write `src/devcc/data/languages/node.json`:
```json
{
  "_id": "node",
  "_name": "TypeScript / Node.js",
  "_default_version": "22",
  "_feature_key": "ghcr.io/devcontainers/features/node:1",
  "_version_param": "version",
  "_extra_apt_packages": [],
  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "22" }
  },
  "customizations": { "vscode": { "extensions": [] } }
}
```

Write `src/devcc/data/languages/rust.json`:
```json
{
  "_id": "rust",
  "_name": "Rust",
  "_default_version": "latest",
  "_feature_key": "ghcr.io/devcontainers/features/rust:1",
  "_version_param": "version",
  "_extra_apt_packages": [],
  "features": {
    "ghcr.io/devcontainers/features/rust:1": { "version": "latest" }
  },
  "customizations": { "vscode": { "extensions": ["rust-lang.rust-analyzer"] } }
}
```

Write `src/devcc/data/languages/r.json`:
```json
{
  "_id": "r",
  "_name": "R",
  "_default_version": "release",
  "_feature_key": "ghcr.io/rocker-devs/devcontainer-features/r-rig:1",
  "_version_param": "version",
  "_extra_apt_packages": [],
  "features": {
    "ghcr.io/rocker-devs/devcontainer-features/r-rig:1": { "version": "release" }
  },
  "customizations": { "vscode": { "extensions": ["REditorSupport.r"] } }
}
```

Write `src/devcc/data/languages/julia.json`:
```json
{
  "_id": "julia",
  "_name": "Julia",
  "_default_version": "latest",
  "_feature_key": "ghcr.io/meaningful-ooo/devcontainer-features/julia:1",
  "_version_param": "version",
  "_extra_apt_packages": [],
  "features": {
    "ghcr.io/meaningful-ooo/devcontainer-features/julia:1": { "version": "latest" }
  },
  "customizations": { "vscode": { "extensions": ["julialang.language-julia"] } }
}
```

Write `src/devcc/data/languages/c-cpp-fortran.json`:
```json
{
  "_id": "c-cpp-fortran",
  "_name": "C / C++ / Fortran",
  "_default_version": "latest",
  "_feature_key": "ghcr.io/devcontainers/features/cmake:1",
  "_version_param": "version",
  "_extra_apt_packages": ["build-essential", "gfortran", "gdb"],
  "features": {
    "ghcr.io/devcontainers/features/cmake:1": {},
    "ghcr.io/fortran-lang/devcontainer-features/fpm:1": {}
  },
  "customizations": { "vscode": { "extensions": ["ms-vscode.cpptools"] } }
}
```

- [ ] **Step 3: Create agent fragments**

Write `src/devcc/data/agents/claude-code.json`:
```json
{
  "_id": "claude-code",
  "_name": "Claude Code",
  "_install_command": "curl -fsSL https://claude.ai/install.sh | bash",
  "_config_dir": "/home/neo/.claude",
  "_requires_node": false
}
```

Write `src/devcc/data/agents/codex.json`:
```json
{
  "_id": "codex",
  "_name": "Codex",
  "_install_command": "npm install -g @openai/codex",
  "_config_dir": "/home/neo/.codex",
  "_requires_node": true
}
```

Write `src/devcc/data/agents/copilot.json`:
```json
{
  "_id": "copilot",
  "_name": "Copilot CLI",
  "_install_command": "npm install -g @github/copilot",
  "_config_dir": "/home/neo/.copilot",
  "_requires_node": true
}
```

Write `src/devcc/data/agents/gemini.json`:
```json
{
  "_id": "gemini",
  "_name": "Gemini CLI",
  "_install_command": "npm install -g @google/gemini-cli",
  "_config_dir": "/home/neo/.gemini",
  "_requires_node": true
}
```

Write `src/devcc/data/agents/cursor.json`:
```json
{
  "_id": "cursor",
  "_name": "Cursor CLI",
  "_install_command": "curl https://cursor.com/install -fsS | bash",
  "_config_dir": "/home/neo/.cursor",
  "_requires_node": false
}
```

- [ ] **Step 4: Create shell script base template**

Write `src/devcc/data/shared/common-setup.sh` (base template — generator appends agent chown lines).
Locale settings (LANG/LC_ALL) are handled exclusively by `containerEnv` and NOT duplicated here:
```bash
#!/bin/bash
# Shared setup for all devcontainers — runs in onCreateCommand

set -e

# Fix volume permissions (Docker volumes default to root ownership)
echo "Fixing volume permissions..."
sudo chown -R neo:neo /commandhistory

# Install git-delta (non-fatal — network may be slow)
echo "Installing git-delta ${GIT_DELTA_VERSION}..."
ARCH=$(dpkg --print-architecture)
if curl -fSL --retry 2 --connect-timeout 5 --max-time 30 \
  "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" \
  -o /tmp/git-delta.deb; then
  sudo dpkg -i /tmp/git-delta.deb
  rm -f /tmp/git-delta.deb
  echo "git-delta installed successfully."
else
  echo "WARNING: git-delta installation failed (network issue?). Skipping."
  rm -f /tmp/git-delta.deb
fi
```

Write `src/devcc/data/shared/zsh-custom.sh` (static — copied as-is).
Locale settings are NOT included here (handled by `containerEnv`):
```bash
# oh-my-zsh plugins
sed -i 's/^plugins=.*/plugins=(git)/' ~/.zshrc

# Custom settings appended to .zshrc
cat >> ~/.zshrc << 'EOF'

# Timestamp format for history
HIST_STAMPS="yyyy-mm-dd"

# autojump
[ -f /usr/share/autojump/autojump.sh ] && . /usr/share/autojump/autojump.sh

# bat is installed as batcat on Ubuntu
alias bat="batcat"
EOF
```

- [ ] **Step 5: Download and bundle the official devcontainer schema**

```bash
curl -fsSL https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.base.schema.json \
  -o src/devcc/data/schema/devContainer.base.schema.json
```

Verify it's valid JSON: `python -c "import json; json.load(open('src/devcc/data/schema/devContainer.base.schema.json'))"`

- [ ] **Step 6: Commit**

```bash
git add src/devcc/data/
git commit -m "feat: add fragment data files, shell scripts, and devcontainer schema"
```

---

### Task 3: DimensionConfig and Data Loading

**Files:**
- Create: `src/devcc/dimensions.py`
- Create: `tests/test_dimensions.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write tests for dimensions**

Write `tests/conftest.py`:
```python
"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Temporary output directory for generated templates."""
    out = tmp_path / "output"
    out.mkdir()
    return out
```

Write `tests/test_dimensions.py`:
```python
"""Tests for dimension config and data loading."""

import pytest

from devcc.dimensions import (
    DIMENSIONS,
    DimensionConfig,
    get_data_path,
    list_available,
    load_dimension_fragment,
    load_fragment,
)


class TestDimensionConfig:
    def test_languages_dimension_exists(self) -> None:
        langs = [d for d in DIMENSIONS if d.name == "languages"]
        assert len(langs) == 1
        assert langs[0].required is True
        assert langs[0].multi is True

    def test_agents_dimension_exists(self) -> None:
        agents = [d for d in DIMENSIONS if d.name == "agents"]
        assert len(agents) == 1
        assert agents[0].required is False
        assert agents[0].multi is True


class TestDataLoading:
    def test_get_data_path_exists(self) -> None:
        path = get_data_path()
        assert path.exists()
        assert (path / "base" / "base.json").exists()

    def test_load_fragment_base(self) -> None:
        path = get_data_path() / "base" / "base.json"
        frag = load_fragment(path)
        assert frag["image"] == "ubuntu:24.04"
        assert "features" in frag

    def test_load_dimension_fragment_python(self) -> None:
        lang_dim = DIMENSIONS[0]
        frag = load_dimension_fragment(lang_dim, "python")
        assert frag["_id"] == "python"
        assert frag["_name"] == "Python"
        assert "features" in frag

    def test_load_dimension_fragment_unknown_raises(self) -> None:
        lang_dim = DIMENSIONS[0]
        with pytest.raises(ValueError, match="Unknown languages ID: nonexistent"):
            load_dimension_fragment(lang_dim, "nonexistent")

    def test_list_available_languages(self) -> None:
        lang_dim = DIMENSIONS[0]
        langs = list_available(lang_dim)
        assert len(langs) == 6
        ids = {f["_id"] for f in langs}
        assert ids == {"python", "node", "rust", "r", "julia", "c-cpp-fortran"}

    def test_list_available_agents(self) -> None:
        agent_dim = DIMENSIONS[1]
        agents = list_available(agent_dim)
        assert len(agents) == 5
        ids = {f["_id"] for f in agents}
        assert ids == {"claude-code", "codex", "copilot", "gemini", "cursor"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_dimensions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devcc.dimensions'`

- [ ] **Step 3: Implement dimensions.py**

Write `src/devcc/dimensions.py`:
```python
"""Dimension configuration and fragment data loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

_DATA_REF = files("devcc") / "data"


@dataclass
class DimensionConfig:
    """Defines a fragment category (languages, agents, etc.)."""

    name: str
    dir_name: str
    cli_flag: str
    cli_name: str
    required: bool
    multi: bool


DIMENSIONS: list[DimensionConfig] = [
    DimensionConfig("languages", "languages", "-l", "langs", required=True, multi=True),
    DimensionConfig("agents", "agents", "-a", "agents", required=False, multi=True),
]


def get_data_path() -> Path:
    """Return the resolved path to the package data directory."""
    return Path(str(_DATA_REF))


def load_fragment(path: Path) -> dict[str, Any]:
    """Load a single JSON fragment file."""
    with open(path) as f:
        return json.load(f)


def load_dimension_fragment(dim: DimensionConfig, fragment_id: str) -> dict[str, Any]:
    """Load a specific fragment by ID from a dimension directory."""
    path = get_data_path() / dim.dir_name / f"{fragment_id}.json"
    if not path.exists():
        raise ValueError(f"Unknown {dim.name} ID: {fragment_id}")
    return load_fragment(path)


def list_available(dim: DimensionConfig) -> list[dict[str, Any]]:
    """List all available fragments for a dimension, sorted by filename."""
    dim_path = get_data_path() / dim.dir_name
    return [load_fragment(p) for p in sorted(dim_path.glob("*.json"))]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dimensions.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/devcc/dimensions.py tests/conftest.py tests/test_dimensions.py
git commit -m "feat: add DimensionConfig, fragment loading, and data path resolution"
```

---

### Task 4: deep_merge

**Files:**
- Create: `src/devcc/generator.py`
- Create: `tests/test_generator.py`

- [ ] **Step 1: Write tests for deep_merge**

Write `tests/test_generator.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py::TestDeepMerge -v`
Expected: FAIL — `ImportError: cannot import name 'deep_merge' from 'devcc.generator'`

- [ ] **Step 3: Implement deep_merge**

Write `src/devcc/generator.py`:
```python
"""Generator: merge fragments and produce devcontainer templates."""

from __future__ import annotations

import copy
import json
from typing import Any


def deep_merge(base: dict[str, Any], *overlays: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge dicts. Arrays concat+dedup, objects merge, scalars overwrite."""
    result = copy.deepcopy(base)
    for overlay in overlays:
        for key, value in overlay.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    seen: set[str] = set()
                    merged: list[Any] = []
                    for item in result[key] + value:
                        item_key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                        if item_key not in seen:
                            seen.add(item_key)
                            merged.append(item)
                    result[key] = merged
                else:
                    result[key] = copy.deepcopy(value)
            else:
                result[key] = copy.deepcopy(value)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py::TestDeepMerge -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/devcc/generator.py tests/test_generator.py
git commit -m "feat: add deep_merge with recursive object merge and array dedup"
```

---

### Task 5: resolve_custom_keys

**Files:**
- Modify: `src/devcc/generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write tests for resolve_custom_keys**

Append to `tests/test_generator.py`:
```python
from devcc.generator import resolve_custom_keys

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py::TestResolveCustomKeys -v`
Expected: FAIL — `ImportError: cannot import name 'resolve_custom_keys'`

- [ ] **Step 3: Implement resolve_custom_keys**

Append to `src/devcc/generator.py`:
```python
NODE_FEATURE_KEY = "ghcr.io/devcontainers/features/node:1"
APT_FEATURE_KEY = "ghcr.io/devcontainers-extra/features/apt-get-packages:1"


def resolve_custom_keys(
    merged: dict[str, Any],
    lang_fragments: list[dict[str, Any]],
    agent_fragments: list[dict[str, Any]],
    version_overrides: dict[str, str],
) -> dict[str, Any]:
    """Resolve all _-prefixed custom keys and strip them from output."""
    result = copy.deepcopy(merged)

    # 1. Extra apt packages
    extra_packages: list[str] = []
    for frag in lang_fragments + agent_fragments:
        extra_packages.extend(frag.get("_extra_apt_packages", []))
    if extra_packages:
        apt_feature = result.get("features", {}).get(APT_FEATURE_KEY, {})
        existing = apt_feature.get("packages", "")
        apt_feature["packages"] = existing + "," + ",".join(extra_packages)
        result["features"][APT_FEATURE_KEY] = apt_feature

    # 2. Agent install commands → postCreateCommand
    for frag in agent_fragments:
        result.setdefault("postCreateCommand", {})[frag["_id"]] = frag["_install_command"]

    # 3. Agent config dirs → mounts + containerEnv
    for frag in agent_fragments:
        agent_id = frag["_id"]
        config_dir = frag["_config_dir"]
        env_key = agent_id.replace("-", "_").upper() + "_CONFIG_DIR"
        mount = f"source=devcc-{agent_id}-config-${{devcontainerId}},target={config_dir},type=volume"
        result.setdefault("mounts", []).append(mount)
        result.setdefault("containerEnv", {})[env_key] = config_dir

    # 4. Node.js injection
    needs_node = any(frag.get("_requires_node", False) for frag in agent_fragments)
    has_node = NODE_FEATURE_KEY in result.get("features", {})
    if needs_node and not has_node:
        result["features"][NODE_FEATURE_KEY] = {"version": "22"}

    # 5. Version overrides
    for frag in lang_fragments:
        lang_id = frag["_id"]
        if lang_id in version_overrides:
            feature_key = frag["_feature_key"]
            version_param = frag["_version_param"]
            if feature_key in result.get("features", {}):
                result["features"][feature_key][version_param] = version_overrides[lang_id]

    # 6. Build name
    lang_names = [frag["_name"] for frag in lang_fragments]
    agent_names = [frag["_name"] for frag in agent_fragments]
    result["name"] = " + ".join(lang_names + agent_names)

    # 7. Strip all _-prefixed keys
    return _strip_custom_keys(result)


def _strip_custom_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Remove all keys starting with _ from a dict, recursively."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            result[key] = _strip_custom_keys(value)
        else:
            result[key] = value
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -v`
Expected: All tests PASS (deep_merge + resolve_custom_keys)

- [ ] **Step 5: Commit**

```bash
git add src/devcc/generator.py tests/test_generator.py
git commit -m "feat: add resolve_custom_keys with apt, agent, node injection, version override"
```

---

### Task 6: generate, write_output, build_setup_script, generate_batch

**Files:**
- Modify: `src/devcc/generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write tests for generate and build_setup_script**

Append to `tests/test_generator.py`:
```python
import json
from pathlib import Path

from devcc.generator import build_setup_script, generate, generate_batch


class TestBuildSetupScript:
    def test_no_agents(self) -> None:
        script = build_setup_script([])
        assert "chown -R neo:neo /commandhistory" in script
        assert "/home/neo/.claude" not in script

    def test_with_agent(self) -> None:
        agent_frags = [{"_id": "claude-code", "_name": "Claude Code",
                         "_install_command": "x", "_config_dir": "/home/neo/.claude",
                         "_requires_node": False}]
        script = build_setup_script(agent_frags)
        assert "chown -R neo:neo /home/neo/.claude" in script

    def test_multiple_agents(self) -> None:
        agent_frags = [
            {"_id": "claude-code", "_name": "CC", "_install_command": "x",
             "_config_dir": "/home/neo/.claude", "_requires_node": False},
            {"_id": "codex", "_name": "Codex", "_install_command": "x",
             "_config_dir": "/home/neo/.codex", "_requires_node": True},
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
        result = generate([("rust", None)], [], tmp_output)
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py::TestGenerate -v`
Expected: FAIL — `ImportError: cannot import name 'generate'`

- [ ] **Step 3: Implement generate, write_output, build_setup_script, generate_batch**

Append to `src/devcc/generator.py`:
```python
import shutil
from pathlib import Path

from devcc.dimensions import (
    DIMENSIONS,
    get_data_path,
    list_available,
    load_dimension_fragment,
    load_fragment,
)


def build_setup_script(agent_fragments: list[dict[str, Any]]) -> str:
    """Build common-setup.sh from base template + agent chown lines."""
    base_path = get_data_path() / "shared" / "common-setup.sh"
    with open(base_path) as f:
        script = f.read()

    if agent_fragments:
        chown_lines = [f"sudo chown -R neo:neo {frag['_config_dir']}" for frag in agent_fragments]
        script += "\n" + "\n".join(chown_lines) + "\n"

    return script


def write_output(
    resolved: dict[str, Any],
    agent_fragments: list[dict[str, Any]],
    output_dir: Path,
) -> Path:
    """Write devcontainer.json + shell scripts to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # devcontainer.json — 2-space indent, trailing newline
    with open(output_dir / "devcontainer.json", "w") as f:
        json.dump(resolved, f, indent=2)
        f.write("\n")

    # common-setup.sh — generated from template
    (output_dir / "common-setup.sh").write_text(build_setup_script(agent_fragments))

    # zsh-custom.sh — static copy
    zsh_src = get_data_path() / "shared" / "zsh-custom.sh"
    shutil.copy2(str(zsh_src), str(output_dir / "zsh-custom.sh"))

    return output_dir


def generate(
    languages: list[tuple[str, str | None]],
    agents: list[str],
    output_dir: Path,
) -> Path:
    """Generate a devcontainer template. Raises ValueError for unknown IDs."""
    from devcc.validator import validate_directory

    lang_dim = DIMENSIONS[0]
    agent_dim = DIMENSIONS[1]

    base = load_fragment(get_data_path() / "base" / "base.json")
    lang_fragments = [load_dimension_fragment(lang_dim, lid) for lid, _ in languages]
    agent_fragments = [load_dimension_fragment(agent_dim, aid) for aid in agents]

    version_overrides = {lid: ver for lid, ver in languages if ver is not None}

    merged = deep_merge(base, *lang_fragments, *agent_fragments)
    resolved = resolve_custom_keys(merged, lang_fragments, agent_fragments, version_overrides)

    path = write_output(resolved, agent_fragments, output_dir)

    # Auto-validate
    errors = validate_directory(path)
    if errors:
        raise RuntimeError(f"Validation failed: {'; '.join(errors)}")

    return path


def generate_batch(output_dir: Path) -> list[Path]:
    """Generate all single-lang x (single-agent + no-agent) combos."""
    lang_dim = DIMENSIONS[0]
    agent_dim = DIMENSIONS[1]
    all_langs = list_available(lang_dim)
    all_agents = list_available(agent_dim)

    paths: list[Path] = []
    for lang in all_langs:
        lang_id = lang["_id"]
        # No-agent combo (generate() auto-validates each)
        paths.append(generate([(lang_id, None)], [], output_dir / lang_id))
        # With each agent
        for agent in all_agents:
            agent_id = agent["_id"]
            dir_name = f"{lang_id}-{agent_id}"
            paths.append(generate([(lang_id, None)], [agent_id], output_dir / dir_name))

    return paths
```

Note: Move the `import shutil` and `from pathlib import Path` to the top of the file along with the existing imports. Also move `from devcc.dimensions import ...` to the top. The `from devcc.validator import validate_directory` is a lazy import inside `generate()` to avoid a circular import (validator imports dimensions, generator imports dimensions).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/devcc/generator.py tests/test_generator.py
git commit -m "feat: add generate, generate_batch, write_output, and build_setup_script"
```

---

### Task 7: Validator

**Files:**
- Create: `src/devcc/validator.py`
- Create: `tests/test_validator.py`

- [ ] **Step 1: Write tests for validator**

Write `tests/test_validator.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_validator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devcc.validator'`

- [ ] **Step 3: Implement validator**

Write `src/devcc/validator.py`:
```python
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
    validator = jsonschema.Draft7Validator(schema)
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

    for script in ["common-setup.sh", "zsh-custom.sh"]:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_validator.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/devcc/validator.py tests/test_validator.py
git commit -m "feat: add validator with official schema and devcc-specific checks"
```

---

### Task 8: CLI

**Files:**
- Create: `src/devcc/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write tests for CLI**

Write `tests/test_cli.py`:
```python
"""CLI integration tests using click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from devcc.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


class TestCreate:
    def test_python_claude_code(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(main, ["create", "-l", "python", "-a", "claude-code", "-o", str(out)])
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
        result = runner.invoke(main, ["create", "-l", "python,node", "-a", "claude-code", "-o", str(out)])
        assert result.exit_code == 0, result.output
        data = json.loads((out / "devcontainer.json").read_text())
        assert "Python" in data["name"]
        assert "Node.js" in data["name"]

    def test_invalid_language(self, runner: CliRunner, tmp_path: Path) -> None:
        out = tmp_path / ".devcontainer"
        result = runner.invoke(main, ["create", "-l", "cobol", "-o", str(out)])
        assert result.exit_code != 0
        assert "cobol" in result.output.lower() or "cobol" in (result.stderr or "").lower()

    def test_missing_language(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, ["create", "-o", str(tmp_path)])
        assert result.exit_code != 0


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ImportError: cannot import name 'main' from 'devcc.cli'`

- [ ] **Step 3: Implement CLI**

Write `src/devcc/cli.py`:
```python
"""Click CLI for devcc."""

from __future__ import annotations

from pathlib import Path

import click

from devcc.dimensions import DIMENSIONS, list_available
from devcc.generator import generate, generate_batch
from devcc.validator import validate_batch, validate_directory


def _parse_languages(langs_str: str) -> list[tuple[str, str | None]]:
    """Parse 'python:3.11,node:20' into [('python', '3.11'), ('node', '20')]."""
    result: list[tuple[str, str | None]] = []
    for item in langs_str.split(","):
        item = item.strip()
        if ":" in item:
            lang_id, version = item.split(":", 1)
            result.append((lang_id, version))
        else:
            result.append((item, None))
    return result


def _parse_agents(agents_str: str) -> list[str]:
    """Parse 'claude-code,codex' into ['claude-code', 'codex']."""
    return [a.strip() for a in agents_str.split(",") if a.strip()]


@click.group()
def main() -> None:
    """devcc — Generate devcontainer templates for AI coding agents."""


@main.command()
@click.option("-l", "--langs", required=True, help="Languages (e.g., python:3.11,node)")
@click.option("-a", "--agents", default="", help="Agents (e.g., claude-code,codex)")
@click.option("-o", "--output", default=".devcontainer", help="Output directory")
def create(langs: str, agents: str, output: str) -> None:
    """Generate a devcontainer template."""
    languages = _parse_languages(langs)
    agent_list = _parse_agents(agents) if agents else []
    output_dir = Path(output)

    try:
        path = generate(languages, agent_list, output_dir)
    except (ValueError, RuntimeError) as e:
        raise click.ClickException(str(e))

    click.echo(f"Generated: {path}")


@main.command()
@click.option("-o", "--output", default="templates", help="Output directory")
def batch(output: str) -> None:
    """Generate all template combinations."""
    output_dir = Path(output)

    try:
        paths = generate_batch(output_dir)
    except (ValueError, RuntimeError) as e:
        raise click.ClickException(str(e))

    click.echo(f"Generated {len(paths)} templates in {output_dir}")


@main.command("list-langs")
def list_langs() -> None:
    """List available languages."""
    lang_dim = DIMENSIONS[0]
    for frag in list_available(lang_dim):
        click.echo(f"{frag['_id']:<20} {frag['_name']:<25} (default: {frag['_default_version']})")


@main.command("list-agents")
def list_agents() -> None:
    """List available agents."""
    agent_dim = DIMENSIONS[1]
    for frag in list_available(agent_dim):
        click.echo(f"{frag['_id']:<20} {frag['_name']}")


@main.command()
@click.argument("path", default="templates")
def validate(path: str) -> None:
    """Validate generated templates."""
    target = Path(path)
    if not target.exists():
        raise click.ClickException(f"Path does not exist: {target}")

    # Single directory or batch?
    if (target / "devcontainer.json").exists():
        errors = validate_directory(target)
        if errors:
            for err in errors:
                click.echo(f"  ERROR: {err}", err=True)
            raise click.ClickException("Validation failed")
        click.echo("Valid")
    else:
        results = validate_batch(target)
        has_errors = False
        total = 0
        for name, errors in results.items():
            total += 1
            if errors:
                has_errors = True
                click.echo(f"{name}:", err=True)
                for err in errors:
                    click.echo(f"  ERROR: {err}", err=True)

        if has_errors:
            raise click.ClickException("Validation failed for some templates")
        click.echo(f"All {total} templates valid")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests across all test files PASS

- [ ] **Step 6: Commit**

```bash
git add src/devcc/cli.py tests/test_cli.py
git commit -m "feat: add click CLI with create, batch, list-langs, list-agents, validate"
```

---

### Task 9: End-to-End Verification

**Files:** None (verification only)

- [ ] **Step 1: uv sync**

Run: `uv sync`
Expected: Clean install

- [ ] **Step 2: devcc help**

Run: `uv run devcc --help`
Expected: Shows group help with all commands listed

- [ ] **Step 3: devcc create with agent**

Run: `uv run devcc create -l python -a claude-code -o /tmp/devcc-test`
Expected: Generates valid `.devcontainer/` with Python + Claude Code

- [ ] **Step 4: devcc create without agent**

Run: `uv run devcc create -l python -o /tmp/devcc-test-noagent`
Expected: Generates valid output without agent entries

- [ ] **Step 5: devcc create with version override**

Run: `uv run devcc create -l python:3.11 -a claude-code -o /tmp/devcc-test-ver`
Expected: Python version is 3.11 in output

- [ ] **Step 6: devcc batch**

Run: `uv run devcc batch -o /tmp/devcc-batch`
Expected: 36 template directories generated

- [ ] **Step 7: devcc validate**

Run: `uv run devcc validate /tmp/devcc-batch`
Expected: "All 36 templates valid"

- [ ] **Step 8: pytest**

Run: `uv run pytest -v`
Expected: All tests pass

- [ ] **Step 9: devcc list-langs**

Run: `uv run devcc list-langs`
Expected: Lists 6 languages with default versions

- [ ] **Step 10: devcc list-agents**

Run: `uv run devcc list-agents`
Expected: Lists 5 agents

- [ ] **Step 11: Commit any fixes and final state**

If any issues were found and fixed during verification, commit them:
```bash
git add -A
git commit -m "fix: address issues found during end-to-end verification"
```
