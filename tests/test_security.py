import pytest

from nova.system.security import run_security_audit


def test_security_audit_all_controls_pass():
    report = run_security_audit(
        firewall_enabled=True,
        antivirus_enabled=True,
        policies_enforced=True,
    )
    assert report.passed is True
    data = report.to_dict()
    assert data["passed"] is True
    assert all(control["status"] == "ok" for control in data["controls"])
    markdown = report.to_markdown()
    assert "Security Audit Report" in markdown
    assert "No outstanding findings" in markdown


def test_security_audit_collects_findings(monkeypatch):
    monkeypatch.delenv("NOVA_FIREWALL_ENABLED", raising=False)
    report = run_security_audit(
        firewall_enabled=False,
        antivirus_enabled=None,
        policies_enforced=None,
        extra_findings=("OPA drift detected",),
    )
    assert report.passed is False
    assert "Firewall" in report.findings[0]
    assert any("OPA drift" in finding for finding in report.findings)
    details = report.to_dict()
    assert details["passed"] is False
    assert any(control["status"] != "ok" for control in details["controls"])
