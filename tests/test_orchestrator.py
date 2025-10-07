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
        assert agent_report.pre_run_messages
        for task_report in agent_report.task_reports:
            assert task_report.status == "completed"
            assert task_report.details
            assert any(detail.startswith("message-sent:") for detail in task_report.details)
    subjects = [message.subject for message in report.communication_log]
    assert "orchestration-start" in subjects
    for agent in orchestrator.agent_types:
        assert f"agent-start::{agent}" in subjects
        assert f"agent-run::{agent}" in subjects
    assert all(
        subject.startswith("task-completed::")
        or subject.startswith("agent-run::")
        or subject == "orchestration-start"
        or subject.startswith("agent-start::")
        for subject in subjects
    )
    markdown = report.to_markdown()
    assert markdown.startswith("# Orchestration Report")
    assert "## Communication Log" in markdown
    assert "Execution mode" in markdown


def test_orchestrator_parallel_execution(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    hub = CommunicationHub()
    orchestrator = Orchestrator(communication_hub=hub, execution_mode="parallel")
    report = orchestrator.execute()
    assert report.success
    assert report.execution_mode == "parallel"
    assert {r.agent_type for r in report.agent_reports} == set(orchestrator.agent_types)
