import pytest

from nova.system import tasks


def test_resolve_task_csv_path_env_override(monkeypatch, tmp_path):
    csv_path = tmp_path / "tasks.csv"
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))
    resolved = tasks.resolve_task_csv_path()
    assert resolved == csv_path


def test_load_agent_tasks_reads_rows(tmp_path):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,In Arbeit\n",
        encoding="utf-8",
    )

    loaded = tasks.load_agent_tasks(csv_path)
    assert len(loaded) == 2
    assert loaded[0].agent_identifier == "nova"
    assert loaded[1].status == "In Arbeit"


def test_filter_tasks_by_agent_and_status():
    entries = [
        tasks.AgentTask("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "Audit", "Offen"),
        tasks.AgentTask("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "Backup", "Abgeschlossen"),
        tasks.AgentTask("orion", "Orion (KI-Software-Spezialist)", "KI-Software-Spezialist", "LLM", "Offen"),
    ]

    filtered = tasks.filter_tasks(entries, ["Nova"], "offen")
    assert len(filtered) == 1
    assert filtered[0].description == "Audit"


def test_group_and_markdown_summary():
    entries = [
        tasks.AgentTask("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "Audit", "Offen"),
        tasks.AgentTask("orion", "Orion (KI-Software-Spezialist)", "KI-Software-Spezialist", "LLM", "In Arbeit"),
    ]

    grouped = tasks.group_tasks_by_agent(entries)
    assert set(grouped) == {"Nova (Chef-Agentin)", "Orion (KI-Software-Spezialist)"}

    markdown = tasks.build_markdown_task_overview(entries)
    assert "# Nova Agent Task Overview" in markdown
    assert "## Nova (Chef-Agentin)" in markdown
    assert "- [Offen] Audit" in markdown


def test_build_markdown_with_empty_tasks():
    assert tasks.build_markdown_task_overview([]).endswith("Keine Aufgaben gefunden.")


def test_load_agent_tasks_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        tasks.load_agent_tasks(tmp_path / "missing.csv")
