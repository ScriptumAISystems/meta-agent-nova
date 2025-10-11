"""NovaCore orchestrates planning, execution and learning for Project Nova."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Protocol, Sequence

from ..explainability import ExplainabilityLogger, SophiaMemoryClient
from ..governance import GovernanceAuditor, GovernanceClient

LOGGER = logging.getLogger("nova.core")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class TaskRequest:
    """Describes an inbound request that Nova should execute."""

    goal: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PlannedTask:
    """Single task that will be executed by a dedicated sub-agent."""

    identifier: str
    description: str
    agent: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.identifier,
            "description": self.description,
            "agent": self.agent,
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class TaskPlan:
    """Collection of tasks derived from a request."""

    request: TaskRequest
    tasks: List[PlannedTask]
    identifier: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.identifier,
            "created_at": self.created_at,
            "request": {
                "goal": self.request.goal,
                "context": dict(self.request.context),
                "metadata": dict(self.request.metadata),
            },
            "tasks": [task.to_dict() for task in self.tasks],
        }


@dataclass(slots=True)
class TaskExecutionResult:
    """Outcome of executing a planned task."""

    task: PlannedTask
    status: str
    output: Dict[str, Any]
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status.lower() in {"completed", "success", "ok"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task.to_dict(),
            "status": self.status,
            "output": dict(self.output),
            "metrics": dict(self.metrics),
            "success": self.success,
        }


@dataclass(slots=True)
class EvaluationReport:
    """Aggregated evaluation for an execution run."""

    success: bool
    summary: str
    issues: List[str] = field(default_factory=list)
    quality_score: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "summary": self.summary,
            "issues": list(self.issues),
            "quality_score": self.quality_score,
        }


# ---------------------------------------------------------------------------
# Protocol definitions for dependency injection
# ---------------------------------------------------------------------------
class PlannerAgent(Protocol):
    name: str

    def plan(self, request: TaskRequest) -> Sequence[PlannedTask]:  # pragma: no cover - protocol
        ...


class ExecutionAgent(Protocol):
    name: str

    def execute(self, task: PlannedTask, context: Mapping[str, Any]) -> TaskExecutionResult:  # pragma: no cover - protocol
        ...


class TesterAgent(Protocol):
    name: str

    def evaluate(self, results: Sequence[TaskExecutionResult]) -> EvaluationReport:  # pragma: no cover - protocol
        ...


class OpsAgent(Protocol):
    name: str

    def apply(self, evaluation: EvaluationReport) -> Dict[str, Any]:  # pragma: no cover - protocol
        ...


# ---------------------------------------------------------------------------
# Event bus implementation
# ---------------------------------------------------------------------------
class RedisEventBus:
    """Publish events to Redis streams or fallback to an in-memory buffer."""

    def __init__(
        self,
        *,
        stream_name: str = "nova-events",
        redis_client: Any | None = None,
    ) -> None:
        self.stream_name = stream_name
        self.redis_client = redis_client
        self._buffer: List[Dict[str, Any]] = []

    def publish(self, event_type: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        event = {
            "id": uuid.uuid4().hex,
            "timestamp": time.time(),
            "type": event_type,
            "payload": json.dumps(dict(payload)),
        }
        if self.redis_client is not None:  # pragma: no cover - requires redis runtime
            try:
                self.redis_client.xadd(self.stream_name, event)
            except Exception:  # pragma: no cover - defensive
                self._buffer.append(event)
        else:
            self._buffer.append(event)
        return event

    @property
    def buffered_events(self) -> List[Dict[str, Any]]:
        return list(self._buffer)


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------
class NovaCore:
    """High level orchestrator for Project Nova's meta-agent."""

    def __init__(
        self,
        *,
        planner: PlannerAgent,
        agents: Mapping[str, ExecutionAgent],
        tester: TesterAgent | None = None,
        ops: OpsAgent | None = None,
        event_bus: RedisEventBus | None = None,
        explainability: ExplainabilityLogger | None = None,
        governance: GovernanceClient | None = None,
        auditor: GovernanceAuditor | None = None,
        memory_client: SophiaMemoryClient | None = None,
    ) -> None:
        if not planner:
            raise ValueError("NovaCore requires a planner instance.")
        self.planner = planner
        self.agents = {name.lower(): agent for name, agent in agents.items()}
        self.tester = tester
        self.ops = ops
        self.event_bus = event_bus or RedisEventBus()
        self.explainability = explainability or ExplainabilityLogger()
        if memory_client is not None:
            self.explainability.attach_memory_client(memory_client)
        self.governance = governance
        self.auditor = auditor or GovernanceAuditor()
        self.memory_client = memory_client
        self._history: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    def plan_task(self, request: TaskRequest) -> TaskPlan:
        self._check_governance("plan", {"goal": request.goal})
        tasks = [
            PlannedTask(
                identifier=task.identifier,
                description=task.description,
                agent=task.agent,
                dependencies=list(task.dependencies),
                metadata=dict(task.metadata),
            )
            for task in self.planner.plan(request)
        ]
        plan = TaskPlan(request=request, tasks=tasks)
        for task in plan.tasks:
            task.metadata.setdefault("plan_id", plan.identifier)
        self._history[plan.identifier] = {"plan": plan, "results": [], "evaluation": None}
        self.event_bus.publish("plan.created", plan.to_dict())
        self.explainability.log_decision(
            "planning",
            reason="Generated execution plan",
            evidence={"tasks": [task.to_dict() for task in tasks]},
            impact="task-breakdown",
            metadata={"goal": request.goal},
        )
        LOGGER.info("Plan created for goal '%s' with %d tasks.", request.goal, len(tasks))
        return plan

    # ------------------------------------------------------------------
    def execute_task(self, plan_or_task: TaskPlan | PlannedTask) -> List[TaskExecutionResult]:
        if isinstance(plan_or_task, TaskPlan):
            plan = plan_or_task
            tasks = plan.tasks
            context = plan.request.context
        else:
            plan = None
            tasks = [plan_or_task]
            context = {}
        results: List[TaskExecutionResult] = []
        for task in tasks:
            self._check_governance("execute", task.to_dict())
            agent = self.agents.get(task.agent.lower())
            if agent is None:
                raise KeyError(f"No agent registered for type '{task.agent}'.")
            LOGGER.info("Executing task '%s' with agent '%s'.", task.identifier, task.agent)
            result = agent.execute(task, context)
            results.append(result)
            self.event_bus.publish("task.completed", result.to_dict())
            self.explainability.log_decision(
                "execution",
                reason=f"Task {task.identifier} completed with status {result.status}",
                evidence=result.to_dict(),
                impact="agent-feedback",
                metadata={"agent": task.agent},
            )
        if plan is not None:
            history = self._history.get(plan.identifier)
            if history:
                history["results"] = list(results)
        return results

    # ------------------------------------------------------------------
    def evaluate_result(self, results: Sequence[TaskExecutionResult]) -> EvaluationReport:
        payload = {"results": [result.to_dict() for result in results]}
        self._check_governance("evaluate", payload)
        if self.tester is not None:
            report = self.tester.evaluate(results)
        else:
            success = all(result.success for result in results)
            summary = "All tasks completed successfully." if success else "Issues detected during execution."
            failing = [result.task.identifier for result in results if not result.success]
            report = EvaluationReport(success=success, summary=summary, issues=failing)
        self.event_bus.publish("evaluation.completed", report.to_dict())
        self.explainability.log_decision(
            "evaluation",
            reason="Evaluation cycle finished.",
            evidence=report.to_dict(),
            impact="quality-score",
        )
        if self.ops is not None:
            ops_feedback = self.ops.apply(report) or {}
            self.event_bus.publish("ops.adjustment", {"feedback": ops_feedback})
            self.explainability.log_decision(
                "operations",
                reason="Operations agent applied changes.",
                evidence={"feedback": ops_feedback},
                impact="pipeline-updated",
            )
        if results:
            plan_id = results[0].task.metadata.get("plan_id") if isinstance(results[0].task.metadata, dict) else None
            if plan_id and plan_id in self._history:
                self._history[plan_id]["evaluation"] = report
        return report

    # ------------------------------------------------------------------
    def update_memory(self, context: Mapping[str, Any], result: EvaluationReport) -> Dict[str, Any]:
        payload = {
            "context": dict(context),
            "result": result.to_dict(),
        }
        self._check_governance("memory-update", payload)
        if self.memory_client is not None:
            self.memory_client.store_context(payload)
        record = self.explainability.log_decision(
            "memory",
            reason="Shared evaluation with Sophia.",
            evidence=payload,
            impact="knowledge-sharing",
        )
        return record.to_dict()

    # ------------------------------------------------------------------
    def get_status(self, plan_id: str) -> Dict[str, Any]:
        history = self._history.get(plan_id)
        if not history:
            raise KeyError(f"Unknown plan id '{plan_id}'.")
        plan: TaskPlan = history["plan"]
        results: List[TaskExecutionResult] = history.get("results", [])
        evaluation: EvaluationReport | None = history.get("evaluation")
        return {
            "plan": plan.to_dict(),
            "results": [result.to_dict() for result in results],
            "evaluation": evaluation.to_dict() if evaluation else None,
        }

    # ------------------------------------------------------------------
    def _check_governance(self, action: str, payload: Mapping[str, Any]) -> None:
        if self.governance is None:
            return
        decision = self.governance.evaluate_action(action, payload)
        if decision.is_blocking:
            self.auditor.record(action, decision.verdict, payload, decision.rationale)
            self.explainability.log_decision(
                "governance",
                reason=f"Action '{action}' blocked.",
                evidence={"payload": dict(payload), "decision": decision.verdict},
                impact="blocked",
            )
            raise PermissionError(f"Governance blocked action '{action}': {decision.rationale}")
        if decision.is_warning:
            self.explainability.log_decision(
                "governance",
                reason=f"Action '{action}' warning.",
                evidence={"payload": dict(payload), "decision": decision.verdict},
                impact="warning",
            )


__all__ = [
    "EvaluationReport",
    "NovaCore",
    "PlannedTask",
    "RedisEventBus",
    "TaskExecutionResult",
    "TaskPlan",
    "TaskRequest",
]
