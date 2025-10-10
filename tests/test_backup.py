from pathlib import Path

import pytest

from nova.system import backup


def test_build_backup_plan_default_contains_sections():
    plan = backup.build_backup_plan("default")

    assert plan.identifier == "default"
    markdown = plan.to_markdown()
    assert "# Default Backup & Recovery Plan" in markdown
    assert "## Backup-Jobs" in markdown
    assert any("pg_dump" in entry for entry in plan.backup_jobs)
    assert any("Restore-Test" in entry or "Restore" in entry for entry in plan.recovery_drills)


def test_build_backup_plan_rejects_unknown_plan():
    with pytest.raises(ValueError):
        backup.build_backup_plan("unknown")


def test_export_backup_plan(tmp_path: Path):
    plan = backup.build_backup_plan("default")
    output = tmp_path / "plan.md"

    result = backup.export_backup_plan(plan, output)

    assert result == output
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "Default Backup & Recovery Plan" in content
