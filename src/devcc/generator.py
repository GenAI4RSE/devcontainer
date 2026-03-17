"""Generator: merge fragments and produce devcontainer templates."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any

from devcc.dimensions import (
    DIMENSIONS,
    get_data_path,
    list_available,
    load_dimension_fragment,
    load_fragment,
)

NODE_FEATURE_KEY = "ghcr.io/devcontainers/features/node:1"
APT_FEATURE_KEY = "ghcr.io/devcontainers-extra/features/apt-get-packages:1"


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

    # 2. Agent install commands -> postCreateCommand
    for frag in agent_fragments:
        result.setdefault("postCreateCommand", {})[frag["_id"]] = frag["_install_command"]

    # 3. Agent config dirs -> mounts + containerEnv
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
