"""Vibe session manager orchestrating planner, coder and tester loops."""

from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Protocol

from ..explainability import ExplainabilityLogger


class PlannerProtocol(Protocol):
    """Protocol describing the planner component used in vibe sessions."""

    def plan(self, goal: str, style: str, parameters: Mapping[str, Any]) -> Mapping[str, Any]:
        """Produce a structured plan for the given goal and creative style."""


class CoderProtocol(Protocol):
    """Protocol describing the coder component used in vibe sessions."""

    def generate(
        self,
        plan: Mapping[str, Any],
        style: str,
        parameters: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Generate implementation artefacts for the provided plan."""


class TesterProtocol(Protocol):
    """Protocol describing the tester component used in vibe sessions."""

    def evaluate(
        self,
        implementation: Mapping[str, Any],
        plan: Mapping[str, Any],
        parameters: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Evaluate the implementation artefacts and return feedback metrics."""


@dataclass(slots=True)
class SessionParameters:
    """Hyper-parameters that can be adapted during a session."""

    temperature: float = 0.7
    token_budget: int = 8000
    role_bias: Dict[str, float] = field(
        default_factory=lambda: {"planner": 1.0, "coder": 1.0, "tester": 1.0}
    )

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable copy of the parameter state."""

        return {
            "temperature": self.temperature,
            "token_budget": self.token_budget,
            "role_bias": dict(self.role_bias),
        }


class VibeSessionManager:
    """Coordinates the planner/coder/tester feedback loop for a vibe session."""

    def __init__(
        self,
        planner: PlannerProtocol,
        coder: CoderProtocol,
        tester: TesterProtocol,
        *,
        explainability: ExplainabilityLogger | None = None,
        config: Mapping[str, Any] | None = None,
        max_iterations: int = 3,
    ) -> None:
        if max_iterations <= 0:
            raise ValueError("max_iterations must be a positive integer")
        self.planner = planner
        self.coder = coder
        self.tester = tester
        self.parameters = SessionParameters()
        self.max_iterations = max_iterations
        self.explainability = explainability or ExplainabilityLogger()
        cfg = dict(config or {})
        self.use_gpu: bool = bool(cfg.get("use_gpu", False))
        self._gpu_active = False
        self._pending_feedback: List[Dict[str, Any]] = []
        self._session_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start_session(
        self,
        goal: str,
        style: str,
        *,
        iterations: int | None = None,
    ) -> Dict[str, Any]:
        """Run the planner/coder/tester loop for the requested number of iterations."""

        if not goal:
            raise ValueError("Goal must be a non-empty string")
        if not style:
            raise ValueError("Style must be a non-empty string")
        total_iterations = iterations or self.max_iterations
        if total_iterations <= 0:
            raise ValueError("iterations must be a positive integer")

        self._activate_gpu_if_configured()
        session_id = uuid.uuid4().hex
        session_log: Dict[str, Any] = {
            "session_id": session_id,
            "goal": goal,
            "style": style,
            "iterations": [],
        }
        scores: List[float] = []

        for index in range(total_iterations):
            parameter_snapshot = self.parameters.snapshot()
            plan = self.planner.plan(goal, style, parameter_snapshot)
            implementation = self.coder.generate(plan, style, parameter_snapshot)
            evaluation = self.tester.evaluate(implementation, plan, parameter_snapshot)
            feedback_score = float(evaluation.get("score", 0.0))
            scores.append(feedback_score)
            iteration_log = {
                "iteration": index + 1,
                "plan": dict(plan),
                "implementation": dict(implementation),
                "evaluation": dict(evaluation),
                "parameters": parameter_snapshot,
            }
            session_log["iterations"].append(iteration_log)
            self._pending_feedback.append(
                {
                    "session_id": session_id,
                    "iteration": index + 1,
                    "goal": goal,
                    "style": style,
                    "plan": dict(plan),
                    "implementation": dict(implementation),
                    "evaluation": dict(evaluation),
                }
            )
            self.adapt_parameters(feedback_score)

        average_score = statistics.fmean(scores) if scores else 0.0
        session_log["summary"] = {
            "iterations": total_iterations,
            "average_score": average_score,
            "gpu_active": self._gpu_active,
        }
        self._session_history.append(session_log)
        return session_log

    def collect_feedback(self) -> List[Any]:
        """Persist pending iteration logs in the explainability layer."""

        records = []
        while self._pending_feedback:
            payload = self._pending_feedback.pop(0)
            iteration = payload["iteration"]
            evaluation = payload["evaluation"]
            score = evaluation.get("score")
            record = self.explainability.log_decision(
                "vibe_session",
                reason=f"Iteration {iteration} feedback collected",
                evidence={
                    "goal": payload["goal"],
                    "style": payload["style"],
                    "plan": payload["plan"],
                    "implementation": payload["implementation"],
                    "evaluation": evaluation,
                },
                impact="high" if isinstance(score, (int, float)) and score > 0.8 else "medium",
                metadata={
                    "session_id": payload["session_id"],
                    "iteration": iteration,
                    "gpu_active": self._gpu_active,
                },
            )
            records.append(record)
        return records

    def adapt_parameters(self, feedback_score: float) -> None:
        """Adjust temperature, token budget and role bias based on feedback."""

        if not 0.0 <= feedback_score <= 1.0:
            raise ValueError("feedback_score must be between 0.0 and 1.0")
        params = self.parameters
        if feedback_score >= 0.9:
            params.temperature = max(0.1, round(params.temperature - 0.1, 3))
            params.token_budget = max(1000, params.token_budget - 1000)
            params.role_bias["tester"] = min(2.0, round(params.role_bias.get("tester", 1.0) + 0.1, 3))
        elif feedback_score >= 0.75:
            params.temperature = max(0.1, round(params.temperature - 0.05, 3))
            params.token_budget = max(2000, params.token_budget - 500)
            params.role_bias["coder"] = min(2.0, round(params.role_bias.get("coder", 1.0) + 0.05, 3))
        else:
            params.temperature = min(1.5, round(params.temperature + 0.1, 3))
            params.token_budget = min(20000, params.token_budget + 1000)
            params.role_bias["planner"] = min(2.0, round(params.role_bias.get("planner", 1.0) + 0.05, 3))

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @property
    def session_history(self) -> List[Dict[str, Any]]:
        """Return a copy of executed session logs."""

        return list(self._session_history)

    @property
    def gpu_active(self) -> bool:
        """Return whether GPU hooks were activated for the last session."""

        return self._gpu_active

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _activate_gpu_if_configured(self) -> None:
        """Enable GPU hooks based on the configuration flag."""

        self._gpu_active = bool(self.use_gpu)
