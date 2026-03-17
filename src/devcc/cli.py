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


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def main() -> None:
    """devcc — Generate devcontainer templates for AI coding agents."""


@main.command()
@click.option(
    "-l",
    "--langs",
    required=False,
    default=None,
    help="\b\n"
    "Comma-separated languages with optional version.\n"
    "E.g., python, python:3.11, python:3.11,node:20.\n"
    "Run 'devcc list-langs' to see available options.",
)
@click.option(
    "-a",
    "--agents",
    default="",
    help="\b\n"
    "Comma-separated AI coding agents.\n"
    "E.g., claude-code, claude-code,codex.\n"
    "Optional — omit for a plain language template.\n"
    "Run 'devcc list-agents' to see available options.",
)
@click.option(
    "-o",
    "--output",
    default=".devcontainer",
    show_default=True,
    help="Output directory.",
)
@click.pass_context
def create(ctx: click.Context, langs: str | None, agents: str, output: str) -> None:
    """Create a devcontainer from one or more languages and agents.

    \b
    Supports multiple languages and agents in a single template:
      devcc create -l python                        # language only
      devcc create -l python -a claude-code         # with an agent
      devcc create -l python:3.11,node:20 -a codex  # multi-lang + version
    """
    if not langs:
        click.echo(ctx.get_help())
        ctx.exit(0)
        return
    languages = _parse_languages(langs)
    agent_list = _parse_agents(agents) if agents else []
    output_dir = Path(output)

    try:
        path = generate(languages, agent_list, output_dir)
    except (ValueError, RuntimeError) as e:
        raise click.ClickException(str(e)) from None

    click.echo(f"Generated: {path}")


@main.command()
@click.option(
    "-o",
    "--output",
    default="templates",
    show_default=True,
    help="Output directory.",
)
def batch(output: str) -> None:
    """Create devcontainers for language-agent pair combinations.

    \b
    Produces 6 languages x (5 agents + no-agent) = 36 templates.
    Each template gets its own directory with:
      devcontainer.json, common-setup.sh, zsh-custom.sh
    Directory naming: <lang> or <lang>-<agent>
      e.g., python/, python-claude-code/, rust-codex/
    All templates are auto-validated after generation.
    """
    output_dir = Path(output)

    try:
        paths = generate_batch(output_dir)
    except (ValueError, RuntimeError) as e:
        raise click.ClickException(str(e)) from None

    click.echo(f"Generated {len(paths)} templates in {output_dir}")


@main.command("list-langs")
def list_langs() -> None:
    """List available languages and their default versions."""
    lang_dim = DIMENSIONS[0]
    for frag in list_available(lang_dim):
        click.echo(f"{frag['_id']:<20} {frag['_name']:<25} (default: {frag['_default_version']})")


@main.command("list-agents")
def list_agents() -> None:
    """List available AI coding agents."""
    agent_dim = DIMENSIONS[1]
    for frag in list_available(agent_dim):
        click.echo(f"{frag['_id']:<20} {frag['_name']}")


@main.command()
@click.argument("path", default="templates")
def validate(path: str) -> None:
    """Validate generated templates.

    Checks against the official devcontainer schema and devcc rules.
    """
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
