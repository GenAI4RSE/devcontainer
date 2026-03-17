# Spec: devcc Python Package

## Overview

Transform the static devcontainer template repository into a pip-installable Python package (`devcc`) that dynamically generates devcontainer templates from composable JSON fragments. The generator uses a dimension system where fragment categories (languages, agents, future: GPU) are registered via `DimensionConfig` — new dimensions require no changes to core logic.

## Fragment Schema

Fragments are JSON files under `src/devcc/data/` that resemble partial `devcontainer.json` files, plus custom keys prefixed with `_` that the generator resolves before output.

### Base Fragment (`data/base/base.json`)

Contains everything shared across all templates. All of the following fields are included:

- `$schema`: devcontainer JSON schema URL (for editor IntelliSense, separate from the bundled validation schema)
- `image`: `"ubuntu:24.04"`
- `init`: `true`
- `features`: common-utils (user "neo", zsh), github-cli, apt-get-packages (`"jq,vim,bat,autojump"`)
- `onCreateCommand`: `{ "system-setup": "bash .devcontainer/common-setup.sh" }`
- `postCreateCommand`: `{ "zsh-custom": "bash .devcontainer/zsh-custom.sh" }`
- `waitFor`: `"postCreateCommand"`
- `customizations`: `{ "vscode": { "extensions": [] } }`
- `containerUser`: `"neo"`
- `remoteUser`: `"neo"`
- `mounts`: bash history volume (`source=devcc-bashhistory-${devcontainerId},target=/commandhistory,type=volume`)
- `containerEnv`: HISTFILE, GIT_DELTA_VERSION, POWERLEVEL9K_DISABLE_GITSTATUS, LANG, LC_ALL, DEVCONTAINER, EDITOR, VISUAL, TZ
- `workspaceMount`: bind mount to `/workspace`
- `workspaceFolder`: `"/workspace"`

### Language Fragments (`data/languages/<id>.json`)

Each language fragment contributes its devcontainer feature, VS Code extensions, and optionally extra apt packages.

Custom keys:

| Key | Type | Purpose |
|-----|------|---------|
| `_id` | `str` | Identifier used in CLI and directory naming |
| `_name` | `str` | Display name (e.g., "Python", "C / C++ / Fortran") |
| `_default_version` | `str` | Default version when user doesn't specify one |
| `_feature_key` | `str` | Which feature URI holds the version parameter |
| `_version_param` | `str` | Parameter name within the feature (usually `"version"`) |
| `_extra_apt_packages` | `list[str]` | Appended to the base apt-get-packages string |

Example (`data/languages/python.json`):
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

Example with extra apt packages (`data/languages/c-cpp-fortran.json`):
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

### Agent Fragments (`data/agents/<id>.json`)

Agent fragments are metadata-only (all custom keys, no standard devcontainer keys). The generator uses the metadata to inject postCreateCommand entries, config dir mounts, and env vars.

Custom keys:

| Key | Type | Purpose |
|-----|------|---------|
| `_id` | `str` | Identifier used in CLI and directory naming |
| `_name` | `str` | Display name |
| `_install_command` | `str` | Shell command for postCreateCommand |
| `_config_dir` | `str` | Absolute path to agent's config directory |
| `_requires_node` | `bool` | If true, inject Node.js feature when not already present |

Example (`data/agents/claude-code.json`):
```json
{
  "_id": "claude-code",
  "_name": "Claude Code",
  "_install_command": "curl -fsSL https://claude.ai/install.sh | bash",
  "_config_dir": "/home/neo/.claude",
  "_requires_node": false
}
```

Example with Node.js dependency (`data/agents/codex.json`):
```json
{
  "_id": "codex",
  "_name": "Codex",
  "_install_command": "npm install -g @openai/codex",
  "_config_dir": "/home/neo/.codex",
  "_requires_node": true
}
```

### Supported Languages

| ID | Name | Feature | Default Version |
|----|------|---------|----------------|
| `python` | Python | `ghcr.io/devcontainers/features/python:1` | 3.12 |
| `node` | TypeScript / Node.js | `ghcr.io/devcontainers/features/node:1` | 22 |
| `rust` | Rust | `ghcr.io/devcontainers/features/rust:1` | latest |
| `r` | R | `ghcr.io/rocker-devs/devcontainer-features/r-rig:1` | release |
| `julia` | Julia | `ghcr.io/meaningful-ooo/devcontainer-features/julia:1` | latest |
| `c-cpp-fortran` | C / C++ / Fortran | cmake:1 + fpm:1 | latest |

### Supported Agents

| ID | Name | Install Command | Config Dir | Requires Node |
|----|------|----------------|------------|---------------|
| `claude-code` | Claude Code | `curl -fsSL https://claude.ai/install.sh \| bash` | `~/.claude` | No |
| `codex` | Codex | `npm install -g @openai/codex` | `~/.codex` | Yes |
| `copilot` | Copilot CLI | `npm install -g @github/copilot` | `~/.copilot` | Yes |
| `gemini` | Gemini CLI | `npm install -g @google/gemini-cli` | `~/.gemini` | Yes |
| `cursor` | Cursor CLI | `curl https://cursor.com/install -fsS \| bash` | `~/.cursor` | No |

