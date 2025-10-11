"""FastAPI application that exposes Nova's orchestration capabilities."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Mapping

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from ..core import NovaCore, PlannedTask, TaskExecutionResult, TaskRequest
from ..explainability import ExplainabilityLogger
from ..self_optimization import PipelineMetrics, PipelineOptimizer

LOGGER = logging.getLogger("nova.api")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class TaskRequestModel(BaseModel):
    goal: str = Field(..., description="High level objective for Nova to execute.")
    context: Dict[str, Any] | None = Field(default_factory=dict)
    metadata: Dict[str, Any] | None = Field(default_factory=dict)

    def to_domain(self) -> TaskRequest:
        return TaskRequest(
            goal=self.goal,
            context=dict(self.context or {}),
            metadata=dict(self.metadata or {}),
        )


class TaskResponseModel(BaseModel):
    plan: Dict[str, Any]
    results: List[Dict[str, Any]]
    evaluation: Dict[str, Any]


class StatusResponseModel(BaseModel):
    plan: Dict[str, Any]
    results: List[Dict[str, Any]]
    evaluation: Dict[str, Any] | None


class OptimizationMetricModel(BaseModel):
    build_time_seconds: float = Field(..., gt=0)
    error_rate: float = Field(..., ge=0, le=1)
    coverage: float = Field(..., ge=0, le=1)


class OptimizationRequestModel(BaseModel):
    metrics: List[OptimizationMetricModel]


class OptimizationResponseModel(BaseModel):
    reward: float
    recommendation: str


# ---------------------------------------------------------------------------
# Default in-process agents used by the public API
# ---------------------------------------------------------------------------
class SimplePlanner:
    name = "planner"

    def plan(self, request: TaskRequest) -> List[PlannedTask]:
        description_prefix = request.metadata.get("summary") or request.goal
        first_id = f"plan-{uuid.uuid4().hex[:8]}"
        tasks = [
            PlannedTask(
                identifier=first_id,
                description=f"Analyse objective: {description_prefix}",
                agent="coder",
                metadata={"priority": 1},
            )
        ]
        second_id = f"plan-{uuid.uuid4().hex[:8]}"
        third_id = f"plan-{uuid.uuid4().hex[:8]}"
        tasks.append(
            PlannedTask(
                identifier=second_id,
                description="Verify implementation with automated tests",
                agent="tester",
                dependencies=[tasks[0].identifier],
                metadata={"priority": 2},
            )
        )
        tasks.append(
            PlannedTask(
                identifier=third_id,
                description="Prepare deployment artefacts and monitoring",
                agent="ops",
                dependencies=[tasks[0].identifier, second_id],
                metadata={"priority": 3},
            )
        )
        return tasks


class SimpleExecutionAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    def execute(self, task: PlannedTask, context: Mapping[str, Any]) -> TaskExecutionResult:
        output = {
            "agent": self.name,
            "description": task.description,
            "context": dict(context),
        }
        return TaskExecutionResult(task=task, status="completed", output=output, metrics={})


class APOps:
    name = "ops"

    def apply(self, evaluation: Any) -> Dict[str, Any]:
        return {"next_action": "monitor" if evaluation.success else "rollback"}


# ---------------------------------------------------------------------------
# Application wiring
# ---------------------------------------------------------------------------
explainability_logger = ExplainabilityLogger()
planner = SimplePlanner()
agents = {
    "coder": SimpleExecutionAgent("coder"),
    "tester": SimpleExecutionAgent("tester"),
    "ops": SimpleExecutionAgent("ops"),
}

core = NovaCore(
    planner=planner,
    agents=agents,
    tester=None,
    ops=APOps(),
    explainability=explainability_logger,
)

optimizer = PipelineOptimizer(logger=explainability_logger)
app = FastAPI(title="Nova API", version="1.0.0", description="Meta-Agent Nova orchestration layer")


@app.post("/task", response_model=TaskResponseModel)
async def create_task(request: TaskRequestModel) -> TaskResponseModel:
    task_request = request.to_domain()
    plan = core.plan_task(task_request)
    results = core.execute_task(plan)
    evaluation = core.evaluate_result(results)
    core.update_memory(task_request.context, evaluation)
    return TaskResponseModel(
        plan=plan.to_dict(),
        results=[result.to_dict() for result in results],
        evaluation=evaluation.to_dict(),
    )


@app.get("/status/{plan_id}", response_model=StatusResponseModel)
async def get_status(plan_id: str) -> StatusResponseModel:
    try:
        status = core.get_status(plan_id)
    except KeyError as exc:  # pragma: no cover - triggered by invalid id
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StatusResponseModel(**status)


@app.post("/optimize", response_model=OptimizationResponseModel)
async def optimize(request: OptimizationRequestModel) -> OptimizationResponseModel:
    metrics = [
        PipelineMetrics(
            build_time_seconds=metric.build_time_seconds,
            error_rate=metric.error_rate,
            coverage=metric.coverage,
        )
        for metric in request.metrics
    ]
    report = optimizer.analyse(metrics)
    return OptimizationResponseModel(reward=report.reward, recommendation=report.recommendation)


try:  # pragma: no cover - optional dependency
    from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
except Exception:  # pragma: no cover - fallback when prometheus is unavailable
    CONTENT_TYPE_LATEST = "text/plain"
    generate_latest = None
    REGISTRY = None


@app.get("/metrics")
async def metrics_endpoint() -> Response:
    if generate_latest is None or REGISTRY is None:
        body = "prometheus_client not installed."
        return Response(content=body, media_type=CONTENT_TYPE_LATEST)
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


__all__ = ["app", "core", "optimizer"]
