from nova.system import containers


class DummyCompleted:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_check_container_runtime_missing_binary(monkeypatch):
    monkeypatch.setattr(containers.shutil, "which", lambda _: None)
    result = containers.check_container_runtime("Docker Engine", "docker")
    assert result.health == "missing"
    assert not result.found
    assert any("nicht im PATH" in note for note in result.notes)


def test_check_container_runtime_with_version(monkeypatch):
    monkeypatch.setattr(containers.shutil, "which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr(
        containers.subprocess,
        "run",
        lambda *_, **__: DummyCompleted(stdout="Docker version 26.0.0"),
    )
    result = containers.check_container_runtime("Docker Engine", "docker")
    assert result.health == "ok"
    assert result.version == "Docker version 26.0.0"


def test_check_container_runtime_kubeconfig_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(containers.shutil, "which", lambda _: "/usr/bin/kubectl")
    monkeypatch.setattr(
        containers.subprocess,
        "run",
        lambda *_, **__: DummyCompleted(stdout="kubectl version v1.30.0", returncode=0),
    )
    kubeconfig = tmp_path / "config"
    result = containers.check_container_runtime(
        "Kubernetes CLI",
        "kubectl",
        version_args=("version", "--client", "--short"),
        config_paths=[kubeconfig],
    )
    assert result.health == "warning"
    assert result.config_ok is False
    assert any("Keine Kubeconfig" in note for note in result.notes)


def test_inspect_container_runtimes_aggregates(monkeypatch):
    results = iter(
        [
            containers.RuntimeCheckResult(
                name="Docker Engine",
                binary="docker",
                found=True,
                version="Docker version 26.0.0",
                health="ok",
                notes=[],
            ),
            containers.RuntimeCheckResult(
                name="Kubernetes CLI",
                binary="kubectl",
                found=True,
                version="kubectl version",
                health="warning",
                notes=["Keine Kubeconfig-Dateien gefunden."],
                config_ok=False,
            ),
        ]
    )
    monkeypatch.setattr(containers, "check_container_runtime", lambda *args, **kwargs: next(results))
    report = containers.inspect_container_runtimes()
    assert not report.all_healthy()
    markdown = report.to_markdown()
    assert "# Nova Container Runtime Check" in markdown
    assert "## Docker Engine" in markdown
    assert "⚠️" in markdown or "warning" in markdown
