"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Temporary output directory for generated templates."""
    out = tmp_path / "output"
    out.mkdir()
    return out