## DimensionConfig

```python
@dataclass
class DimensionConfig:
    name: str           # "languages", "agents"
    dir_name: str       # directory under data/
    cli_flag: str       # "-l", "-a"
    cli_name: str       # "langs", "agents"
    required: bool      # True = must pick at least one
    multi: bool         # True = can pick multiple

DIMENSIONS: list[DimensionConfig] = [
    DimensionConfig("languages", "languages", "-l", "langs", required=True, multi=True),
    DimensionConfig("agents", "agents", "-a", "agents", required=False, multi=True),
]
```

## Generator Pipeline

```
load_fragment(path) -> dict
       |
load_dimension(dim, selections) -> list[dict]
       |
deep_merge(base, *fragments) -> dict
       |
resolve_custom_keys(merged) -> dict
       |
write_output(resolved, output_dir) -> Path
```

### Merge Order

Fragments are merged in this order: **base → languages (left-to-right from CLI) → agents (left-to-right from CLI)**. This means language values override base, and agent values override both. Within a dimension, the order follows the CLI argument order (e.g., `-l python,node` merges python first, then node).

### Merge Rules

| Value type | Strategy |
|-----------|----------|
| Objects (`features`, `containerEnv`, `postCreateCommand`) | Recursive merge; later values overwrite on key conflict |
| Arrays (`extensions`, `mounts`) | Concatenate, deduplicate |
| Scalars (`image`, `containerUser`) | Later value wins |

### Custom Key Resolution

Single pass over the merged dict:

1. **`_extra_apt_packages`**: Collect from all fragments into a single list. Join with commas and append to the base `apt-get-packages` string (e.g., `"jq,vim,bat,autojump"` becomes `"jq,vim,bat,autojump,build-essential,gfortran,gdb"`).
2. **`_install_command` + `_id`** (agents): Add `postCreateCommand[agent_id] = install_command`
3. **`_config_dir`** (agents): Add mount (`source=devcc-{agent_id}-config-${devcontainerId},target={config_dir},type=volume`) and `containerEnv[{AGENT_UPPER}_CONFIG_DIR] = config_dir` where `{AGENT_UPPER}` is the agent `_id` with hyphens replaced by underscores and uppercased (e.g., `claude-code` → `CLAUDE_CODE_CONFIG_DIR`). Also append a `chown` line to the generated `common-setup.sh`.
4. **`_requires_node`**: If any agent has `true` and no Node.js feature key (`ghcr.io/devcontainers/features/node:1`) exists in `features`, inject it with `version: "22"`. If the `node` language is already selected, its version takes precedence — the injection is skipped entirely (not merged).
5. **Version override**: If user specified a version for a language, overwrite `features[_feature_key][_version_param]`. Only the feature declared in `_feature_key` receives the override — other features in the same fragment (e.g., `fpm:1` in c-cpp-fortran) are not affected.
6. **`name` field**: Build from language and agent display names (e.g., `"Python"`, `"Python + Claude Code"`, `"Python + Node.js + Claude Code + Codex"`)
7. **Strip all `_`-prefixed keys** from the final output

### Key Functions

- `deep_merge(base: dict, *overlays: dict) -> dict` — generic recursive merge
- `resolve_custom_keys(merged: dict) -> dict` — applies all resolution rules, strips `_` keys
- `generate(languages: list[tuple[str, str | None]], agents: list[str], output_dir: Path) -> Path` — top-level entry point. Language tuples are `(id, version_or_none)`. Returns the output directory path. Raises `ValueError` for unknown language/agent IDs.
- `generate_batch(output_dir: Path) -> list[Path]` — all single-lang x single-agent combos + no-agent combos (6 × 6 = 36 total). Batch intentionally generates only single-language combinations; multi-language is a `create`-only feature. Batch uses default versions for all languages.

### Output Structure

Single generation writes to `<output_dir>/`:
```
<output_dir>/
├── devcontainer.json
├── common-setup.sh
└── zsh-custom.sh
```

Batch generation writes to `<output_dir>/`:
```
templates/
├── python/                     # no agent
├── python-claude-code/
├── python-codex/
├── ...
├── c-cpp-fortran/
├── c-cpp-fortran-claude-code/
└── ...
```

Shell scripts (`common-setup.sh`, `zsh-custom.sh`) are shipped as package data under `data/shared/` and copied into each output directory.

**`common-setup.sh` is generated from a base template.** The base template is stored in `data/shared/common-setup.sh` and contains volume permission fixes (bash history `chown`) and git-delta installation. Locale settings (LANG, LC_ALL) are handled exclusively by `containerEnv` and are NOT duplicated in shell scripts. At generation time, the generator reads this base template and appends agent-specific `chown` lines for each selected agent's config directory mount. When no agent is selected, no agent `chown` lines are appended.

