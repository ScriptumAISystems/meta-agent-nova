"""CI/CD workflow synchronisation for the builder agent."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

LOGGER = logging.getLogger("nova.builder.ci")

_REQUIRED_WORKFLOWS = {
    "build.yml": "Ensures application build succeeds",
    "qa.yml": "Runs quality assurance checks",
    "release.yml": "Publishes tagged releases",
}


@dataclass(slots=True)
class CISyncResult:
    """Outcome of a workflow synchronisation pass."""

    target_repo: str | None
    workflow_differences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    missing_workflows: List[str] = field(default_factory=list)
    python_versions: Dict[str, str] = field(default_factory=dict)
    gpu_checks_missing: List[str] = field(default_factory=list)
    release_tagging_missing: List[str] = field(default_factory=list)
    suggestions_path: Path | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_repo": self.target_repo,
            "workflow_differences": self.workflow_differences,
            "missing_workflows": list(self.missing_workflows),
            "python_versions": dict(self.python_versions),
            "gpu_checks_missing": list(self.gpu_checks_missing),
            "release_tagging_missing": list(self.release_tagging_missing),
            "suggestions_path": str(self.suggestions_path) if self.suggestions_path else None,
        }


class CISync:
    """Identifies and resolves drift across CI/CD workflows."""

    def __init__(
        self,
        *,
        output_dir: str | Path = "nova/output",
        reference_repo: str | Path | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pr_suggestions_dir = self.output_dir / "pr_suggestions"
        self.pr_suggestions_dir.mkdir(parents=True, exist_ok=True)
        self.reference_repo = Path(reference_repo).resolve() if reference_repo else None

    # ------------------------------------------------------------------
    def sync(
        self,
        *,
        target_repo: str | Path | None,
        source_repo: str | Path | None = None,
    ) -> CISyncResult:
        """Analyse workflows and produce a harmonisation plan."""

        source = self._resolve_repo(source_repo) if source_repo else self.reference_repo
        target = self._resolve_repo(target_repo) if target_repo else None
        result = CISyncResult(target_repo=str(target) if target else None)
        if target is None:
            LOGGER.info("No target repository provided for CI synchronisation")
            return result

        source_workflows = self._collect_workflows(source) if source else {}
        target_workflows = self._collect_workflows(target)
        result.missing_workflows = [name for name in _REQUIRED_WORKFLOWS if name not in target_workflows]
        result.workflow_differences = self._compare_workflows(source_workflows, target_workflows)
        result.python_versions = {
            name: self._extract_python_version(content)
            for name, content in target_workflows.items()
        }
        result.gpu_checks_missing = [
            name for name, content in target_workflows.items() if not self._has_gpu_stage(content)
        ]
        result.release_tagging_missing = [
            name for name, content in target_workflows.items() if not self._has_release_tagging(content)
        ]
        result.suggestions_path = self._write_suggestions(result)
        LOGGER.info("CI synchronisation completed for %s", target)
        return result

    # ------------------------------------------------------------------
    def _collect_workflows(self, repo_path: Path) -> Dict[str, str]:
        workflows_dir = repo_path / ".github" / "workflows"
        files: Dict[str, str] = {}
        if not workflows_dir.is_dir():
            LOGGER.debug("No workflows directory at %s", workflows_dir)
            return files
        for file in workflows_dir.glob("*.yml"):
            try:
                files[file.name] = file.read_text(encoding="utf-8")
            except OSError as exc:  # pragma: no cover - filesystem errors
                LOGGER.warning("Failed to read workflow %s: %s", file, exc)
        return files

    def _compare_workflows(
        self,
        source: Mapping[str, str],
        target: Mapping[str, str],
    ) -> Dict[str, Dict[str, Any]]:
        differences: Dict[str, Dict[str, Any]] = {}
        for name, content in target.items():
            source_content = source.get(name) if source else None
            if source_content is None:
                continue
            if source_content == content:
                continue
            differences[name] = {
                "summary": "Workflow diverges from reference",
                "source_hash": hash(source_content),
                "target_hash": hash(content),
            }
        return differences

    def _extract_python_version(self, content: str) -> str:
        match = re.search(r"python-version:\s*['\"]?([0-9.]+)", content)
        return match.group(1) if match else "unknown"

    def _has_gpu_stage(self, content: str) -> bool:
        return "gpu" in content.lower() or "cuda" in content.lower()

    def _has_release_tagging(self, content: str) -> bool:
        return "tag" in content.lower() and "release" in content.lower()

    def _write_suggestions(self, result: CISyncResult) -> Path:
        suggestions = {
            "target_repo": result.target_repo,
            "missing_workflows": result.missing_workflows,
            "python_versions": result.python_versions,
            "gpu_checks_missing": result.gpu_checks_missing,
            "release_tagging_missing": result.release_tagging_missing,
            "workflow_differences": result.workflow_differences,
        }
        filename = f"ci_sync_{(result.target_repo or 'unknown').replace('/', '_')}.json"
        path = self.pr_suggestions_dir / filename
        with path.open("w", encoding="utf-8") as handle:
            json.dump(suggestions, handle, indent=2)
        return path

    def _resolve_repo(self, repo: str | Path | None) -> Path | None:
        if repo is None:
            return None
        candidate = Path(repo)
        if candidate.is_dir():
            return candidate.resolve()
        raise FileNotFoundError(f"Repository '{repo}' could not be resolved for CI sync")


__all__ = ["CISync", "CISyncResult"]
