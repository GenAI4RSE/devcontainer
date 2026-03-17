# Plan: Transform Repo into a Python Package (`devcc`)

## Context

The repo currently has `generate.py`, `validate.py`, `fragments/`, and `templates/` at the root level. The goal is to make this a proper pip-installable Python package managed by `uv`, with static typing, click CLI, and pytest tests.

## Target Structure
```
├── LICENSE
├── README.md
├── pyproject.toml                    # uv/package config
├── Makefile
├── src/
│   └── devcc/
│       ├── __init__.py
│       ├── cli.py                    # click group + commands
│       ├── generator.py             # core merge logic (typed)
│       ├── validator.py             # schema validation (typed)
│       └── data/                    # package data
│           ├── base/base.json
│           ├── languages/*.json
│           ├── agents/*.json
│           └── shared/*.sh
├── tests/
│   ├── conftest.py                  # shared fixtures
│   ├── test_generator.py            # unit tests for merge logic
│   ├── test_validator.py            # unit tests for validation
│   └── test_cli.py                  # click CliRunner tests
├── templates/                       # generated output (gitignored)
└── .gitignore
```

## Modular Fragment Architecture

The generator treats fragment categories as **dimensions** — each dimension is a directory under `data/` with `.json` fragments that get merged into the output. Adding a new dimension (e.g., GPU support) means:
1. Add a `data/gpu/` directory with fragment files (e.g., `nvidia.json`)
2. Register the dimension in a config (name, CLI flag, required/optional)
3. No changes to core merge logic

```
data/
├── base/base.json           # always included
├── languages/*.json         # dimension: required, pick 1+
├── agents/*.json            # dimension: required, pick 1+
└── gpu/*.json               # dimension: optional, pick 0-1 (future)
```

Each dimension is defined by a `DimensionConfig`:
```python
@dataclass
class DimensionConfig:
    name: str          # "languages", "agents", "gpu"
    dir_name: str      # directory under data/
    cli_flag: str      # "-l", "-a", "-g"
    cli_name: str      # "langs", "agents", "gpu"
    required: bool     # True for languages/agents, False for gpu
    id_key: str        # key in fragment JSON: "dir_name", "agent_id", "gpu_id"
    label_key: str     # key for display: "name", "agent_label", "gpu_label"
```

Dimensions are registered in a list — the CLI and generator iterate over this list, so adding a new dimension is just appending to the list + adding fragment files.

## Key Design Decisions

### Package tooling: `uv`
- `uv init`, `uv add click`, `uv add --dev pytest`
- `uv run devcc create -l python -a claude-code`
- `uv run pytest`

### CLI framework: `click`
- 1 dependency, clean API
- Built-in `CliRunner` for testing (no extra test deps)

### Static typing
- All functions fully typed with type hints
- Return types, parameter types, TypedDict for fragment schemas

### Testing: `pytest` + click `CliRunner`
- **`test_generator.py`**: unit tests for `deep_merge`, `merge_all`, `handle_extra_apt_packages`, `build_agent_setup_script`, `strip_custom_keys`, Node.js dedup, multi-lang/agent merging
- **`test_validator.py`**: unit tests for schema validation, template metadata validation, error detection
- **`test_cli.py`**: integration tests using click's `CliRunner`:
  ```python
  from click.testing import CliRunner
  from devcc.cli import main

  def test_create(tmp_path):
      runner = CliRunner()
      result = runner.invoke(main, ["create", "-l", "python", "-a", "claude-code", "-o", str(tmp_path)])
      assert result.exit_code == 0
      assert (tmp_path / "devcctainer.json").exists()
  ```
- Use `tmp_path` fixture for output directories
- Use `CliRunner(mix_stderr=False)` for clean stderr/stdout separation

### Auto-validation
- `devcc create` and `devcc batch` automatically validate output after generation
- Fail fast with clear error if validation fails

## CLI Interface
```bash
devcc create -l python -a claude-code             # single combo → .devcctainer/
devcc create -l python,node -a claude-code,copilot # multi combo
devcc create -l python -a claude-code -o /tmp/out  # custom output
devcc batch                                        # all 30 templates → templates/
devcc list-langs                                   # available languages
devcc list-agents                                  # available agent CLIs
devcc validate                                     # validate templates/ (batch)
devcc validate .devcctainer                       # validate specific dir
```

## `pyproject.toml`
```toml
[project]
name = "devcc"
version = "0.1.0"
description = "Generate devcctainer templates for AI coding agents"
requires-python = ">=3.11"
dependencies = ["click"]

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

## Implementation Steps

### Step 1: Set up package with uv
- `uv init` or create `pyproject.toml` manually
- `uv add click`
- `uv add --dev pytest`
- Create `src/devcc/__init__.py`

### Step 2: Move fragments → `src/devcc/data/`
- Move `fragments/` content to `src/devcc/data/`
- Use `importlib.resources` for runtime data path resolution

### Step 3: Create `src/devcc/generator.py` (typed)
- Extract core merge logic from `generate.py`
- Add full type annotations
- Dimension-aware: `load_dimension(name)` replaces `load_all_languages()`/`load_all_agents()`
- `merge_all(base, selections: dict[str, list[dict]])` takes a dict of dimension→fragments
- `DimensionConfig` dataclass defines each dimension's metadata
- `DIMENSIONS` list registers all known dimensions — add new ones here

### Step 4: Create `src/devcc/validator.py` (typed)
- Move from `validate.py`
- Add full type annotations
- Expose `validate_devcctainer_json()`, `validate_template_json()`, `validate_directory()`

### Step 5: Create `src/devcc/cli.py` (click)
- `@click.group` with commands: `create`, `batch`, `list-langs`, `list-agents`, `validate`
- `create` and `batch` call validator after generation
- Add `__main__.py` for `python -m devcc`

### Step 6: Write tests
- `tests/conftest.py`: fixtures for sample fragments, tmp output dirs
- `tests/test_generator.py`: unit tests for all merge/build functions
- `tests/test_validator.py`: unit tests for validation logic
- `tests/test_cli.py`: CliRunner integration tests for all commands

### Step 7: Update Makefile
```makefile
generate:
	uv run devcc batch
validate:
	uv run devcc validate
test:
	uv run pytest
```

### Step 8: Clean up old files
- Delete `generate.py`, `validate.py`, `fragments/`

### Step 9: Update README.md
- Install: `pip install devcc` or `uv add devcc`
- Usage examples with `devcc` CLI
- Development: `uv sync && uv run pytest`

## Verification
1. `uv sync` installs the package
2. `uv run devcc` shows help
3. `uv run devcc create -l python -a claude-code` produces valid `.devcctainer/`
4. `uv run devcc batch` produces 30 templates
5. `uv run devcc validate` passes
6. `uv run pytest` — all tests pass
7. `pip install .` works from a clean venv
