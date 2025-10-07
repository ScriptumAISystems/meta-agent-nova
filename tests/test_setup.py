from pathlib import Path

from nova.system import setup


def test_prepare_environment_creates_structure(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    report = setup.prepare_environment()
    assert report.root == Path(tmp_path)
    assert (Path(tmp_path) / "configs" / "settings.json").exists()
    assert report.created_paths


def test_install_packages_filters_duplicates(monkeypatch):
    monkeypatch.setenv("NOVA_HOME", "unused")
    report = setup.install_packages(["Docker", "docker", "kubernetes"], dry_run=True)
    assert report.requested == ["Docker", "kubernetes"]
    assert "docker" in report.skipped
    assert report.dry_run is True


def test_configure_os_merges_settings():
    custom = setup.configure_os({"timezone": "Europe/Berlin"})
    assert custom.settings["timezone"] == "Europe/Berlin"
    assert "file_descriptor_limit" in custom.settings
