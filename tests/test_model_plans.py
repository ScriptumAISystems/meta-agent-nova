from pathlib import Path

import pytest

from nova.models import plans


def test_build_model_plan_finetune_sections():
    plan = plans.build_model_plan("finetune")
    markdown = plan.to_markdown()

    assert plan.identifier == "finetune"
    assert "# Sophia Finetuning Playbook" in markdown
    assert "## Ziele & Erfolgskriterien" in markdown
    assert "LoRA/PEFT-Konfiguration" in markdown
    assert "Human-in-the-loop Review-Panel" in markdown
    assert "Runbook für Deployment" in markdown


def test_build_model_plan_unknown():
    with pytest.raises(ValueError):
        plans.build_model_plan("unknown")


def test_export_model_plan(tmp_path: Path):
    plan = plans.build_model_plan("finetune")
    destination = tmp_path / "finetune_plan.md"

    written_path = plans.export_model_plan(plan, destination)

    assert written_path == destination
    content = written_path.read_text(encoding="utf-8")
    assert content.startswith("# Sophia Finetuning Playbook")
    assert content.rstrip().endswith("Lessons Learned & nächste Iterationen in `progress_report.md` bzw. Nova CLI (`python -m nova summary`) spiegeln.")
