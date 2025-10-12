"""Planning blueprints for LLM fine-tuning and deployment."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List


@dataclass(slots=True)
class ModelPlan:
    """Structured description of an LLM preparation or fine-tuning workflow."""

    identifier: str
    title: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    data_preparation: List[str] = field(default_factory=list)
    training_pipeline: List[str] = field(default_factory=list)
    evaluation: List[str] = field(default_factory=list)
    deployment: List[str] = field(default_factory=list)
    automation: List[str] = field(default_factory=list)
    governance: List[str] = field(default_factory=list)
    handover: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render the model plan as a Markdown document."""

        lines: list[str] = [f"# {self.title}", ""]
        lines.append("## Zusammenfassung")
        lines.append(self.summary)
        lines.append("")

        def render_section(title: str, items: Iterable[str]) -> None:
            entries = list(items)
            if not entries:
                return
            lines.append(f"## {title}")
            for entry in entries:
                lines.append(f"- {entry}")
            lines.append("")

        render_section("Ziele", self.objectives)
        render_section("Voraussetzungen", self.prerequisites)
        render_section("Datenvorbereitung", self.data_preparation)
        render_section("Fine-Tuning Pipeline", self.training_pipeline)
        render_section("Evaluierung", self.evaluation)
        render_section("Deployment", self.deployment)
        render_section("Automatisierung & Monitoring", self.automation)
        render_section("Governance & Compliance", self.governance)
        render_section("Übergabe & Dokumentation", self.handover)
        render_section("Referenzen", self.references)

        return "\n".join(lines).strip()


