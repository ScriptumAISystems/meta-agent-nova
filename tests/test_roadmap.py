from nova.system.mission import build_default_plan
from nova.system.roadmap import (
    build_global_step_plan,
    build_next_steps_summary,
    build_phase_roadmap,
)
from nova.system.tasks import AgentTask


def _sample_tasks() -> list[AgentTask]:
    return [
        AgentTask(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "System prüfen",
            "Offen",
        ),
        AgentTask(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "Backup einrichten",
            "Abgeschlossen",
        ),
        AgentTask(
            "orion",
            "Orion (KI-Software-Spezialist)",
            "KI-Software-Spezialist",
            "LLM vorbereiten",
            "In Arbeit",
        ),
    ]


def test_build_phase_roadmap_highlights_pending_steps():
    plan = build_default_plan()
    roadmap = build_phase_roadmap(_sample_tasks(), plan)

    assert "# Nova Phasen-Roadmap" in roadmap
    assert "## Foundation" in roadmap
    assert "*Fortschritt:* 1/2 (50%)" in roadmap
    assert "1. [ ] System prüfen (Status: Offen)" in roadmap
    assert "LLM vorbereiten" in roadmap


def test_build_phase_roadmap_handles_empty_phases():
    plan = build_default_plan()
    roadmap = build_phase_roadmap([], plan)

    assert "- Gesamtaufgaben: 0" in roadmap
    assert "Keine Phasen definiert." not in roadmap
    assert "*Hinweis:* Für diese Phase" in roadmap


def test_build_phase_roadmap_filters_to_requested_phase():
    plan = build_default_plan()
    roadmap = build_phase_roadmap(
        _sample_tasks(),
        plan,
        phase_filters=["model-operations"],
    )

    assert "## Foundation" not in roadmap
    assert "## Model-Operations" in roadmap
    assert "1. [ ] LLM vorbereiten (Status: In Arbeit)" in roadmap
    assert "*Gefiltert nach Phasen:* model-operations" in roadmap


def test_build_phase_roadmap_warns_on_unknown_phase():
    plan = build_default_plan()
    roadmap = build_phase_roadmap(
        _sample_tasks(),
        plan,
        phase_filters=["unbekannt"],
    )

    assert "Keine der angeforderten Phasen" in roadmap


def test_build_next_steps_summary_groups_by_phase_and_limit():
    plan = build_default_plan()
    tasks = [
        AgentTask("nova", "Nova (Chef-Agentin)", "Chef-Agentin", "System prüfen", "Offen"),
        AgentTask(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "Backup einrichten",
            "In Arbeit",
        ),
        AgentTask(
            "orion",
            "Orion (KI-Software-Spezialist)",
            "KI-Software-Spezialist",
            "LLM vorbereiten",
            "In Arbeit",
        ),
        AgentTask(
            "chronos",
            "Chronos (Workflow & Automation Specialist)",
            "Workflow & Automation Specialist",
            "n8n Workflows aufsetzen",
            "Offen",
        ),
        AgentTask(
            "zeus",
            "Zeus",
            None,
            "Sonstige Abstimmungen",
            "Offen",
        ),
        AgentTask(
            "echo",
            "Echo",
            "Avatar & Interaction Designer",
            "Avatar Demo",
            "Abgeschlossen",
        ),
    ]

    summary = build_next_steps_summary(tasks, plan, limit_per_agent=1)

    assert "# Nova Nächste Schritte" in summary
    assert "- Offene Aufgaben gesamt: 5" in summary
    assert "## Foundation" in summary and "System prüfen" in summary
    assert "- … 1 weitere Aufgabe" in summary
    assert "## Model-Operations" in summary
    assert "n8n Workflows aufsetzen" in summary
    assert "## Ad-Hoc" in summary
    assert "Zeus" in summary
    assert "Backup einrichten" not in summary


def test_build_next_steps_summary_reports_completion():
    plan = build_default_plan()
    tasks = [
        AgentTask(
            "nova",
            "Nova (Chef-Agentin)",
            "Chef-Agentin",
            "System prüfen",
            "Abgeschlossen",
        )
    ]

    summary = build_next_steps_summary(tasks, plan)

    assert summary.strip().endswith("Alle Aufgaben abgeschlossen. ✅")


def test_build_global_step_plan_includes_all_statuses():
    plan = build_default_plan()
    tasks = _sample_tasks()
    tasks.append(
        AgentTask("chronos", "Chronos", "Workflow", "n8n Workflows", "Offen")
    )
    tasks.append(AgentTask("zeus", "Zeus", None, "Abstimmung", "In Arbeit"))

    plan_markdown = build_global_step_plan(tasks, plan)

    assert "# Nova Schritt-für-Schritt Plan" in plan_markdown
    assert "- Gesamtaufgaben: 5" in plan_markdown
    assert "1. [ ] System prüfen (Status: Offen)" in plan_markdown
    assert "2. [x] Backup einrichten (Status: Abgeschlossen)" in plan_markdown
    assert "3. [ ] LLM vorbereiten (Status: In Arbeit)" in plan_markdown
    assert "Abstimmung" in plan_markdown


def test_build_global_step_plan_respects_phase_filters():
    plan = build_default_plan()
    plan_markdown = build_global_step_plan(
        _sample_tasks(),
        plan,
        phase_filters=["model-operations"],
    )

    assert "*Gefiltert nach Phasen:* model-operations" in plan_markdown
    assert "1. [ ] LLM vorbereiten (Status: In Arbeit)" in plan_markdown
    assert "System prüfen" not in plan_markdown
