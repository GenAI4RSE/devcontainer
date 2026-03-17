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
