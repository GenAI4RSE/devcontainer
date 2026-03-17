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
