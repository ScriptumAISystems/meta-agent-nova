from lumina import (
    DeploymentPlan,
    InstallationStep,
    install_mongodb,
    install_postgresql,
    setup_vector_db,
)


def _assert_plan(plan: DeploymentPlan, expected_service: str) -> None:
    assert isinstance(plan, DeploymentPlan)
    assert plan.service == expected_service
    assert plan.steps
    assert all(isinstance(step, InstallationStep) for step in plan.steps)
    assert plan.configuration
    assert plan.verification
    exported = plan.to_dict()
    assert exported["service"] == expected_service
    assert exported["steps"]
    assert exported["configuration"]
    assert exported["verification"]


def test_install_mongodb_plan():
    plan = install_mongodb()
    _assert_plan(plan, "mongodb")
    commands = [step.command for step in plan.steps]
    assert "sudo apt-get install -y mongodb-org" in commands


def test_install_postgresql_plan():
    plan = install_postgresql()
    _assert_plan(plan, "postgresql")
    commands = [step.command for step in plan.steps]
    assert "sudo systemctl enable --now postgresql" in commands


def test_setup_vector_db_pinecone():
    plan = setup_vector_db("pinecone")
    _assert_plan(plan, "pinecone")
    assert any("pinecone configure" in step.command for step in plan.steps)


def test_setup_vector_db_faiss():
    plan = setup_vector_db("faiss")
    _assert_plan(plan, "faiss")
    assert any(step.command == "pip install faiss-cpu" for step in plan.steps)


def test_setup_vector_db_invalid():
    try:
        setup_vector_db("unknown")
    except ValueError as exc:
        assert "Unsupported vector database type" in str(exc)
    else:  # pragma: no cover - defensive, should not execute
        assert False, "Expected ValueError"