def _finetune_model_plan() -> ModelPlan:
    summary = (
        "End-to-end Plan für das Fine-Tuning eines LLM mit NVIDIA NeMo auf der DGX "
        "Spark Umgebung. Der Fokus liegt auf reproduzierbaren Pipelines, klaren "
        "KPIs und einer sauberen Übergabe an Betrieb und Sicherheit."
    )

    objectives = [
        "LLM-Auswahl (z. B. Llama 3) validieren und auf Sophia-Anforderungen zuschneiden.",
        "NVIDIA NeMo Trainings- und Evaluationsprofile vorbereiten (GPU-optimiert).",
        "Mehrstufige Evaluierung mit Sicherheits- und Qualitätsmetriken etablieren.",
        "Bereitstellung für Inferenz (TensorRT- oder Triton-Inferenzpfad) vorbereiten.",
    ]

    prerequisites = [
        "GPU-fähige Umgebung mit CUDA 12.x, PyTorch 2.x und NeMo >= 2.0.",
        "Zugriff auf Trainingsdaten (Dialoge, Wissensbasis, Sicherheitsregeln).",
        "Definierte Metriken: Genauigkeit, Antwortlatenz, Halluzinationsquote.",
        "Abgestimmter Security-Review (Policy Engine & Audit Logging aktiv).",
    ]

    data_preparation = [
        "Datensichtung & Klassifizierung gemäß `docs/DEFINITION_OF_DONE.md`.",
        "Preprocessing-Pipeline in `notebooks/` oder `nova/data` als Referenz implementieren.",
        "Sensitive Inhalte anonymisieren, DSGVO/Lizenzcheck dokumentieren.",
        "Datasets versionieren (DVC/Git-LFS) und Metadaten im Orchestrierungsjournal ablegen.",
    ]

    training_pipeline = [
        "Baseline-Notebook oder CLI-Skript `python -m nova models --plan finetune` als Template nutzen.",
        "NeMo Experiment konfigurieren: Optimizer, Scheduler, Mixed Precision (AMP/O2).",
        "Checkpoint-Speicherung nach jeder Epoche (s3:// oder NFS) + Delta-Adapter (LoRA/QLoRA).",
        "Monitoring Hooks integrieren (`nova.monitoring.kpi.KPITracker`) zur Laufzeitüberwachung.",
        "Automatisierte Smoke-Tests nach jedem Training (Testruns in `tests/test_models_*`).",
    ]

    evaluation = [
        "Validierung gegen Golden-Set (Sicherheitsfragen, Unternehmenswissen).",
        "Toxicity & Bias Checks (NeMo Guardrails, OpenAI evals) dokumentieren.",
        "Regressionstests mit `python -m nova monitor --optimize` für Performance-Benchmarks.",
        "Akzeptanzkriterien in `docs/NOVA_DEFINITION_OF_DONE.md` abhaken.",
    ]

    deployment = [
        "Export des angepassten Modells (ONNX/TensorRT) für den Serving-Stack vorbereiten.",
        "Triton Inference Server oder Riva Deployment YAML erstellen und versionieren.",
        "CI/CD-Integration (GitHub Actions → Kubernetes Namespace `sophia-llm`).",
        "Rollback-Strategie definieren (letzter stabiler Checkpoint, Canary Traffic).",
    ]

    automation = [
        "Trainings- und Evaluationsjobs via Argo Workflows oder Airflow orchestrieren.",
        "Alerting in `python -m nova alerts` einspeisen (z. B. Stalls, GPU Overcommit).",
        "Nightly Smoke-Tests per `python -m nova summary --limit 5` protokollieren.",
        "KPIs an Grafana Dashboard (`docs/LUX_DASHBOARD.md`) anbinden.",
    ]

    governance = [
        "Lizenz- und Nutzungsbedingungen für Basis-LLM dokumentieren.",
        "Security Sign-off mit `python -m nova audit --policies enabled` einholen.",
        "Datenherkunft & Consent in `orchestration_journal/compliance/` archivieren.",
        "Responsible-AI-Kontrollen (Bias, Explainability) überprüfen.",
    ]

    handover = [
        "Runbook für Betriebsteam (Start/Stop, Scaling, Incident Response) verfassen.",
        "Checkliste in `Agenten_Aufgaben_Uebersicht.csv` aktualisieren (Orion & Chronos).",
        "Lessons Learned & Benchmarks im `progress_report.md` ergänzen.",
        "Abnahme-Workshop mit Stakeholdern (Produkt, Security, Data) durchführen.",
    ]

    references = [
        "NVIDIA NeMo Framework Doku: https://docs.nvidia.com/nemo-framework/",
        "Llama 3 Model Card & Lizenzhinweise.",
        "Nova Monitoring Alerts: `python -m nova alerts --dry-run --export ...`.",
        "DGX Vorbereitungsplan: `docs/DGX_PRE_ARRIVAL_PLAN.md`.",
    ]

    return ModelPlan(
        identifier="finetune",
        title="Finetuning-Plan für Sophia LLM",
        summary=summary,
        objectives=objectives,
        prerequisites=prerequisites,
        data_preparation=data_preparation,
        training_pipeline=training_pipeline,
        evaluation=evaluation,
        deployment=deployment,
        automation=automation,
        governance=governance,
        handover=handover,
        references=references,
    )


_PLAN_BUILDERS: dict[str, Callable[[], ModelPlan]] = {
    "finetune": _finetune_model_plan,
}


def list_available_model_plans() -> list[str]:
    """Return all available model plan identifiers."""

    return sorted(_PLAN_BUILDERS)


def build_model_plan(plan_name: str) -> ModelPlan:
    """Construct the requested model plan."""

    if not plan_name:
        raise ValueError("plan_name must be provided")
    key = plan_name.strip().lower()
    builder = _PLAN_BUILDERS.get(key)
    if builder is None:
        available = ", ".join(sorted(_PLAN_BUILDERS))
        raise ValueError(f"Unsupported model plan: {plan_name}. Available plans: {available}")
    return builder()


def export_model_plan(plan: ModelPlan, path: Path) -> Path:
    """Write ``plan`` to ``path`` as Markdown and return the absolute path."""

    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(plan.to_markdown() + "\n", encoding="utf-8")
    return resolved


__all__ = [
    "ModelPlan",
    "build_model_plan",
    "export_model_plan",
    "list_available_model_plans",
]
