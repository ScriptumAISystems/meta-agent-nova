"""Test client for the lightweight FastAPI shim."""

from __future__ import annotations

import json
from typing import Any, Mapping

from . import FastAPI


class _ShimResponse:
    def __init__(self, status_code: int, data: Any) -> None:
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        return self._data

    @property
    def text(self) -> str:
        if isinstance(self._data, (dict, list)):
            return json.dumps(self._data)
        return str(self._data)


class TestClient:
    """Invoke app routes directly without spinning up an HTTP server."""

    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def _prepare_body(self, data: Any = None, json_body: Any = None) -> bytes:
        if data is not None:
            if isinstance(data, bytes):
                return data
            if isinstance(data, str):
                return data.encode("utf-8")
            raise TypeError("data must be bytes or str")
        if json_body is None:
            return b""
        return json.dumps(json_body).encode("utf-8")

    def post(self, path: str, data: Any = None, json: Any = None, headers: Mapping[str, str] | None = None) -> _ShimResponse:
        body = self._prepare_body(data=data, json_body=json)
        status_code, payload = self._run("POST", path, body, headers or {})
        return _ShimResponse(status_code, payload)

    def get(self, path: str, headers: Mapping[str, str] | None = None) -> _ShimResponse:
        status_code, payload = self._run("GET", path, b"", headers or {})
        return _ShimResponse(status_code, payload)

    def _run(self, method: str, path: str, body: bytes, headers: Mapping[str, str]) -> tuple[int, Any]:
        loop = None
        try:
            import asyncio

            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._app.handle(method, path, body, headers))


TestClient.__test__ = False  # Prevent pytest from treating this as a test container.
