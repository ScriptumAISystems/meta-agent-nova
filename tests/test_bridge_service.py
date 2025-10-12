import hashlib
import hmac
import json
from typing import Any, Mapping

import pytest
from fastapi.testclient import TestClient

from nova.automation import (
    BridgeForwardingError,
    BridgeSettings,
    WorkflowResult,
    create_bridge_app,
)


def _signed_body(payload: Mapping[str, Any], secret: str) -> tuple[bytes, str]:
    body = json.dumps(payload).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, digest


class StubForwarder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    async def forward(self, workflow: str, payload: Mapping[str, Any]) -> WorkflowResult:
        self.calls.append((workflow, payload))
        return WorkflowResult(status_code=202, detail="accepted", response_body={"ok": True})


class FailingForwarder:
    def __init__(self, message: str) -> None:
        self.message = message

    async def forward(self, workflow: str, payload: Mapping[str, Any]) -> WorkflowResult:  # type: ignore[override]
        raise BridgeForwardingError(self.message)


@pytest.fixture()
def settings() -> BridgeSettings:
    return BridgeSettings(
        n8n_base_url="http://n8n:5678/webhook",
        auth_user="admin",
        auth_password="change_me",
        shared_secret="super-secret",
    )


def test_summary_refresh_forwards_payload(settings: BridgeSettings) -> None:
    forwarder = StubForwarder()
    app = create_bridge_app(settings=settings, forwarder=forwarder)
    client = TestClient(app)

    payload = {"context": {"source": "unit-test"}}
    body, signature = _signed_body(payload, settings.shared_secret)
    response = client.post(
        "/workflows/summary-refresh",
        data=body,
        headers={"x-nova-signature": signature},
    )

    assert response.status_code == 200
    assert response.json()["workflow"] == "summary-refresh"
    assert forwarder.calls == [("summary-refresh", payload)]


def test_missing_signature_rejected(settings: BridgeSettings) -> None:
    app = create_bridge_app(settings=settings, forwarder=StubForwarder())
    client = TestClient(app)

    response = client.post("/workflows/summary-refresh", json={})
    assert response.status_code == 401
    assert "Missing signature" in response.text


def test_invalid_signature_rejected(settings: BridgeSettings) -> None:
    app = create_bridge_app(settings=settings, forwarder=StubForwarder())
    client = TestClient(app)

    response = client.post(
        "/workflows/summary-refresh",
        json={},
        headers={"x-nova-signature": "invalid"},
    )
    assert response.status_code == 401
    assert "Invalid signature" in response.text


def test_finetune_status_forwarded(settings: BridgeSettings) -> None:
    forwarder = StubForwarder()
    app = create_bridge_app(settings=settings, forwarder=forwarder)
    client = TestClient(app)

    payload = {
        "run_id": "sophia-finetune-dev",
        "stage": "evaluation",
        "metrics": {"bleu": 36.4, "rouge_l": 0.41, "win_rate": 0.67},
    }
    body, signature = _signed_body(payload, settings.shared_secret)
    response = client.post(
        "/workflows/finetune-status",
        data=body,
        headers={"x-nova-signature": signature},
    )

    assert response.status_code == 200
    assert response.json()["workflow"] == "finetune-status"
    assert forwarder.calls == [("finetune-status", payload)]


def test_forwarder_failure_returns_502(settings: BridgeSettings) -> None:
    app = create_bridge_app(settings=settings, forwarder=FailingForwarder("boom"))
    client = TestClient(app)

    payload = {"context": {}}
    body, signature = _signed_body(payload, settings.shared_secret)
    response = client.post(
        "/workflows/summary-refresh",
        data=body,
        headers={"x-nova-signature": signature},
    )

    assert response.status_code == 502
    assert "boom" in response.text
