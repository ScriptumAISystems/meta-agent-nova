from __future__ import annotations

from pathlib import Path

from nova.governance.integrity_check import (
    IntegrityCheckConfig,
    run_integrity_checks,
    write_reports,
)
from nova.governance.validators.policy_validator import PolicyValidator


def test_integrity_report_pass(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = repo_root / "config/governance/integrity_config.json"
    config = IntegrityCheckConfig.from_file(config_path)
    report = run_integrity_checks(config)

    assert report.overall_status == "PASS"
    assert len(report.results) == 3
    json_path, md_path = write_reports(report, tmp_path)
    assert json_path.exists()
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "Governance Integrity Report" in content
    assert "Overall Status" in content


def test_policy_validator_detects_missing_fields(tmp_path: Path) -> None:
    invalid_policy = tmp_path / "policy.json"
    invalid_policy.write_text("{}", encoding="utf-8")
    result = PolicyValidator(resource=str(invalid_policy)).validate()
    assert result.status == "FAIL"
    assert any("missing keys" in detail for detail in result.details)
