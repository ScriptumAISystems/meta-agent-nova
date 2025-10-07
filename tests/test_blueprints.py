from nova.blueprints.generator import create_blueprint, list_blueprints


def test_blueprint_contains_tasks():
    available = list_blueprints()
    assert {"aura", "chronos", "echo", "lumina", "nova", "orion"}.issubset(
        set(available)
    )

    blueprint = create_blueprint("aura")
    assert blueprint.agent_type == "aura"
    assert blueprint.tasks, "Blueprint should define tasks"
    first_task = blueprint.tasks[0]
    assert first_task.name == "install-grafana"
    assert first_task.steps

    nova_blueprint = create_blueprint("nova")
    assert len(nova_blueprint.tasks) == 5
    assert nova_blueprint.tasks[0].name == "infrastructure-audit"

    lumina_blueprint = create_blueprint("lumina")
    assert {task.name for task in lumina_blueprint.tasks} == {
        "relational-databases",
        "vector-knowledge-base",
    }

    orion_tasks = {task.name for task in create_blueprint("orion").tasks}
    assert {"nemo-installation", "finetuning-protocol", "llm-selection", "langchain-integration"}.issubset(orion_tasks)

    chronos_tasks = {task.name for task in create_blueprint("chronos").tasks}
    assert {
        "bootstrap-n8n",
        "continuous-delivery",
        "agent-pipelines",
        "data-flywheel",
    }.issubset(chronos_tasks)

    aura_tasks = {task.name for task in create_blueprint("aura").tasks}
    assert {
        "install-grafana",
        "lux-dashboard",
        "efficiency-optimisation",
        "emotional-feedback-visualisation",
    }.issubset(aura_tasks)

    echo_tasks = {task.name for task in create_blueprint("echo").tasks}
    assert {"ace-toolkit-setup", "avatar-pipeline", "teams-integration"}.issubset(echo_tasks)
