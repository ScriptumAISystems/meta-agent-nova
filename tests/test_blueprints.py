from nova.blueprints.generator import create_blueprint, list_blueprints


def test_blueprint_contains_tasks():
    available = list_blueprints()
    assert {"aura", "chronos", "echo", "orion"}.issubset(set(available))

    blueprint = create_blueprint("aura")
    assert blueprint.agent_type == "aura"
    assert blueprint.tasks, "Blueprint should define tasks"
    first_task = blueprint.tasks[0]
    assert first_task.name == "install-grafana"
    assert first_task.steps
