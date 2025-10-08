from nova.system.mission import build_default_plan
from nova.system.roadmap import build_phase_roadmap
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
