import os

from nova.system.communication import CommunicationHub
from nova.system.orchestrator import Orchestrator


def test_orchestrator_executes_all_agents(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    hub = CommunicationHub()
    orchestrator = Orchestrator(communication_hub=hub)
    report = orchestrator.execute()
    assert report.success
    assert report.agent_reports
    assert {r.agent_type for r in report.agent_reports} == set(orchestrator.agent_types)
    for agent_report in report.agent_reports:
        for task_report in agent_report.task_reports:
            assert task_report.status == "completed"
            assert task_report.details
            assert any(detail.startswith("message-sent:") for detail in task_report.details)
    assert report.communication_log
    assert all(message.subject.startswith("task-completed::") or message.subject.startswith("agent-run::") for message in report.communication_log)
    markdown = report.to_markdown()
    assert markdown.startswith("# Orchestration Report")
    assert "## Communication Log" in markdown
