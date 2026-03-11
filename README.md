# DevContainer Templates for AI Coding Agents

Pre-configured [devcontainer](https://containers.dev/) templates for running AI coding agents in isolated, reproducible and more safe environments. Each template provides a fully set up development container for a specific language, with Claude Code CLI pre-installed.


## Quick Start

1. Copy the files for your language into your project:

   ```bash
   # Example: Python
   mkdir -p .devcontainer
   cp devcontainer/python/devcontainer.json .devcontainer/
   cp devcontainer/common-setup.sh .devcontainer/
   cp devcontainer/zsh-custom.sh .devcontainer/
   ```

2. Open the project in VS Code and select **Reopen in Container**.

3. Once the container starts, Claude Code is ready to use:

   ```bash
   claude
   ```

## Supported Languages

| Template | Language / Runtime | Version | VS Code Extension |
|---|---|---|---|
| `python/` | Python | 3.12 | `ms-python.python` |
| `c-cpp-fortran/` | C / C++ / Fortran | gcc, gfortran, gdb, CMake, fpm | `ms-vscode.cpptools` |
| `rust/` | Rust | latest | `rust-lang.rust-analyzer` |
| `r/` | R | release | `REditorSupport.r` |
| `julia/` | Julia | latest | `julialang.language-julia` |
| `node/` | TypeScript / Node.js | 22 | -- |

## Common Features

All templates share:

- **Base image:** Ubuntu 24.04
- **Non-root user:** `neo` with zsh (oh-my-zsh) as default shell
- **Claude Code CLI** installed automatically on container creation
- **CLI tools:** jq, vim, bat, autojump, GitHub CLI, git-delta
- **Workspace mount:** your project directory is automatically bind-mounted to `/workspace`
- **Persistent volumes:** shell history and `~/.claude` config survive container rebuilds

## How It Works

Each template is a single `devcontainer.json` that composes [devcontainer features](https://containers.dev/features) — no custom Dockerfiles needed. The container lifecycle runs two shared scripts:

- **`common-setup.sh`** (onCreateCommand) — configures UTF-8 locale, fixes Docker volume permissions for the `neo` user, and installs git-delta with retry logic.
- **`zsh-custom.sh`** (postCreateCommand) — configures oh-my-zsh plugins, sets up autojump, aliases `bat` to `batcat`, and applies history timestamp formatting.

Claude Code CLI is installed via `curl -fsSL https://claude.ai/install.sh | bash` during `postCreateCommand`.

## Customization

You can easily customize the templates to fit your needs:

- **New language:** Copy any template, swap the language feature, and update the VS Code extension.
- **Additional packages:** Add to the `packages` list in the `apt-get-packages` feature.
- **VS Code extensions:** Add to the `customizations.vscode.extensions` array.
- **Use a different AI agent:** Replace the `claude-code` entry in `postCreateCommand` with the install command for your preferred agent (e.g., Aider, Codex CLI, or Gemini CLI).
- **Firewall rules:** Restrict network access by adding `"runArgs": ["--network=none"]` to the `devcontainer.json`, or configure iptables rules in `common-setup.sh` to sandbox what the agent can reach.


## Acknowledgements
This work is inspired by the official [Claude Code development containers](https://code.claude.com/docs/en/devcontainer), which also demonstrate applying firewall rules to the container.