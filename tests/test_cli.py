import pytest

from nova import __main__
from nova.system import containers as container_utils


@pytest.mark.parametrize(
    "argv",
    [
        ["blueprints"],
        ["monitor"],
        ["next-steps"],
        ["step-plan"],
        ["progress"],
        ["summary"],
    ],
)
def test_cli_commands(argv):
    __main__.main(argv)


def test_cli_setup_and_orchestrate(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    __main__.main(["setup", "--packages", "docker", "kubernetes"])
    assert (tmp_path / "configs" / "settings.json").exists()

    __main__.main(["orchestrate"])
    report_path = tmp_path / "reports" / "nova-test-report.md"
    assert report_path.exists()
    assert report_path.read_text().startswith("# Nova Integration Test Report")


def test_cli_audit(monkeypatch):
    warnings: list[str] = []
    infos: list[str] = []
    monkeypatch.setattr(__main__, "notify_warning", lambda message: warnings.append(message))
    monkeypatch.setattr(__main__, "notify_info", lambda message: infos.append(message))
    __main__.main(["audit", "--firewall", "enabled", "--antivirus", "enabled", "--policies", "disabled"])
    assert warnings, "audit should raise warnings when a control is disabled"
    assert not infos, "audit should not report success when warnings are issued"


def test_cli_containers_command(monkeypatch):
    report = container_utils.ContainerInspectionReport(
        [
            container_utils.RuntimeCheckResult(
                name="Docker Engine",
                binary="docker",
                found=True,
                version="Docker version 26.0.0",
                health="ok",
                notes=[],
            )
        ]
    )
    captured: list[container_utils.ContainerInspectionReport] = []
    monkeypatch.setattr(__main__, "inspect_container_runtimes", lambda kubeconfig=None: report)
    monkeypatch.setattr(__main__, "log_container_report", lambda rep: captured.append(rep))

    __main__.main(["containers"])

    assert captured == [report]


def test_cli_containers_fix_plan(monkeypatch, caplog):
    report = container_utils.ContainerInspectionReport(
        [
            container_utils.RuntimeCheckResult(
                name="Docker Engine",
                binary="docker",
                found=False,
                version=None,
                health="missing",
                notes=["Binary 'docker' wurde nicht im PATH gefunden."],
            )
        ]
    )

    monkeypatch.setattr(__main__, "inspect_container_runtimes", lambda kubeconfig=None: report)
    monkeypatch.setattr(__main__, "log_container_report", lambda rep: None)
    monkeypatch.setattr(
        __main__,
        "build_container_fix_plan",
        lambda rep: "# Fix\n\nProblem\nLösung",
    )

    caplog.set_level("INFO", logger="nova.monitoring")

    __main__.main(["containers", "--fix"])

    assert "Fix" in caplog.text
    assert "Problem" in caplog.text
    assert "Lösung" in caplog.text


def test_cli_orchestrate_parallel(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    monkeypatch.setenv("NOVA_EXECUTION_MODE", "parallel")
    __main__.main(["orchestrate"])
    assert (tmp_path / "reports" / "nova-test-report.md").exists()


def test_cli_tasks_command(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,In Arbeit\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["tasks", "--status", "offen"])

    assert "Loading agent tasks from" in caplog.text
    assert "Total tasks: 1" in caplog.text
    assert "## Nova (Chef-Agentin)" in caplog.text


def test_cli_tasks_checklist(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),Backup,Abgeschlossen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["tasks", "--checklist"])

    assert "Nova Agent Task Checklist" in caplog.text
    assert "1. [x] Backup (Status: Abgeschlossen)" in caplog.text
    assert "2. [ ] LLM vorbereiten (Status: Offen)" in caplog.text


def test_cli_roadmap_command(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["roadmap"])

    assert "Nova Phasen-Roadmap" in caplog.text
    assert "System prüfen" in caplog.text


def test_cli_roadmap_with_phase_filter(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Aura (Monitoring & Dashboard-Entwicklerin),Grafana installieren,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["roadmap", "--phase", "observability"])

    assert "*Gefiltert nach Phasen:* observability" in caplog.text
    assert "## Observability" in caplog.text
    assert "Grafana installieren" in caplog.text
    assert "## Foundation" not in caplog.text


def test_cli_next_steps_command(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Nova (Chef-Agentin),Backup,In Arbeit\n"
        "Chronos (Workflow & Automation Specialist),n8n Workflows,Offen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,Abgeschlossen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["next-steps", "--limit", "1"])

    assert "Nova Nächste Schritte" in caplog.text
    assert "System prüfen" in caplog.text
    assert "… 1 weitere Aufgabe" in caplog.text
    assert "n8n Workflows" in caplog.text


def test_cli_step_plan_command(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Nova (Chef-Agentin),Backup,Abgeschlossen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,In Arbeit\n"
        "Zeus,Abstimmung,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["step-plan"])

    assert "Nova Schritt-für-Schritt Plan" in caplog.text
    assert "1. [ ] System prüfen (Status: Offen)" in caplog.text
    assert "2. [x] Backup (Status: Abgeschlossen)" in caplog.text
    assert "LLM vorbereiten" in caplog.text
    assert "Abstimmung" in caplog.text


def test_cli_progress_command(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Nova (Chef-Agentin),Backup,Abgeschlossen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,Offen\n"
        "Orion (KI-Software-Spezialist),Feintuning planen,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["progress", "--limit", "1"])

    assert "Nova Fortschrittsbericht" in caplog.text


def test_cli_summary_command(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Nova (Chef-Agentin),Backup,Abgeschlossen\n"
        "Chronos (Workflow & Automatisierungsspezialist),n8n Workflows,Offen\n"
        "Zeus,Abstimmung,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["summary", "--limit", "1"])

    assert "Nova Roadmap Snapshot" in caplog.text
    assert "## Foundation" in caplog.text
    assert "System prüfen" in caplog.text
    assert "## Ad-Hoc" in caplog.text
    assert "Abstimmung" in caplog.text
    assert "- Gesamtaufgaben: 4" in caplog.text
    assert "### Offene Schritte" in caplog.text


def test_cli_progress_default_shows_all_tasks(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Nova (Chef-Agentin),Backup,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["progress"])

    assert caplog.text.count("- [ ]") == 2
    assert "weitere Aufgabe" not in caplog.text


def test_cli_progress_with_agent_filter(tmp_path, monkeypatch, caplog):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text(
        "Agenten-Name,Aufgabe,Status\n"
        "Nova (Chef-Agentin),System prüfen,Offen\n"
        "Nova (Chef-Agentin),Backup,Abgeschlossen\n"
        "Orion (KI-Software-Spezialist),LLM vorbereiten,Offen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVA_TASK_CSV", str(csv_path))

    caplog.set_level("INFO", logger="nova.monitoring")
    __main__.main(["progress", "--agent", "nova"])

    assert "Loading agent tasks from" in caplog.text
    assert "- Gesamtaufgaben: 2" in caplog.text
    assert "## Nova (Chef-Agentin)" in caplog.text
    assert "## Orion" not in caplog.text
