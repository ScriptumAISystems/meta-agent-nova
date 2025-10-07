from nova.system.communication import CommunicationHub
from nova.system.orchestrator import Orchestrator
from nova.monitoring.reports import (
    build_markdown_test_report,
    extract_failed_tasks,
    summarise_agent_metrics,
)


def test_build_markdown_test_report(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    hub = CommunicationHub()
    orchestrator = Orchestrator(communication_hub=hub)
    report = orchestrator.execute()

    markdown = build_markdown_test_report(report, title="Daily Nova Report")
    assert markdown.startswith("# Daily Nova Report")
    assert "Overall status" in markdown
    assert "## Agent Outcomes" in markdown
    assert "## Communication Summary" in markdown

    failures = extract_failed_tasks(report)
    assert failures == []

    metrics = summarise_agent_metrics(report)
    assert metrics
    assert set(metrics.keys()) == set(orchestrator.agent_types)