**`zsh-custom.sh` is static** — it configures oh-my-zsh plugins, history timestamps, autojump sourcing, and the `bat`→`batcat` alias. Locale settings are NOT included (handled by `containerEnv`).

## Validator

### Layer 1: Official devcontainer schema

Validate `devcontainer.json` against the official JSON schema from `https://containers.dev/implementors/json_schema/`. Uses the `jsonschema` library. Schema is bundled in `data/schema/devContainer.base.schema.json` (fetched once at build time, not at runtime).

### Layer 2: devcc-specific checks

- No `_`-prefixed custom keys remain in output
- `common-setup.sh` and `zsh-custom.sh` exist alongside the JSON
- `name` field is non-empty

### Functions

- `validate_directory(path: Path) -> list[str]` — checks file existence, runs both layers
- `validate_devcontainer_json(data: dict) -> list[str]` — Layer 1 + Layer 2 on parsed dict
- `validate_batch(templates_dir: Path) -> dict[str, list[str]]` — validates all subdirectories

### Auto-validation

`generate()` and `generate_batch()` call the validator after writing output. Validation failures raise with error details. The CLI surfaces as non-zero exit codes.

## CLI Interface

```bash
devcc create -l python -a claude-code             # single combo → .devcontainer/
devcc create -l python:3.11,node:20 -a codex      # multi-lang, explicit versions
devcc create -l rust                               # no agent
devcc create -l python -a claude-code -o /tmp/out  # custom output dir
devcc batch                                        # all 36 templates → templates/
devcc batch -o /tmp/templates                      # custom batch output
devcc list-langs                                   # available languages + defaults
devcc list-agents                                  # available agents
devcc validate                                     # validate templates/ dir
devcc validate .devcontainer                       # validate specific dir
```

Default output for `create` is `.devcontainer/` in the current directory. Default output for `batch` is `templates/` in the current directory.

## Package Structure

```
├── pyproject.toml
├── Makefile
├── src/
│   └── devcc/
│       ├── __init__.py
│       ├── __main__.py            # python -m devcc
│       ├── cli.py                 # click group + commands
│       ├── generator.py           # merge logic, resolve, generate
│       ├── validator.py           # schema + devcc validation
│       ├── dimensions.py          # DimensionConfig + DIMENSIONS
│       └── data/
│           ├── base/base.json
│           ├── languages/*.json
│           ├── agents/*.json
│           ├── shared/common-setup.sh
│           ├── shared/zsh-custom.sh
│           └── schema/devContainer.base.schema.json
├── tests/
│   ├── conftest.py
│   ├── test_generator.py
│   ├── test_validator.py
│   └── test_cli.py
└── templates/                     # generated output (gitignored)
```

## pyproject.toml

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

## Data Path Resolution

Use `importlib.resources` to locate `data/` at runtime:
```python
from importlib.resources import files
DATA_DIR = files("devcc") / "data"
```

This works for both editable installs (`uv sync`) and installed wheels.

## Testing

### `tests/conftest.py`

Shared fixtures: sample fragments as dicts, `tmp_path`-based output directories.

### `tests/test_generator.py`

- `deep_merge`: objects merge recursively, arrays concat+dedup, scalars overwrite
- `resolve_custom_keys`: `_extra_apt_packages` appends to apt string, `_install_command` becomes postCreateCommand entry, `_config_dir` becomes mount+env, `_requires_node` injects Node feature, all `_` keys stripped
- Version override: `python:3.11` overwrites feature version
- No-agent generation: no agent entries in output
- Multi-lang merge: features and extensions combined
- Node.js dedup: `node` language + npm-based agent doesn't duplicate Node feature
- Multi-agent: `-a claude-code,codex` produces two postCreateCommand entries, two config mounts, Node.js injected from codex
- Generated `common-setup.sh` contains correct `chown` lines for selected agents

### `tests/test_validator.py`

- Valid template passes both layers
- Missing shell scripts caught
- Leftover `_` keys caught
- Invalid JSON schema caught (official schema layer)

### `tests/test_cli.py`

Integration tests with `CliRunner`:
- `create` produces valid output with expected files
- `create` with no agent works
- `create` with version override works
- `batch` generates 36 directories
- `list-langs` / `list-agents` show expected output
- `validate` returns 0 on valid, non-zero on invalid
- Invalid language/agent ID gives clear error

## Output Formatting

Generated `devcontainer.json` uses 2-space indentation with a trailing newline, matching the existing hand-crafted templates. All functions must have full type annotations (parameters + return types) per project coding standards.

## Verification Criteria

1. `uv sync` installs the package
2. `uv run devcc` shows help
3. `uv run devcc create -l python -a claude-code` produces valid `.devcontainer/`
4. `uv run devcc create -l python` produces valid output without agent
5. `uv run devcc create -l python:3.11 -a claude-code` uses Python 3.11
6. `uv run devcc batch` produces 36 templates
7. `uv run devcc validate` passes on all generated templates
8. `uv run pytest` — all tests pass
