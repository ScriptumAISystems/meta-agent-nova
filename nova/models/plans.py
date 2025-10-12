"""Structured model planning artifacts for Orion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List


@dataclass(slots=True)
class ModelPlan:
    """Represents a structured rollout plan for model operations."""

    identifier: str
    title: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    data_preparation: List[str] = field(default_factory=list)
    infrastructure: List[str] = field(default_factory=list)
    training_pipeline: List[str] = field(default_factory=list)
    evaluation: List[str] = field(default_factory=list)
    risk_mitigation: List[str] = field(default_factory=list)
    handover: List[str] = field(default_factory=list)

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

        render_section("Ziele & Erfolgskriterien", self.objectives)
        render_section("Datenaufbereitung & Governance", self.data_preparation)
        render_section("Infrastruktur & Tooling", self.infrastructure)
        render_section("Trainingspipeline", self.training_pipeline)
        render_section("Evaluierung & Qualitätssicherung", self.evaluation)
        render_section("Risiken & Gegenmaßnahmen", self.risk_mitigation)
        render_section("Übergabe & Automatisierung", self.handover)

        return "\n".join(lines).strip()


def _finetune_plan() -> ModelPlan:
    summary = (
        "Standardisierte LoRA/PEFT-Finetuning-Pipeline für Sophia inklusive Daten-"
        "Governance, Infrastruktur und Übergabe an Betriebsteams."
    )

    objectives = [
        "Lieferung eines reproduzierbaren Finetuning-Playbooks für Orion inkl. GPU- und CPU-Fallback.",
        "Dokumentierter Pfad von Datenaufnahme bis Modellübergabe mit klaren KPIs (BLEU, ROUGE, Win-Rate).",
        "Verankerung der Aufgaben in Novas Task- und Monitoring-Ökosystem (Alerts, Backups, Journale).",
    ]

    data_preparation = [
        "Domänenspezifische Korpora inventarisieren (Dialoge, SOPs, Wissensartikel) inklusive Eigentümer & Klassifizierung.",
        "Anonymisierung & DSGVO-Konformität sicherstellen; Freigaben in `orchestration_journal/data/consent_log.md` protokollieren.",
        "Annotation-Guidelines definieren (Richtlinien, Quality-Gates, Review-Kadenz).",
        "Datenaufteilung festlegen (Train/Val/Test ≥ 70/15/15) und Seed-Management dokumentieren.",
    ]

    infrastructure = [
        "NeMo & Abhängigkeiten in isolierter Umgebung bereitstellen (`nemo`, `pytorch`, `transformers`).",
        "DGX GPU-Profile vorbereiten (CUDA Toolkit, TensorRT-LLM) und CPU-Fallback via vLLM oder HF-Inference beschreiben.",
        "Artefakt-Registry und Weights-Speicher (`models/finetune/`) mit Versionsschema einrichten.",
        "Überwachungshooks für Trainingsjobs in `python -m nova monitor` aufnehmen (Laufzeit, GPU-Auslastung, Fehler).",
    ]

    training_pipeline = [
        "Baseline-Modell auswählen (z. B. Llama 3 8B Instruct) und Hyperparameter-Tabelle bereitstellen.",
        "LoRA/PEFT-Konfiguration in YAML-Schablone erfassen (`config/finetune/lora.yaml`).",
        "Trainingsskript skizzieren (`scripts/finetune_nemo.py`) inkl. Resume/Checkpoint-Handling.",
        "Experiment-Tracking (Weights & Biases oder MLflow) mit Namenskonvention `sophia-finetune-<datum>` definieren.",
        "Deployment-Pipeline vorbereiten (Helm/Terraform) für aktualisierte Adapter-Gewichte.",
    ]

    evaluation = [
        "Evaluationsdatensätze kuratieren (Szenario-Dialoge, Edge-Cases) und Referenzantworten festlegen.",
        "Automatisierte Metriken (BLEU ≥ 35, ROUGE-L ≥ 0.4, Win-Rate ≥ 65 %) konfigurieren.",
        "Human-in-the-loop Review-Panel etablieren; Feedback in `orchestration_journal/models/finetune_reviews.md` sammeln.",
        "Regressionstests gegen Basismodell durchführen; Abweichungen dokumentieren und bei Bedarf Rollback initiieren.",
    ]

    risk_mitigation = [
        "Data-Leakage-Prüfungen (Prompt-Leaks, PII) mit Security-Team abstimmen und Findings triagieren.",
        "Fallback-Strategie definieren: Basismodell + Safety-Layer aktivieren, wenn KPIs unterschritten werden.",
        "Kosten- und Laufzeitbudget monitoren; Schwellenwerte in `python -m nova alerts --dry-run` testen.",
        "Compliance-Review (Lizenz, Exportkontrollen) vor Go-Live dokumentieren.",
    ]

    handover = [
        "Trainingslog, Configs und Adapter-Gewichte unter `orchestration_journal/models/` versionieren.",
        "Runbook für Deployment und Rollback (`orchestration_journal/models/finetune_runbook.md`) erstellen.",
        "Agenten-Aufgabenliste aktualisieren (Status → Abgeschlossen) und Stakeholder informieren.",
        "Lessons Learned & nächste Iterationen in `progress_report.md` bzw. Nova CLI (`python -m nova summary`) spiegeln.",
    ]

    return ModelPlan(
        identifier="finetune",
        title="Sophia Finetuning Playbook",
        summary=summary,
        objectives=objectives,
        data_preparation=data_preparation,
        infrastructure=infrastructure,
        training_pipeline=training_pipeline,
        evaluation=evaluation,
        risk_mitigation=risk_mitigation,
        handover=handover,
    )


_PLAN_BUILDERS: dict[str, Callable[[], ModelPlan]] = {
    "finetune": _finetune_plan,
}


def list_available_model_plans() -> list[str]:
    """Return identifiers of the available model plans."""

    return sorted(_PLAN_BUILDERS)


def build_model_plan(plan_name: str) -> ModelPlan:
    """Build the model plan associated with ``plan_name``."""

    if not plan_name:
        raise ValueError("plan_name must be provided")

    key = plan_name.strip().lower()
    builder = _PLAN_BUILDERS.get(key)
    if builder is None:
        available = ", ".join(sorted(_PLAN_BUILDERS))
        raise ValueError(
            f"Unsupported model plan: {plan_name}. Available plans: {available}"
        )
    return builder()


def export_model_plan(plan: ModelPlan, path: Path) -> Path:
    """Persist ``plan`` as Markdown and return the written path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.to_markdown() + "\n", encoding="utf-8")
    return path


__all__ = [
    "ModelPlan",
    "build_model_plan",
    "export_model_plan",
    "list_available_model_plans",
]
