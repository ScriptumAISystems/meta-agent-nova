from pathlib import Path

from nova.system.dgx_audit import run_dgx_audit


def test_run_dgx_audit_creates_report(tmp_path: Path) -> None:
    result = run_dgx_audit(base_path=tmp_path)
    assert result.report_path.exists()
    assert result.log_path.exists()
    content = result.report_path.read_text(encoding="utf-8")
    assert "DGX Audit Report" in content
    assert any(check.status in {"ok", "warning", "error"} for check in result.checks)
