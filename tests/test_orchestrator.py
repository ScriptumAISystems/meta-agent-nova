import os

from nova.system.orchestrator import Orchestrator


def test_orchestrator_executes_all_agents(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_HOME", str(tmp_path))
    orchestrator = Orchestrator()
    report = orchestrator.execute()
    assert report.success
    assert report.agent_reports
    assert {r.agent_type for r in report.agent_reports} == set(orchestrator.agent_types)
    for agent_report in report.agent_reports:
        for task_report in agent_report.task_reports:
            assert task_report.status == "completed"
            assert task_report.details
