"""Autonomous repository builder agent for Nova."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Mapping

from ..explainability import ExplainabilityLogger
from ..governance import GovernanceClient
from .ci_sync import CISync, CISyncResult
from .code_generator import CodeGenerationReport, CodeGenerator
from .repo_manager import RepoManager, RepositorySnapshot

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ..core.engine import PlannedTask, TaskExecutionResult

try:  # pragma: no cover - optional dependency for optimisation feedback
    from ..self_optimization import PipelineMetrics, PipelineOptimizer
except Exception:  # pragma: no cover - defensive fallback
    PipelineMetrics = None  # type: ignore[assignment]
    PipelineOptimizer = None  # type: ignore[assignment]

LOGGER = logging.getLogger("nova.builder.agent")


class BuilderAgent:
    """Coordinates repository scanning, code generation and CI sync."""

    name = "builder"

    def __init__(
        self,
        *,
        explainability: ExplainabilityLogger | None = None,
        governance: GovernanceClient | None = None,
        optimizer: PipelineOptimizer | None = None,
        output_dir: str | Path = "nova/output",
        default_target_repo: str | None = "Spark-Sophia",
    ) -> None:
        self.explainability = explainability or ExplainabilityLogger()
        self.governance = governance
        self.optimizer = optimizer
        self.output_root = Path(output_dir)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.logs_dir = self.output_root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = self.output_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.activity_path = self.reports_dir / "builder_activity.json"
        self.log_path = self.logs_dir / "builder.log"
        self.default_target_repo = default_target_repo

        self.repo_manager = RepoManager(report_dir=self.reports_dir)
        self.code_generator = CodeGenerator(output_dir=self.output_root)
        self.ci_sync = CISync(output_dir=self.output_root)

    # ------------------------------------------------------------------
    def scan_repository(
        self,
        repository: str | Path,
        *,
        include_branches: bool = True,
        include_commits: bool = True,
    ) -> RepositorySnapshot:
        payload = {"repository": str(repository)}
        self._check_governance("repo-update", payload)
        snapshot = self.repo_manager.scan(
            repository,
            include_branches=include_branches,
            include_commits=include_commits,
        )
        report_path = self.repo_manager.write_status_report(snapshot)
        activity = snapshot.to_dict() | {"report_path": str(report_path)}
        self._record_activity("scan_repository", activity)
        self._log("scan_repository", activity)
        self._explain("Scanned repository", evidence=activity)
        return snapshot

    # ------------------------------------------------------------------
    def generate_module(
        self,
        module_name: str,
        *,
        goal: str,
        policy: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        dry_run: bool = False,
    ) -> CodeGenerationReport:
        payload = {"module": module_name, "goal": goal, "dry_run": dry_run}
        self._check_governance("repo-update", payload)
        report = self.code_generator.generate_module(
            module_name,
            goal=goal,
            policy=policy,
            context=context,
            dry_run=dry_run,
        )
        activity = report.to_dict()
        optimizer_report = None
        if self.optimizer is not None and PipelineMetrics is not None:
            metrics = PipelineMetrics(
                build_time_seconds=report.duration_seconds,
                error_rate=0.0 if report.syntax_check_passed else 1.0,
                coverage=0.0,
            )
            optimizer_report = self.optimizer.analyse([metrics])
            activity["optimizer_reward"] = optimizer_report.reward
            activity["optimizer_recommendation"] = optimizer_report.recommendation
        self._record_activity("generate_module", activity)
        self._log("generate_module", activity)
        metadata = {"module": module_name, "dry_run": dry_run}
        if optimizer_report is not None:
            metadata["optimizer_reward"] = optimizer_report.reward
        self._explain("Generated module scaffold", evidence=activity, metadata=metadata)
        return report

    # ------------------------------------------------------------------
    def sync_ci_workflows(
        self,
        *,
        target_repo: str | Path | None = None,
        source_repo: str | Path | None = None,
    ) -> CISyncResult:
        effective_target = target_repo or self.default_target_repo
        payload = {"target_repo": str(effective_target) if effective_target else None}
        self._check_governance("repo-update", payload)
        result = self.ci_sync.sync(target_repo=effective_target, source_repo=source_repo)
        activity = result.to_dict()
        self._record_activity("sync_ci_workflows", activity)
        self._log("sync_ci_workflows", activity)
        self._explain("Synchronized CI workflows", evidence=activity, metadata=payload)
        return result

    # ------------------------------------------------------------------
    def execute(self, task: "PlannedTask", context: Mapping[str, Any]) -> "TaskExecutionResult":
        from ..core.engine import TaskExecutionResult  # local import to avoid circular deps

        action = str(getattr(task.metadata, "get", lambda *_: "scan")("builder_action", "scan"))
        start = time.time()
        output: Dict[str, Any]
        status = "completed"
        try:
            if action == "scan":
                repo = getattr(task.metadata, "get", lambda *_: None)("repository")
                if repo is None:
                    repo = context.get("repository")
                if repo is None:
                    raise ValueError("Repository not specified for builder scan task")
                snapshot = self.scan_repository(repo)
                output = {"snapshot": snapshot.to_dict()}
            elif action == "generate":
                module_name = getattr(task.metadata, "get", lambda *_: None)("module")
                goal = getattr(task.metadata, "get", lambda *_: None)("goal")
                if module_name is None or goal is None:
                    raise ValueError("Module name and goal required for generation task")
                policy = getattr(task.metadata, "get", lambda *_: None)("policy")
                dry_run = bool(getattr(task.metadata, "get", lambda *_: False)("dry_run", False))
                report = self.generate_module(
                    module_name,
                    goal=goal,
                    policy=policy,
                    context=context,
                    dry_run=dry_run,
                )
                output = {"generation": report.to_dict()}
            elif action == "sync-ci":
                repo = getattr(task.metadata, "get", lambda *_: None)("target_repo")
                result = self.sync_ci_workflows(target_repo=repo)
                output = {"ci_sync": result.to_dict()}
            else:
                raise ValueError(f"Unsupported builder action '{action}'")
        except Exception as exc:  # pragma: no cover - error path
            LOGGER.exception("Builder task failed: %s", exc)
            status = "failed"
            output = {"error": str(exc)}
        duration = time.time() - start
        metrics = {"duration_seconds": duration}
        output.setdefault("duration_seconds", duration)
        return TaskExecutionResult(task=task, status=status, output=output, metrics=metrics)

    # ------------------------------------------------------------------
    def _check_governance(self, action: str, payload: Mapping[str, Any]) -> None:
        if self.governance is None:
            return
        decision = self.governance.evaluate_action(action, payload)
        if decision.is_blocking:
            self.explainability.log_decision(
                "builder",
                reason="Governance blocked builder action",
                evidence={"action": action, "payload": dict(payload)},
                impact="blocked",
            )
            raise PermissionError(f"Governance blocked builder action '{action}': {decision.rationale}")
        if decision.is_warning:
            self.explainability.log_decision(
                "builder",
                reason="Governance issued warning for builder action",
                evidence={"action": action, "payload": dict(payload)},
                impact="warning",
            )

    def _record_activity(self, action: str, payload: Mapping[str, Any]) -> None:
        entry = {"timestamp": time.time(), "action": action, "payload": payload}
        if self.activity_path.exists():
            try:
                current = json.loads(self.activity_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                current = []
        else:
            current = []
        current.append(entry)
        self.activity_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    def _log(self, action: str, payload: Mapping[str, Any]) -> None:
        line = json.dumps({"timestamp": time.time(), "action": action, "payload": payload})
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        LOGGER.debug("Builder action logged: %s", action)

    def _explain(
        self,
        reason: str,
        *,
        evidence: Mapping[str, Any],
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.explainability.log_decision(
            "builder",
            reason=reason,
            evidence=dict(evidence),
            impact="repository-update",
            metadata=dict(metadata or {}),
        )


__all__ = ["BuilderAgent"]
