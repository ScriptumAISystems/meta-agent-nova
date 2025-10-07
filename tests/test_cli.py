import pytest

from nova import __main__


@pytest.mark.parametrize(
    "argv",
    [
        ["blueprints"],
        ["monitor"],
    ],
)
def test_cli_commands(argv):
    __main__.main(argv)


def test_cli_setup_and_orchestrate(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    __main__.main(["setup", "--packages", "docker", "kubernetes"])
    assert (tmp_path / "configs" / "settings.json").exists()

    __main__.main(["orchestrate"])
    report_path = tmp_path / "reports" / "nova-test-report.md"
    assert report_path.exists()
    assert report_path.read_text().startswith("# Nova Integration Test Report")


def test_cli_audit(monkeypatch):
    warnings: list[str] = []
    infos: list[str] = []
    monkeypatch.setattr(__main__, "notify_warning", lambda message: warnings.append(message))
    monkeypatch.setattr(__main__, "notify_info", lambda message: infos.append(message))
    __main__.main(["audit", "--firewall", "enabled", "--antivirus", "enabled", "--policies", "disabled"])
    assert warnings, "audit should raise warnings when a control is disabled"
    assert not infos, "audit should not report success when warnings are issued"


def test_cli_orchestrate_parallel(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    monkeypatch.setenv("NOVA_EXECUTION_MODE", "parallel")
    __main__.main(["orchestrate"])
    assert (tmp_path / "reports" / "nova-test-report.md").exists()
