"""NovaCore orchestrates planning, execution and learning for Project Nova."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Protocol, Sequence

from ..builder.builder_agent import BuilderAgent
from ..explainability import ExplainabilityLogger, SophiaMemoryClient
from ..governance import GovernanceAuditor, GovernanceClient, GovernanceDecision

try:  # pragma: no cover - optional dependency
    from ..self_optimization import PipelineOptimizer
except Exception:  # pragma: no cover - optional dependency missing
    PipelineOptimizer = None  # type: ignore[assignment]

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
    reward: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "summary": self.summary,
            "issues": list(self.issues),
            "quality_score": self.quality_score,
            "reward": self.reward,
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
        shared_memory_refresh_interval: float = 300.0,
        shared_memory_query: str | None = "nova.orchestration",
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
        self._governance_log: List[Dict[str, Any]] = []
        self._memory_cache: List[Dict[str, Any]] = []
        self.refresh_interval = max(shared_memory_refresh_interval, 0.0)
        self._default_refresh_query = shared_memory_query
        self._last_refresh: float = 0.0
        optimizer = None
        if PipelineOptimizer is not None:
            try:
                optimizer = PipelineOptimizer(logger=self.explainability)
            except Exception:  # pragma: no cover - defensive
                optimizer = None
        self.builder = BuilderAgent(
            explainability=self.explainability,
            governance=self.governance,
            optimizer=optimizer,
        )

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
        phase_progress: Dict[str, Dict[str, Any]] = {}
        for task in plan.tasks:
            phase_name = str(task.metadata.get("phase", "unspecified")).strip() or "unspecified"
            key = phase_name.lower()
            entry = phase_progress.setdefault(
                key,
                {"phase": phase_name, "total": 0, "completed": 0},
            )
            entry["total"] += 1
        self._history[plan.identifier] = {
            "plan": plan,
            "results": [],
            "evaluation": None,
            "phase_progress": phase_progress,
            "resume_points": {},
            "_completed_tasks": set(),
        }
        self.event_bus.publish("plan.created", plan.to_dict())
        try:
            graph_path = self.export_orchestration_graph(plan)
            self.event_bus.publish(
                "plan.graph",
                {"plan_id": plan.identifier, "path": str(graph_path)},
            )
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to export orchestration graph: %s", exc)
        self.explainability.log_decision(
            "planning",
            reason="Generated execution plan",
            evidence={"tasks": [task.to_dict() for task in tasks]},
            impact="task-breakdown",
            metadata={"goal": request.goal},
        )
        self.memory_checkpoint(plan.identifier, metadata={"event": "plan_created"})
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
            if self.memory_client is not None and self.refresh_interval:
                self.refresh()
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
                if history is not None:
                    phase_name = str(task.metadata.get("phase", "unspecified")).strip() or "unspecified"
                    key = phase_name.lower()
                    phase_progress = history.setdefault("phase_progress", {})
                    entry = phase_progress.setdefault(
                        key,
                        {"phase": phase_name, "total": 0, "completed": 0},
                    )
                    if entry["total"] == 0:
                        entry["total"] = 1
                    if result.success:
                        completed_ids = history.setdefault("_completed_tasks", set())
                        if task.identifier not in completed_ids:
                            entry["completed"] = entry.get("completed", 0) + 1
                            completed_ids.add(task.identifier)
                    history["last_phase"] = phase_name
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
            report = EvaluationReport(
                success=success,
                summary=summary,
                issues=failing,
                quality_score=100.0 if success else 0.0,
                reward=100.0 if success else 0.0,
            )
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
        reward_value = report.reward if hasattr(report, "reward") else None
        if reward_value is None and report.quality_score is not None:
            reward_value = report.quality_score
        if isinstance(reward_value, (int, float)) and reward_value < 50:
            try:
                self.builder.sync_ci_workflows()
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.warning("Builder CI sync attempt failed: %s", exc)
        if results:
            plan_id = results[0].task.metadata.get("plan_id") if isinstance(results[0].task.metadata, dict) else None
            if plan_id and plan_id in self._history:
                self._history[plan_id]["evaluation"] = report
                phase_progress = self._history[plan_id].get("phase_progress")
                if phase_progress:
                    self._history[plan_id]["phase_progress"] = phase_progress
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
    def memory_checkpoint(
        self,
        plan_id: str | None = None,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Persist a structured snapshot of the current orchestration state."""

        plans: Dict[str, Any] = {}
        if plan_id and plan_id not in self._history:
            raise KeyError(f"Unknown plan id '{plan_id}'.")
        selected_items = (
            {plan_id: self._history[plan_id]}
            if plan_id and plan_id in self._history
            else self._history
        )
        for identifier, history in selected_items.items():
            plan: TaskPlan = history["plan"]
            results: List[TaskExecutionResult] = history.get("results", [])
            evaluation: EvaluationReport | None = history.get("evaluation")
            phase_progress = history.get("phase_progress", {})
            resume_points = history.get("resume_points", {})
            plans[identifier] = {
                "plan": plan.to_dict(),
                "results": [result.to_dict() for result in results],
                "evaluation": evaluation.to_dict() if evaluation else None,
                "phase_progress": {
                    key: {
                        "phase": value.get("phase"),
                        "total": value.get("total", 0),
                        "completed": value.get("completed", 0),
                    }
                    for key, value in phase_progress.items()
                },
                "resume_points": {k: dict(v) for k, v in resume_points.items()},
            }
        snapshot = {
            "timestamp": time.time(),
            "plans": plans,
            "governance": list(self._governance_log),
            "memory_cache": list(self._memory_cache),
            "metadata": dict(metadata or {}),
        }
        payload = {"type": "checkpoint", "snapshot": snapshot}
        if self.memory_client is not None:
            try:
                self.memory_client.store_context(payload)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.warning("Failed to persist memory checkpoint: %s", exc)
        self.event_bus.publish("memory.checkpoint", payload)
        self.explainability.log_decision(
            "memory",
            reason="Persisted orchestration checkpoint.",
            evidence={"plan_ids": list(plans.keys())},
            impact="state-checkpoint",
        )
        if plan_id and plan_id in self._history:
            self._history[plan_id]["last_checkpoint"] = snapshot["timestamp"]
        return snapshot

    # ------------------------------------------------------------------
    def export_orchestration_graph(
        self, plan: TaskPlan, path: str | Path = "orchestration_graph.json"
    ) -> Path:
        """Serialise the execution plan into a graph JSON file."""

        path_obj = Path(path)
        if not path_obj.parent.exists():
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, str]] = []
        for task in plan.tasks:
            nodes.append(
                {
                    "id": task.identifier,
                    "label": task.description,
                    "agent": task.agent,
                    "phase": task.metadata.get("phase"),
                    "metadata": dict(task.metadata),
                }
            )
            for dependency in task.dependencies:
                edges.append({"from": dependency, "to": task.identifier})
        graph = {
            "plan_id": plan.identifier,
            "goal": plan.request.goal,
            "created_at": plan.created_at,
            "nodes": nodes,
            "edges": edges,
        }
        with path_obj.open("w", encoding="utf-8") as handle:
            json.dump(graph, handle, indent=2, sort_keys=True, default=str)
        self.explainability.log_decision(
            "planning",
            reason="Exported orchestration graph",
            evidence={"plan_id": plan.identifier, "nodes": len(nodes), "edges": len(edges)},
            impact="graph-export",
        )
        return path_obj

    # ------------------------------------------------------------------
    def refresh(
        self,
        *,
        force: bool = False,
        query: str | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Fetch the latest insights from Sophia's shared memory service."""

        if self.memory_client is None:
            return []
        now = time.time()
        if not force and self.refresh_interval:
            if now - self._last_refresh < self.refresh_interval:
                return list(self._memory_cache)
        effective_query = query or self._default_refresh_query or "nova"
        try:
            results = self.memory_client.search(effective_query, limit=limit)
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Shared memory refresh failed: %s", exc)
            return list(self._memory_cache)
        entries: List[Dict[str, Any]] = [
            {
                "id": result.identifier,
                "content": dict(result.content),
                "score": result.score,
            }
            for result in results
        ]
        self._memory_cache = entries
        self._last_refresh = now
        self.event_bus.publish(
            "memory.refresh",
            {"query": effective_query, "entries": entries},
        )
        self.explainability.log_decision(
            "memory",
            reason="Refreshed insights from shared memory.",
            evidence={"query": effective_query, "entries": entries[:3]},
            impact="memory-refresh",
        )
        return list(entries)

    # ------------------------------------------------------------------
    def phase_resume(self, plan_id: str, phase_name: str) -> Dict[str, Any]:
        """Rebuild execution context for a partially completed phase."""

        history = self._history.get(plan_id)
        if history is None:
            raise KeyError(f"Unknown plan id '{plan_id}'.")
        plan: TaskPlan = history["plan"]
        target = phase_name.lower()
        completed_ids = set(history.get("_completed_tasks", set()))
        phase_tasks = [
            task
            for task in plan.tasks
            if str(task.metadata.get("phase", "unspecified")).strip().lower() == target
        ]
        pending_tasks = [
            task.to_dict()
            for task in phase_tasks
            if task.identifier not in completed_ids
        ]
        summary = {
            "plan_id": plan_id,
            "phase": phase_name,
            "pending": pending_tasks,
            "completed": sum(1 for task in phase_tasks if task.identifier in completed_ids),
            "total": len(phase_tasks),
        }
        history.setdefault("resume_points", {})[target] = summary
        self.event_bus.publish("phase.resume", summary)
        if self.memory_client is not None:
            try:
                self.memory_client.store_context({"type": "phase-resume", **summary})
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.warning("Failed to persist phase resume data: %s", exc)
        self.explainability.log_decision(
            "execution",
            reason=f"Resuming phase '{phase_name}'.",
            evidence={"pending": [task["id"] for task in pending_tasks]},
            impact="phase-resume",
        )
        return summary

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
            "phase_progress": {
                key: {
                    "phase": value.get("phase"),
                    "total": value.get("total", 0),
                    "completed": value.get("completed", 0),
                }
                for key, value in history.get("phase_progress", {}).items()
            },
            "resume_points": {
                key: dict(value) for key, value in history.get("resume_points", {}).items()
            },
        }

    # ------------------------------------------------------------------
    def _check_governance(self, action: str, payload: Mapping[str, Any]) -> None:
        if self.governance is None:
            return
        decision = self.governance.evaluate_action(action, payload)
        impact = "approved"
        if decision.is_blocking:
            self.auditor.record(action, decision.verdict, payload, decision.rationale)
            impact = "blocked"
        elif decision.is_warning:
            self.auditor.record(action, decision.verdict, payload, decision.rationale)
            impact = "warning"
        self._register_governance_feedback(action, decision, payload, impact)
        if decision.is_blocking:
            raise PermissionError(f"Governance blocked action '{action}': {decision.rationale}")

    # ------------------------------------------------------------------
    def _register_governance_feedback(
        self,
        action: str,
        decision: GovernanceDecision | Any,
        payload: Mapping[str, Any],
        impact: str,
    ) -> None:
        verdict = getattr(decision, "verdict", "UNKNOWN")
        rationale = getattr(decision, "rationale", "")
        details = getattr(decision, "details", {})
        payload_dict = dict(payload)
        record = {
            "timestamp": time.time(),
            "action": action,
            "verdict": verdict,
            "rationale": rationale,
            "details": dict(details) if isinstance(details, Mapping) else {},
            "payload": payload_dict,
        }
        self._governance_log.append(record)
        try:
            self.event_bus.publish("governance.decision", record)
        except Exception:  # pragma: no cover - defensive publish
            LOGGER.debug("Failed to publish governance decision.", exc_info=True)
        if self.memory_client is not None:
            try:
                self.memory_client.store_decision(record)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.warning("Failed to persist governance decision: %s", exc)
        self.explainability.log_decision(
            "governance",
            reason=f"Action '{action}' governance verdict: {verdict}",
            evidence={"payload": payload_dict, "decision": record},
            impact=impact,
        )
        plan_id = None
        if isinstance(payload_dict, Mapping):
            plan_id = payload_dict.get("plan_id")
            if plan_id is None:
                task_payload = payload_dict.get("task")
                if isinstance(task_payload, Mapping):
                    metadata = task_payload.get("metadata")
                    if isinstance(metadata, Mapping):
                        plan_id = metadata.get("plan_id")
        if plan_id and plan_id in self._history:
            self._history[plan_id].setdefault("governance", []).append(record)


__all__ = [
    "EvaluationReport",
    "NovaCore",
    "PlannedTask",
    "RedisEventBus",
    "TaskExecutionResult",
    "TaskPlan",
    "TaskRequest",
]
