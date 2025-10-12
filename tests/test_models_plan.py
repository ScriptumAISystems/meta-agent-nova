from pathlib import Path

from nova.models import plans


def test_list_available_model_plans_contains_finetune():
    assert "finetune" in plans.list_available_model_plans()


def test_build_model_plan_returns_markdown():
    plan = plans.build_model_plan("finetune")

    markdown = plan.to_markdown()

    assert plan.identifier == "finetune"
    assert "# Finetuning-Plan für Sophia LLM" in markdown
    assert "## Datenvorbereitung" in markdown
    assert "## Automatisierung & Monitoring" in markdown


def test_export_model_plan_writes_file(tmp_path: Path):
    plan = plans.build_model_plan("finetune")
    output = tmp_path / "plan.md"

    result = plans.export_model_plan(plan, output)

    assert result == output.resolve()
    content = output.read_text(encoding="utf-8")
    assert "# Finetuning-Plan für Sophia LLM" in content
