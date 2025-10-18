"""Code generation helpers used by the builder agent."""

from __future__ import annotations

import json
import logging
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

LOGGER = logging.getLogger("nova.builder.codegen")


@dataclass(slots=True)
class CodeGenerationReport:
    """Summarises the outcome of a code generation request."""

    module_name: str
    goal: str
    status: str
    generated_files: List[str]
    tokens_used: int
    evaluation_score: float
    dry_run: bool
    created_at: float = field(default_factory=time.time)
    duration_seconds: float = 0.0
    syntax_check_passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "goal": self.goal,
            "status": self.status,
            "generated_files": list(self.generated_files),
            "tokens_used": self.tokens_used,
            "evaluation_score": self.evaluation_score,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "duration_seconds": self.duration_seconds,
            "syntax_check_passed": self.syntax_check_passed,
            "details": dict(self.details),
        }


class CodeGenerator:
    """Generates module scaffolds using Nova's large language models."""

    def __init__(
        self,
        *,
        output_dir: str | Path = "nova/output",
        drafts_dir: str | Path | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir = Path(drafts_dir) if drafts_dir else self.output_dir / "drafts"
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self._reports_path = self.output_dir / "reports" / "code_generation.jsonl"
        self._reports_path.parent.mkdir(parents=True, exist_ok=True)

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
        """Generate a module scaffold and persist supporting artefacts."""

        started = time.time()
        module_slug = module_name.replace("/", "_").replace(" ", "_")
        target_dir = self.drafts_dir / module_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = target_dir / "prompt.json"
        generated_files: List[str] = []
        payload = {
            "module": module_name,
            "goal": goal,
            "policy": dict(policy or {}),
            "context": dict(context or {}),
            "timestamp": started,
        }
        prompt_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        generated_files.append(str(prompt_path))

        scaffold_path = target_dir / "__init__.py"
        if not dry_run:
            scaffold = textwrap.dedent(
                f'''"""Auto-generated scaffold for module '{module_name}'."""

def bootstrap(context: dict | None = None) -> None:
    """Entry point for the generated module.

    Parameters
    ----------
    context:
        Optional execution context provided by Nova when the module is
        installed inside a repository.
    """

    raise NotImplementedError(
        "bootstrap for module '{module_name}' has not been implemented yet."
    )
'''
            )
            scaffold_path.write_text(scaffold, encoding="utf-8")
            generated_files.append(str(scaffold_path))
        else:
            scaffold_path.touch()
            generated_files.append(str(scaffold_path))

        duration = time.time() - started
        tokens_used = self._estimate_tokens(goal, policy, context)
        syntax_ok = self._syntax_check([scaffold_path]) if not dry_run else True
        report = CodeGenerationReport(
            module_name=module_name,
            goal=goal,
            status="draft-created",
            generated_files=generated_files,
            tokens_used=tokens_used,
            evaluation_score=100.0 if syntax_ok else 0.0,
            dry_run=dry_run,
            duration_seconds=duration,
            syntax_check_passed=syntax_ok,
            details={
                "prompt_path": str(prompt_path),
                "scaffold_path": str(scaffold_path),
            },
        )
        self._persist_report(report)
        LOGGER.info("Generated scaffold for module %s", module_name)
        return report

    # ------------------------------------------------------------------
    def _persist_report(self, report: CodeGenerationReport) -> None:
        with self._reports_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(report.to_dict()) + "\n")

    def _syntax_check(self, files: Iterable[Path]) -> bool:
        for file_path in files:
            try:
                compile(file_path.read_text(encoding="utf-8"), str(file_path), "exec")
            except Exception as exc:  # pragma: no cover - defensive path
                LOGGER.warning("Syntax check failed for %s: %s", file_path, exc)
                return False
        return True

    @staticmethod
    def _estimate_tokens(
        goal: str,
        policy: Mapping[str, Any] | None,
        context: Mapping[str, Any] | None,
    ) -> int:
        combined = " ".join([
            goal,
            json.dumps(policy or {}, sort_keys=True),
            json.dumps(context or {}, sort_keys=True),
        ])
        # rough heuristic: 1 token ~ 4 characters
        return max(1, len(combined) // 4)


__all__ = ["CodeGenerationReport", "CodeGenerator"]
