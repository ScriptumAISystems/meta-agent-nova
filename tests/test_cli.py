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


def test_cli_orchestrate_parallel(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    monkeypatch.setenv("NOVA_EXECUTION_MODE", "parallel")
    __main__.main(["orchestrate"])
    assert (tmp_path / "reports" / "nova-test-report.md").exists()
