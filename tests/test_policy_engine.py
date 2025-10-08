"""Unit tests for the OPA policy engine integration."""
from __future__ import annotations

import json
import threading
import urllib.error
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Generator, Tuple, Type

import pytest

from nova.policy import PolicyEngine, PolicyEngineUnavailable


class _MockOPAHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length))
        subject = payload["input"]["subject"]
        if subject == "admin":
            result = {"allow": True, "reason": "administrator"}
        else:
            result = {"allow": False, "reason": "forbidden"}
        body = json.dumps({"result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args, **kwargs):  # noqa: D401,N802
        """Silence default HTTP server logging."""
        return


class _CountingOPAHandler(_MockOPAHandler):
    call_count = 0

    def do_POST(self) -> None:  # noqa: N802
        type(self).call_count += 1
        super().do_POST()


@contextmanager
def _run_mock_opa(handler: Type[_MockOPAHandler]) -> Generator[Tuple[HTTPServer, threading.Thread], None, None]:
    server = HTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, thread
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _engine_for(server: HTTPServer) -> PolicyEngine:
    return PolicyEngine(opa_url=f"http://localhost:{server.server_address[1]}", policy_path="/")


def test_policy_engine_authorizes_admin() -> None:
    with _run_mock_opa(_MockOPAHandler) as (server, _):
        engine = _engine_for(server)
        decision = engine.authorize(subject="admin", action="write", resource="queue")
        assert decision.allow is True
        assert "admin" in decision.reason


def test_policy_engine_denies_default_user() -> None:
    with _run_mock_opa(_MockOPAHandler) as (server, _):
        engine = _engine_for(server)
        decision = engine.authorize(subject="user", action="write", resource="queue")
        assert decision.allow is False
        assert "forbidden" in decision.reason


def test_policy_engine_uses_cache_for_repeated_requests() -> None:
    _CountingOPAHandler.call_count = 0
    with _run_mock_opa(_CountingOPAHandler) as (server, _):
        engine = _engine_for(server)
        first_decision = engine.authorize(subject="admin", action="write", resource="queue")
        second_decision = engine.authorize(subject="admin", action="write", resource="queue")

    assert _CountingOPAHandler.call_count == 1
    # Cached decisions should be the same object instance to avoid unnecessary copies.
    assert first_decision is second_decision


def test_policy_engine_raises_on_unavailable_opa(monkeypatch) -> None:
    def _raise_unavailable(*args, **kwargs):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("nova.policy.engine.urllib.request.urlopen", _raise_unavailable)

    engine = PolicyEngine(opa_url="http://localhost:8181", policy_path="/")
    with pytest.raises(PolicyEngineUnavailable):
        engine.authorize(subject="user", action="read", resource="queue")
