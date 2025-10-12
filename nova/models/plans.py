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


def _nemo_installation_plan() -> ModelPlan:
    summary = (
        "Installations-Playbook für NVIDIA NeMo inklusive Abhängigkeitsmanagement, "
        "Validierungsschritten und Übergabe an den Betrieb."
    )

    objectives = [
        "GPU- und CPU-kompatible Installationspfade für NeMo bereitstellen (Container & venv).",
        "Sicherstellen, dass Lizenz- und Compliance-Anforderungen dokumentiert und freigegeben sind.",
        "Smoke-Tests automatisieren, damit Orion & Chronos die Umgebung reproduzierbar verifizieren können.",
    ]

    data_preparation = [
        "Hardware-Voraussetzungen erfassen (GPU Generation, CUDA-Version, Treiberstand).",
        "Kompatibilitätsmatrix für PyTorch, CUDA, cuDNN und TensorRT pflegen.",
        "Offline-Mirror (Wheel-Cache oder Container Registry) für air-gapped Deployments vorbereiten.",
    ]

    infrastructure = [
        "Container-Image (`nvcr.io/nvidia/nemo:latest`) referenzieren und Pull-Prüfung dokumentieren.",
        "Alternativ: Python Virtualenv mit `pip install nemo_toolkit[all]` + `onnxruntime-gpu` beschreiben.",
        "Monitoring Hooks (DCGM Exporter, nvidia-smi Logs) in Betriebskonzept aufnehmen.",
    ]

    training_pipeline = [
        "Smoke-Test Notebook (NLP + ASR) unter `notebooks/nemo_smoke_test.ipynb` anlegen.",
        "CLI-Skript `python -m nova models --plan finetune` als Folgeaufgabe verlinken.",
        "Resource-Quotas definieren (GPU Memory, Disk) und in `deploy/automation/bridge/.env` spiegeln.",
    ]

    evaluation = [
        "`pytest -k nemo` Workflow in CI integrieren (Mock Tests ohne GPU).",
        "Validierungslog `orchestration_journal/models/nemo_validation.md` führen.",
        "Kompatibilitätstests für Mehrsprachigkeit & Mixed Precision dokumentieren.",
    ]

    risk_mitigation = [
        "Fallback auf CPU-Build dokumentieren (`nemo_toolkit[asr]` + `onnxruntime`).",
        "Security-Bulletins von NVIDIA beobachten und Hotfix-Pfade festhalten.",
        "Lizenzbedingungen (NVIDIA AI Enterprise) prüfen und in Governance-Archiv ablegen.",
    ]

    handover = [
        "Installationsprotokoll im `orchestration_journal/models/nemo_installation.md` aktualisieren.",
        "Operations Runbook (`docs/MODEL_OPERATIONS_KICKOFF.md`) mit finalen Parametern ergänzen.",
        "Ticket in Service-Now/Jira für Go-Live-Abnahme anstoßen.",
    ]

    return ModelPlan(
        identifier="nemo-installation",
        title="NVIDIA NeMo Installationsleitfaden",
        summary=summary,
        objectives=objectives,
        data_preparation=data_preparation,
        infrastructure=infrastructure,
        training_pipeline=training_pipeline,
        evaluation=evaluation,
        risk_mitigation=risk_mitigation,
        handover=handover,
    )


