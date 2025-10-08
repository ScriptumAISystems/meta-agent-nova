"""Unit tests for the OPA policy engine integration."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from nova.policy import PolicyEngine


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


def _start_mock_opa() -> Tuple[HTTPServer, threading.Thread]:
    server = HTTPServer(("localhost", 0), _MockOPAHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_policy_engine_authorizes_admin() -> None:
    server, _ = _start_mock_opa()
    engine = PolicyEngine(opa_url=f"http://localhost:{server.server_address[1]}", policy_path="/")
    decision = engine.authorize(subject="admin", action="write", resource="queue")
    assert decision.allow is True
    assert "admin" in decision.reason
    server.shutdown()


def test_policy_engine_denies_default_user() -> None:
    server, _ = _start_mock_opa()
    engine = PolicyEngine(opa_url=f"http://localhost:{server.server_address[1]}", policy_path="/")
    decision = engine.authorize(subject="user", action="write", resource="queue")
    assert decision.allow is False
    assert "forbidden" in decision.reason
    server.shutdown()
