from nova.containers.container_manager import deploy_dgx, status


def test_deploy_dgx_produces_markdown() -> None:
    report = deploy_dgx()
    assert report.builds
    assert report.deployments
    markdown = report.to_markdown()
    assert "# DGX Container Deployment" in markdown


def test_container_status_entries() -> None:
    results = status()
    assert results
    for entry in results:
        assert entry.name
        assert entry.status in {"running", "stopped"}
        assert entry.details
