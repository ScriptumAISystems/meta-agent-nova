"""LangChain ↔ n8n bridge service implementation."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Protocol

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from pydantic import BaseModel


def _model_validate(model: type[BaseModel], data: Mapping[str, Any]) -> BaseModel:
    """Return a pydantic model instance for ``data`` across major versions."""

    try:  # Pydantic v2
        return model.model_validate(data)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - v1 fallback
        return model.parse_obj(data)  # type: ignore[call-arg]


class WorkflowForwarder(Protocol):
    """Protocol for forwarding workflow payloads to downstream systems."""

    async def forward(self, workflow: str, payload: Mapping[str, Any]) -> "WorkflowResult":
        """Send ``payload`` to ``workflow`` and return the downstream outcome."""


@dataclass(slots=True)
class WorkflowResult:
    """Result of a workflow forwarding operation."""

    status_code: int
    detail: str
    response_body: Mapping[str, Any] | None = None


@dataclass(slots=True)
class BridgeSettings:
    """Runtime configuration for the bridge service."""

    n8n_base_url: str
    auth_user: str
    auth_password: str
    shared_secret: str
    signature_header: str = "x-nova-signature"
    request_timeout: float = 10.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "BridgeSettings":
        """Build settings from environment variables."""

        source: Mapping[str, str] = env or os.environ
        base_url = source.get("N8N_WEBHOOK_URL", "http://n8n:5678/webhook")
        user = source.get("N8N_WEBHOOK_USER", "admin")
        password = source.get("N8N_WEBHOOK_PASSWORD", "change_me")
        secret = source.get("NOVA_BRIDGE_TOKEN", "nova-dev-secret")
        header = source.get("NOVA_BRIDGE_SIGNATURE_HEADER", "x-nova-signature")
        timeout = float(source.get("NOVA_BRIDGE_TIMEOUT", "10"))
        return cls(
            n8n_base_url=base_url.rstrip("/"),
            auth_user=user,
            auth_password=password,
            shared_secret=secret,
            signature_header=header.lower(),
            request_timeout=timeout,
        )


class BridgeForwardingError(RuntimeError):
    """Raised when forwarding a request to n8n fails."""


class N8NForwarder:
    """Forwarder implementation that posts payloads to n8n webhooks."""

    def __init__(self, settings: BridgeSettings) -> None:
        self._settings = settings

    async def forward(self, workflow: str, payload: Mapping[str, Any]) -> WorkflowResult:
        url = f"{self._settings.n8n_base_url}/{workflow}".rstrip("/")
        auth = httpx.BasicAuth(self._settings.auth_user, self._settings.auth_password)
        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout) as client:
                response = await client.post(url, json=payload, auth=auth)
                body: Mapping[str, Any] | None = None
                if response.headers.get("content-type", "").startswith("application/json"):
                    try:
                        body = response.json()
                    except ValueError:
                        body = None
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - error path
            raise BridgeForwardingError(
                f"n8n responded with status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            raise BridgeForwardingError(f"Failed to reach n8n webhook at {url}: {exc}") from exc

        detail = "forwarded"
        if isinstance(body, Mapping) and "detail" in body:
            detail = str(body["detail"])
        return WorkflowResult(status_code=response.status_code, detail=detail, response_body=body)


class SummaryRefreshPayload(BaseModel):
    """Payload schema for the summary refresh workflow."""

    context: MutableMapping[str, Any] | None = None


class FinetuneStatusPayload(BaseModel):
    """Payload schema for finetuning status updates."""

    run_id: str
    stage: str
    metrics: MutableMapping[str, Any] | None = None


class ForwardResponse(BaseModel):
    """Standard response emitted by the bridge endpoints."""

    workflow: str
    status: str
    n8n_status: int
    detail: str
    forwarded_payload: Mapping[str, Any]


def _compute_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return digest


async def _read_body(request: Request) -> bytes:
    return await request.body()


def _verify_signature(settings: BridgeSettings, headers: Mapping[str, str], body: bytes) -> None:
    if not settings.shared_secret:
        return
    header_name = settings.signature_header.lower()
    provided = None
    for key, value in headers.items():
        if key.lower() == header_name:
            provided = value.strip()
            break
    if provided is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature header")
    expected = _compute_signature(settings.shared_secret, body)
    if provided.startswith("sha256="):
        provided = provided.split("=", 1)[1]
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")


def _parse_json(body: bytes) -> Mapping[str, Any]:
    if not body:
        return {}
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc


def create_bridge_app(
    settings: BridgeSettings | None = None,
    forwarder: WorkflowForwarder | None = None,
) -> FastAPI:
    """Create a configured FastAPI application for the bridge."""

    cfg = settings or BridgeSettings.from_env()
    router = APIRouter()
    sink = forwarder or N8NForwarder(cfg)

    @router.get("/health")
    async def healthcheck() -> Mapping[str, Any]:
        return {
            "status": "ok",
            "n8n_base_url": cfg.n8n_base_url,
            "timeout": cfg.request_timeout,
        }

    @router.post("/workflows/summary-refresh", response_model=ForwardResponse)
    async def summary_refresh(request: Request) -> ForwardResponse:
        body = await _read_body(request)
        _verify_signature(cfg, request.headers, body)
        payload_raw = _parse_json(body)
        model = _model_validate(SummaryRefreshPayload, payload_raw)
        payload_to_forward: Mapping[str, Any] = {"context": dict(model.context or {})}
        try:
            result = await sink.forward("summary-refresh", payload_to_forward)
        except BridgeForwardingError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        return ForwardResponse(
            workflow="summary-refresh",
            status="forwarded",
            n8n_status=result.status_code,
            detail=result.detail,
            forwarded_payload=payload_to_forward,
        )

    @router.post("/workflows/finetune-status", response_model=ForwardResponse)
    async def finetune_status(request: Request) -> ForwardResponse:
        body = await _read_body(request)
        _verify_signature(cfg, request.headers, body)
        payload_raw = _parse_json(body)
        model = _model_validate(FinetuneStatusPayload, payload_raw)
        payload_to_forward = {
            "run_id": model.run_id,
            "stage": model.stage,
            "metrics": dict(model.metrics or {}),
        }
        try:
            result = await sink.forward("finetune-status", payload_to_forward)
        except BridgeForwardingError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        return ForwardResponse(
            workflow="finetune-status",
            status="forwarded",
            n8n_status=result.status_code,
            detail=result.detail,
            forwarded_payload=payload_to_forward,
        )

    app = FastAPI(title="Nova LangChain ↔ n8n Bridge", version="0.1.0")
    app.include_router(router)
    app.state.settings = cfg
    return app


__all__ = [
    "BridgeSettings",
    "BridgeForwardingError",
    "WorkflowForwarder",
    "WorkflowResult",
    "N8NForwarder",
    "create_bridge_app",
]
