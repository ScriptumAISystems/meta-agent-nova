from nova.blueprints.generator import create_blueprint
from nova.system.communication import CommunicationHub
from nova.agents.nova import NovaAgent


def test_communication_hub_records_messages():
    hub = CommunicationHub()
    hub.send(sender="nova", subject="hello", body="world", recipients=("lumina",))
    hub.broadcast(sender="orchestrator", subject="update", body="all good")
    assert len(hub.messages) == 2
    assert hub.messages_for("lumina")
    assert hub.messages_for("orion")  # broadcast delivered to everyone
    latest = hub.latest()
    assert latest is not None
    assert latest.subject == "update"


def test_agent_emits_messages_on_task_completion():
    blueprint = create_blueprint("nova")
    hub = CommunicationHub()
    agent = NovaAgent(blueprint, communication_hub=hub)
    report = agent.execute()
    assert report.success
    assert hub.messages
    subjects = {message.subject for message in hub.messages}
    assert any(subject.startswith("task-completed::") for subject in subjects)
