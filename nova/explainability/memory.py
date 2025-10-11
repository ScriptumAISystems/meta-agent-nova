"""Client abstraction for Sophia's shared memory service."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List

LOGGER = logging.getLogger("nova.memory")


@dataclass(slots=True)
class MemorySearchResult:
    """Represents a single entry retrieved from Sophia's memory."""

    identifier: str
    content: Dict[str, Any]
    score: float | None = None


class SophiaMemoryClient:
    """Minimal HTTP client for interacting with Sophia's shared memory API."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self.timeout = timeout

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------
    def store_decision(self, payload: Dict[str, Any]) -> None:
        """Persist a decision payload using the `/memory/store` endpoint."""

        self._post("memory/store", payload)

    def store_context(self, context: Dict[str, Any]) -> None:
        """Persist arbitrary execution context data in Sophia's memory."""

        self._post("memory/store", context)

    def search(self, query: str, *, limit: int = 10) -> List[MemorySearchResult]:
        """Query Sophia's memory using the `/memory/search` endpoint."""

        params = urllib.parse.urlencode({"q": query, "limit": limit})
        url = f"{self.base_url}memory/search?{params}"
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:  # pragma: no cover - network fallback
            LOGGER.warning("Memory search failed: %s", exc)
            return []
        try:
            data = json.loads(body)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            LOGGER.warning("Invalid JSON payload received from Sophia's memory.")
            return []
        results: List[MemorySearchResult] = []
        for entry in data if isinstance(data, list) else []:
            identifier = str(entry.get("id", ""))
            content = entry.get("content", {})
            score = entry.get("score")
            results.append(
                MemorySearchResult(
                    identifier=identifier,
                    content=content if isinstance(content, dict) else {},
                    score=float(score) if score is not None else None,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post(self, endpoint: str, payload: Dict[str, Any]) -> None:
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                pass
        except urllib.error.URLError as exc:  # pragma: no cover - network fallback
            LOGGER.warning("Failed to push data to Sophia's memory: %s", exc)


__all__ = ["SophiaMemoryClient", "MemorySearchResult"]
