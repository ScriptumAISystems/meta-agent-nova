"""OPA-backed policy evaluation engine for Nova."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..logging import get_logger


class PolicyEngineError(RuntimeError):
    """Base error raised for policy engine failures."""


class PolicyEngineUnavailable(PolicyEngineError):
    """Raised when OPA cannot be reached."""


@dataclass
class PolicyDecision:
    """Represents the outcome of a policy evaluation."""

    allow: bool
    reason: str
    raw: Dict[str, Any]


class PolicyEngine:
    """Thin client around an Open Policy Agent server."""

    def __init__(
        self,
        *,
        opa_url: str = "http://localhost:8181",
        policy_path: str = "/v1/data/nova/authz/allow",
        request_timeout: float = 5.0,
    ) -> None:
        self._opa_url = opa_url.rstrip("/")
        self._policy_path = policy_path
        self._timeout = request_timeout
        self._logger = get_logger("nova.policy.engine")
        self._lock = threading.Lock()
        self._cache: Dict[str, PolicyDecision] = {}

    def authorize(
        self,
        *,
        subject: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        payload = {
            "input": {
                "subject": subject,
                "action": action,
                "resource": resource,
                "context": context or {},
            }
        }
        cache_key = json.dumps(payload, sort_keys=True)
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        decision = self._query_opa(payload)
        with self._lock:
            self._cache[cache_key] = decision
        return decision

    def _query_opa(self, payload: Dict[str, Any]) -> PolicyDecision:
        url = f"{self._opa_url}{self._policy_path}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:  # pragma: no cover - network failure path
            self._logger.error("OPA request failed", exc_info=exc)
            raise PolicyEngineUnavailable("OPA server unavailable") from exc

        parsed = json.loads(body)
        result = parsed.get("result")
        if isinstance(result, dict):
            allow = bool(result.get("allow"))
            reason = result.get("reason", "denied by policy" if not allow else "allowed")
        else:
            allow = bool(result)
            reason = "allowed" if allow else "denied by policy"
        decision = PolicyDecision(allow=allow, reason=reason, raw=parsed)
        self._logger.info("Policy decision", extra={"allow": allow, "reason": reason})
        return decision


__all__ = ["PolicyEngine", "PolicyDecision", "PolicyEngineError", "PolicyEngineUnavailable"]
