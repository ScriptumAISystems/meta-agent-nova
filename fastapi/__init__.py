"""Lightweight FastAPI-compatible shim for test environments without external deps."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Iterable, List, Mapping

from pydantic import BaseModel


__all__ = [
    "APIRouter",
    "FastAPI",
    "HTTPException",
    "Request",
    "Response",
    "status",
]


class HTTPException(Exception):
    """Minimal HTTP exception mirroring FastAPI's behaviour."""

    def __init__(self, status_code: int, detail: str = "") -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Response:
    """Simplified response container."""

    def __init__(self, content: Any, media_type: str = "application/json") -> None:
        self.content = content
        self.media_type = media_type


class Request:
    """Request wrapper used by the shimmed router."""

    def __init__(self, body: bytes, headers: Mapping[str, str] | None = None) -> None:
        self._body = body
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}

    async def body(self) -> bytes:
        return self._body


@dataclass
class _Route:
    path: str
    methods: Iterable[str]
    endpoint: Callable[..., Any]
    response_model: type[BaseModel] | None = None


class APIRouter:
    """Collects route definitions and attaches them to a FastAPI instance."""

    def __init__(self) -> None:
        self.routes: List[_Route] = []

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        methods: Iterable[str],
        response_model: type[BaseModel] | None = None,
    ) -> None:
        self.routes.append(_Route(path=path, methods=[m.upper() for m in methods], endpoint=endpoint, response_model=response_model))

    def get(self, path: str, response_model: type[BaseModel] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, func, ["GET"], response_model=response_model)
            return func

        return decorator

    def post(self, path: str, response_model: type[BaseModel] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, func, ["POST"], response_model=response_model)
            return func

        return decorator


class FastAPI:
    """Extremely small subset of FastAPI used for testing."""

    def __init__(self, title: str | None = None, version: str | None = None, description: str | None = None) -> None:
        self.title = title or "FastAPI"
        self.version = version or "0"
        self.description = description or ""
        self._routes: List[_Route] = []
        self.state = SimpleNamespace()

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        methods: Iterable[str],
        response_model: type[BaseModel] | None = None,
    ) -> None:
        self._routes.append(_Route(path=path, methods=[m.upper() for m in methods], endpoint=endpoint, response_model=response_model))

    def include_router(self, router: APIRouter) -> None:
        self._routes.extend(router.routes)

    def _find_route(self, method: str, path: str) -> _Route | None:
        method = method.upper()
        for route in self._routes:
            if path == route.path and method in route.methods:
                return route
        return None

    async def _invoke(self, route: _Route, request: Request) -> tuple[int, Any]:
        try:
            result = route.endpoint(request)  # type: ignore[arg-type]
            if asyncio.iscoroutine(result):
                result = await result
        except HTTPException as exc:
            return exc.status_code, {"detail": exc.detail}

        if isinstance(result, Response):
            return 200, result.content
        if isinstance(result, BaseModel):
            try:
                data = result.model_dump()  # type: ignore[attr-defined]
            except AttributeError:  # pragma: no cover - pydantic v1 fallback
                data = result.dict()  # type: ignore[attr-defined]
            return 200, data
        if isinstance(result, dict):
            return 200, result
        return 200, result

    async def handle(self, method: str, path: str, body: bytes, headers: Mapping[str, str]) -> tuple[int, Any]:
        route = self._find_route(method, path)
        if route is None:
            return 404, {"detail": "Not Found"}
        request = Request(body=body, headers=headers)
        return await self._invoke(route, request)


class _StatusModule:
    HTTP_200_OK = 200
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_404_NOT_FOUND = 404
    HTTP_502_BAD_GATEWAY = 502


status = _StatusModule()
