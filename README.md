# devcc

`devcc` creates [devcontainer](https://containers.dev/) templates for running AI coding agents in isolated, reproducible environments. Pick a language, pick an agent, and get a ready-to-use `.devcontainer/`.

## Installation

```bash
pip install devcc
```

## Step 1: See What languages and agents are available

```bash
devcc list
```

```
Languages:
  python               Python                    (default: latest)
  node                 TypeScript / Node.js      (default: latest)

Agents:
  claude-code          Claude Code CLI
  codex                Codex
  copilot              Copilot CLI
  cursor               Cursor CLI
  gemini               Gemini CLI
```

## Step 2: Generate a devcontainer template

Go to your project repository and run:

```bash
cd /path/to/your/project
devcc create -l python -a claude-code
```

This creates a `.devcontainer/` folder in your project:

```
.devcontainer/
├── devcontainer.json    # container configuration
├── common-setup.sh      # system setup (volume permissions, git-delta)
└── zsh-custom.sh        # shell customization (oh-my-zsh, autojump, aliases)
```

### More Examples

```bash
# Pin a specific language version
devcc create -l python:3.11 -a claude-code

# Multiple languages in one container
devcc create -l python,node -a claude-code

# Multiple agents
devcc create -l python -a claude-code,codex

# Language only, no agent
devcc create -l node

# Custom output directory
devcc create -l python -a claude-code -o my-devcontainer
```

## Step 3: Start the Dev Container

**Option A: VS Code**

1. Open your project in VS Code
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) if you haven't already
3. Press `F1` and select **Dev Containers: Reopen in Container**
4. VS Code builds the container and sets up your environment

**Option B: CLI** (using the [Dev Container CLI](https://github.com/devcontainers/cli))

```bash
# Install the CLI (once)
npm install -g @devcontainers/cli

# Build and start the container
devcontainer up --workspace-folder .

# Open a shell inside the container
devcontainer exec --workspace-folder . zsh
```

Once inside the container, your agent is ready to use (e.g., run `claude` for Claude Code).

## What You Get

Every generated container includes:

- **Ubuntu 24.04** base image
- **Non-root user** `neo`
- **Workspace mount:** your project is bind-mounted to `/workspace`
- **Zsh and oh-my-zsh** with a custom theme and plugins
- **Your language(s)** with the correct devcontainer feature and VS Code extension
- **Your agent(s)** installed automatically on container creation
- **Persistent volumes:** shell history and agent config survive container rebuilds

## Validation

Validate devcontainer templates against the [official devcontainer JSON schema](https://containers.dev/implementors/json_schema/):

```bash
devcc validate .devcontainer
```

You don't need to validate the `devcontainer.json` created by `devcc`. However, if you manually edit the generated `devcontainer.json`, you can run validation to ensure it remains compliant with the schema.