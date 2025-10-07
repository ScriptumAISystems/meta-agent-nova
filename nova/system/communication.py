"""Lightweight communication primitives used by the Nova orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Iterable, Tuple


@dataclass(slots=True)
class AgentMessage:
    """Immutable representation of an inter-agent message."""

    sender: str
    recipients: Tuple[str, ...]
    subject: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "recipients": list(self.recipients),
            "subject": self.subject,
            "body": self.body,
            "metadata": dict(self.metadata),
        }


class CommunicationHub:
    """In-memory message bus that keeps a log of agent interactions."""

    def __init__(self) -> None:
        self._messages: list[AgentMessage] = []
        self._lock = RLock()

    @staticmethod
    def _normalise_recipients(recipients: Iterable[str] | None) -> Tuple[str, ...]:
        if not recipients:
            return ("orchestrator",)
        return tuple(recipient.strip().lower() for recipient in recipients if recipient.strip())

    def publish(self, message: AgentMessage) -> AgentMessage:
        """Store ``message`` in the log and return it."""

        with self._lock:
            self._messages.append(message)
        return message

    def send(
        self,
        *,
        sender: str,
        subject: str,
        body: str,
        recipients: Iterable[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentMessage:
        """Create a message and persist it in the communication log."""

        message = AgentMessage(
            sender=sender.lower(),
            recipients=self._normalise_recipients(recipients),
            subject=subject,
            body=body,
            metadata=dict(metadata or {}),
        )
        return self.publish(message)

    def broadcast(
        self,
        *,
        sender: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> AgentMessage:
        """Send a message to all recipients."""

        return self.send(
            sender=sender,
            subject=subject,
            body=body,
            recipients=("all",),
            metadata=metadata,
        )

    @property
    def messages(self) -> Tuple[AgentMessage, ...]:
        """Return the recorded messages as an immutable tuple."""

        with self._lock:
            return tuple(self._messages)

    def messages_for(self, recipient: str) -> list[AgentMessage]:
        """Return all messages addressed to ``recipient`` or broadcast to ``all``."""

        recipient_key = recipient.strip().lower()
        with self._lock:
            return [
                message
                for message in self._messages
                if "all" in message.recipients or recipient_key in message.recipients
            ]

    def latest(self) -> AgentMessage | None:
        """Return the newest message in the log if available."""

        with self._lock:
            if not self._messages:
                return None
            return self._messages[-1]

    def clear(self) -> None:
        """Remove all stored messages."""

        with self._lock:
            self._messages.clear()


__all__ = ["AgentMessage", "CommunicationHub"]

