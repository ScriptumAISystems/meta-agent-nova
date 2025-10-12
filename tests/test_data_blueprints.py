"""Tests for the data blueprint utilities."""

from pathlib import Path

import pytest

from nova.data.blueprints import (
    build_data_blueprint,
    export_data_blueprint,
    list_available_data_blueprints,
)


def test_list_available_data_blueprints_includes_core():
    available = list_available_data_blueprints()
    assert "core" in available


def test_build_core_blueprint_contains_expected_sections():
    blueprint = build_data_blueprint("core")
    markdown = blueprint.to_markdown()
    assert "# Sophia Data Core Blueprint" in markdown
    assert "MongoDB Cluster (Ops Ready)" in markdown
    assert "Pinecone (Managed Option)" in markdown
    assert "`pip install faiss-cpu`" in markdown


def test_export_data_blueprint(tmp_path: Path):
    blueprint = build_data_blueprint("core")
    output = tmp_path / "core_blueprint.md"
    destination = export_data_blueprint(blueprint, output)
    assert destination == output
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert content.startswith("# Sophia Data Core Blueprint")


def test_build_data_blueprint_invalid():
    with pytest.raises(ValueError) as exc:
        build_data_blueprint("unknown")
    assert "Unsupported data blueprint" in str(exc.value)
