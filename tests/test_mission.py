from nova.system.mission import ExecutionPlan, ExecutionPhase, build_default_plan


def test_default_plan_orders_agents():
    plan = build_default_plan()
    filtered = plan.filtered(["nova", "orion", "lumina", "chronos", "echo", "aura"])
    assert filtered.phases
    assert filtered.iter_agents() == (
        "nova",
        "orion",
        "chronos",
        "lumina",
        "echo",
        "aura",
    )
    assert filtered.dependencies_for("chronos") == ("nova", "orion")


def test_plan_retains_unknown_agents():
    plan = ExecutionPlan((ExecutionPhase(name="custom", goal="", agents=("alpha",)),))
    filtered = plan.filtered(["alpha", "beta"])
    assert filtered.iter_agents() == ("alpha", "beta")
    assert filtered.dependencies_for("beta") == ("alpha",)