def _llm_selection_plan() -> ModelPlan:
    summary = (
        "Entscheidungsmatrix und Bereitstellungsplan für Sophias Basismodell inklusive Governance-Checks."
    )

    objectives = [
        "Transparente Bewertung von mindestens drei LLM-Kandidaten (Lizenz, Kontextfenster, Kosten).",
        "Proof-of-Concept-Bereitstellung (HF Inference Endpoint oder TensorRT-LLM) sicherstellen.",
        "Integration in Monitoring und Sicherheitsrichtlinien vorbereiten (Audit Logging, Access Control).",
    ]

    data_preparation = [
        "Eval-Datensätze definieren (Dialoge, Compliance, Eskalationen).",
        "Prompt-Guidelines und Guardrails (Safety Prompts, Moderation) aufnehmen.",
        "Legal/Procurement-Review für Lizenzbedingungen dokumentieren.",
    ]

    infrastructure = [
        "Deployment-Optionen vergleichen: Managed (Azure OpenAI, AWS Bedrock) vs. Self-Hosted (DGX).",
        "Helm/Compose-Manifest in `deploy/models/<candidate>/` vorbereiten.",
        "Observability (latency, token-usage) mit Prometheus/Grafana koppeln.",
    ]

    training_pipeline = [
        "Baseline-Benchmarks durchführen (`python -m nova benchmarks --profile llm-core`).",
        "Red Teaming-Scenarios definieren und in QA-Plan aufnehmen.",
        "Vorbereitung für Adapter/LoRA-Anbindung dokumentieren (Kompatibilität).",
    ]

    evaluation = [
        "Bewertungstabelle `orchestration_journal/models/llm_selection_matrix.md` pflegen.",
        "KPI-Katalog (Latenz, Win-Rate, Kosten) mit Aura abstimmen.",
        "Stakeholder-Review (Product, Legal, Security) einholen und protokollieren.",
    ]

    risk_mitigation = [
        "Fallback-Modell definieren (z. B. Mixtral 8x7B) mit reduzierten Ressourcen.",
        "Exit-Strategie bei Lizenzänderungen oder API-Limits beschreiben.",
        "Datenschutz-Folgenabschätzung (DSFA) dokumentieren, falls Cloud-Anbieter im Spiel sind.",
    ]

    handover = [
        "Decision Log in `docs/MODEL_OPERATIONS_KICKOFF.md` ergänzen.",
        "`Agenten_Aufgaben_Uebersicht.csv` aktualisieren (Status → Abgeschlossen) nach Freigabe.",
        "Monitoring & Alerts für gewähltes Modell aktivieren (`python -m nova alerts`).",
    ]

    return ModelPlan(
        identifier="llm-selection",
        title="Sophia LLM Auswahl- und Bereitstellungsplan",
        summary=summary,
        objectives=objectives,
        data_preparation=data_preparation,
        infrastructure=infrastructure,
        training_pipeline=training_pipeline,
        evaluation=evaluation,
        risk_mitigation=risk_mitigation,
        handover=handover,
    )


def _langchain_integration_plan() -> ModelPlan:
    summary = (
        "Integrationsfahrplan, um LangChain in Novas Orchestrierungslandschaft einzubetten und mit n8n zu koppeln."
    )

    objectives = [
        "Standardisierte Schnittstelle zwischen LangChain und Nova-Agents etablieren.",
        "n8n-Workflows triggern, überwachen und rückkoppeln (Data Flywheel).",
        "Security- und Observability-Guidelines für orchestrierte Agenten festschreiben.",
    ]

    data_preparation = [
        "Prompts/Tools katalogisieren (Knowledge Retrieval, Ticketing, Monitoring).",
        "Secrets-Management für LangChain (API Keys, Webhook Tokens) in Vault dokumentieren.",
        "Testdaten für Chain-Validierung definieren (Happy Path & Edge Cases).",
    ]

    infrastructure = [
        "FastAPI-Bridge (`nova/automation/bridge.py`) erweitern und Deployment in `deploy/automation/bridge/` synchronisieren.",
        "LangChain Execution Environment (Python Env oder Container) mit Dependencies versehen.",
        "n8n Webhook-Konfigurationen versionieren (`orchestration_journal/automation/n8n_sample_workflow.json`).",
    ]

    training_pipeline = [
        "Test-Suite für Chains definieren (`pytest -k chain` Ziel).",
        "Observability-Hooks (Structured Logging, Trace IDs) implementieren.",
        "Fallback-Pfade skizzieren, wenn externe Services (LLM, Vector Store) nicht verfügbar sind.",
    ]

    evaluation = [
        "Integrationstest-Szenarien dokumentieren (`orchestration_journal/automation/langchain_bridge.md`).",
        "Latency- und Erfolgsmetriken erfassen; KPIs im LUX-Dashboard visualisieren.",
        "Security-Review für Token-Handling und Rate Limiting durchführen.",
    ]

    risk_mitigation = [
        "Circuit Breaker & Retry-Strategien beschreiben (Tenacity, Resilienz-Patterns).",
        "Audit-Logging aktivieren, damit Chronos Änderungen nachvollziehen kann.",
        "Incident-Playbook für Ausfälle und Fehlkonfigurationen bereitstellen.",
    ]

    handover = [
        "Developer-Handbuch `orchestration_journal/automation/langchain_bridge.md` erweitern.",
        "n8n Admins & DevOps in Knowledge-Transfer-Session schulen.",
        "Definition-of-Done für LangChain Integration im Governance-Doc abhaken.",
    ]

    return ModelPlan(
        identifier="langchain-integration",
        title="LangChain Integrationsfahrplan",
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
    "nemo-installation": _nemo_installation_plan,
    "llm-selection": _llm_selection_plan,
    "langchain-integration": _langchain_integration_plan,
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
