from nova.system.progress import build_progress_report
from nova.system.tasks import AgentTask


def _task(agent: str, display: str, role: str | None, description: str, status: str) -> AgentTask:
    return AgentTask(
        agent_identifier=agent,
        agent_display_name=display,
        agent_role=role,
        description=description,
        status=status,
    )


def test_progress_report_includes_summary_and_pending_tasks():
    tasks = [
        _task("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "System prüfen", "Offen"),
        _task(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "Backup validieren",
            "Abgeschlossen",
        ),
        _task(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "Dokumentation aktualisieren",
            "Offen",
        ),
        _task(
            "orion",
            "Orion (KI-Software-Spezialist)",
            "KI-Software-Spezialist",
            "LLM bereitstellen",
            "Abgeschlossen",
        ),
    ]

    report = build_progress_report(tasks, pending_limit=1)

    assert "# Nova Fortschrittsbericht" in report
    assert "- Gesamtaufgaben: 4" in report
    assert "- Fortschritt: 50%" in report
    assert "## Nova (Chef-Agentin)" in report
    assert "*Rolle:* Chef-Agentin" in report
    assert "- Aufgaben: 3" in report
    assert "- Fortschritt: 33%" in report
    assert "### Nächste Schritte" in report
    assert "- [ ] Dokumentation aktualisieren (Status: Offen)" in report
    assert "- … 1 weitere Aufgabe" in report
    assert "Alle Aufgaben abgeschlossen. ✅" in report


def test_progress_report_limit_zero_includes_all_pending():
    tasks = [
        _task("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "System prüfen", "Offen"),
        _task(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "Dokumentation aktualisieren",
            "Offen",
        ),
    ]

    report = build_progress_report(tasks, pending_limit=0)

    assert report.count("- [ ]") == 2
    assert "weitere Aufgabe" not in report


def test_progress_report_default_includes_all_pending():
    tasks = [
        _task("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "System prüfen", "Offen"),
        _task(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "Dokumentation aktualisieren",
            "Offen",
        ),
    ]

    report = build_progress_report(tasks)

    assert report.count("- [ ]") == 2
    assert "weitere Aufgabe" not in report


def test_progress_report_without_tasks_returns_placeholder():
    report = build_progress_report([], pending_limit=2)
    assert report == "# Nova Fortschrittsbericht\n\nKeine Aufgaben gefunden."

