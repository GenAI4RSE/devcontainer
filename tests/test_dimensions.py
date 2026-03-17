"""Tests for dimension config and data loading."""

import pytest

from devcc.dimensions import (
    DIMENSIONS,
    get_data_path,
    list_available,
    load_dimension_fragment,
    load_fragment,
)


class TestDimensionConfig:
    def test_languages_dimension_exists(self) -> None:
        langs = [d for d in DIMENSIONS if d.name == "languages"]
        assert len(langs) == 1
        assert langs[0].required is True
        assert langs[0].multi is True

    def test_agents_dimension_exists(self) -> None:
        agents = [d for d in DIMENSIONS if d.name == "agents"]
        assert len(agents) == 1
        assert agents[0].required is False
        assert agents[0].multi is True


class TestDataLoading:
    def test_get_data_path_exists(self) -> None:
        path = get_data_path()
        assert path.exists()
        assert (path / "base" / "base.json").exists()

    def test_load_fragment_base(self) -> None:
        path = get_data_path() / "base" / "base.json"
        frag = load_fragment(path)
        assert frag["image"] == "ubuntu:24.04"
        assert "features" in frag

    def test_load_dimension_fragment_python(self) -> None:
        lang_dim = DIMENSIONS[0]
        frag = load_dimension_fragment(lang_dim, "python")
        assert frag["_id"] == "python"
        assert frag["_name"] == "Python"
        assert "features" in frag

    def test_load_dimension_fragment_unknown_raises(self) -> None:
        lang_dim = DIMENSIONS[0]
        with pytest.raises(ValueError, match="Unknown languages ID: nonexistent"):
            load_dimension_fragment(lang_dim, "nonexistent")

    def test_list_available_languages(self) -> None:
        lang_dim = DIMENSIONS[0]
        langs = list_available(lang_dim)
        assert len(langs) == 6
        ids = {f["_id"] for f in langs}
        assert ids == {"python", "node", "rust", "r", "julia", "c-cpp-fortran"}

    def test_list_available_agents(self) -> None:
        agent_dim = DIMENSIONS[1]
        agents = list_available(agent_dim)
        assert len(agents) == 5
        ids = {f["_id"] for f in agents}
        assert ids == {"claude-code", "codex", "copilot", "gemini", "cursor"}
