
## Hard rules
- The name format for plans and specs must be "YYMMDD-plan-<topic>.md" or "YYMMDD-spec-<topic>.md"
- Plan files is in ".dev/plan/" and spec files is in ".dev/spec/"


## Tech Stack

- **Package manager**: `uv`
- **CLI framework**: `click`
- **Linting/formatting**: `ruff` (check + format)
- **Testing**: `pytest` with click's `CliRunner`
- **Python**: >= 3.11
- **Build backend**: `hatchling`

## Coding Standards

- **Static typing**: All functions must have full type annotations (parameters + return types)
- **Modular architecture**: The generator uses a dimension system — new fragment categories (e.g., GPU) are added by registering a `DimensionConfig`, not by modifying core logic
- **Auto-validation**: `devcc create` and `devcc batch` validate output automatically after generation


## Common Commands for Development

```bash
uv sync                                          # install dependencies
uv run devcc create -l python -a claude-code     # generate .devcontainer/
uv run devcc batch                               # generate all 36 templates
uv run devcc validate                            # validate generated templates
uv run ruff check src/ tests/                    # lint
uv run ruff format src/ tests/                   # format
uv run pytest                                    # run tests
```

## Supported Agents

| Agent | Install Command | Config Dir |
|---|---|---|
| Claude Code | `curl -fsSL https://claude.ai/install.sh \| bash` | `~/.claude` |
| Codex | `npm install -g @openai/codex` | `~/.codex` |
| Copilot CLI | `npm install -g @github/copilot` | `~/.copilot` |
| Gemini CLI | `npm install -g @google/gemini-cli` | `~/.gemini` |
| Cursor CLI | `curl https://cursor.com/install -fsS \| bash` | `~/.cursor` |
