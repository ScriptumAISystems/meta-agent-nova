"""Backup and recovery planning utilities for Nova."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List


@dataclass(slots=True)
class BackupPlan:
    """Structured representation of a backup & recovery rollout."""

    identifier: str
    title: str
    summary: str
    scope: List[str] = field(default_factory=list)
    backup_jobs: List[str] = field(default_factory=list)
    recovery_drills: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    retention_policies: List[str] = field(default_factory=list)
    automation_hooks: List[str] = field(default_factory=list)
    integration_notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render the plan as a Markdown document."""

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

        render_section("Schutzumfang & Ziele", self.scope)
        render_section("Backup-Jobs", self.backup_jobs)
        render_section("Recovery-Übungen", self.recovery_drills)
        render_section("Validierung & Überwachung", self.validation_steps)
        render_section("Aufbewahrung & Compliance", self.retention_policies)
        render_section("Automatisierung & Integration", self.automation_hooks)
        render_section("Nova-spezifische Hinweise", self.integration_notes)

        return "\n".join(lines).strip()


def _default_backup_plan() -> BackupPlan:
    summary = (
        "Standardisierter Backup- und Wiederherstellungsplan für die Spark-Sophia-"
        "Umgebung. Der Plan deckt Systemkonfigurationen, Datenbanken, Modellartefakte"
        " und Arbeitsdaten ab und koppelt die Ergebnisse mit Novas Reporting." 
    )

    scope = [
        "Wöchentliche Voll-Backups für Konfigurationsdateien (DGX, Kubernetes, VPN).",
        "Tägliche inkrementelle Sicherungen der produktiven Datenbanken (MongoDB, PostgreSQL).",
        "Snapshots der Vector-Datenbank sowie LLM-Checkpoints (NeMo/finetuning).",
        "Recovery Time Objective (RTO): < 2 Stunden für kritische Services.",
        "Recovery Point Objective (RPO): <= 15 Minuten für Transaktionsdaten.",
    ]

    backup_jobs = [
        "Konfigurations-Archive via `tar` in verschlüsseltem Object Storage (S3/MinIO) ablegen.",
        "Datenbank-Dumps automatisieren: `pg_dump` & `mongodump` inkl. Zeitstempel und Hash-Prüfsumme.",
        "Vector-Store Snapshots exportieren (`faiss`-Index oder Pinecone Snapshot) und mit Metadaten katalogisieren.",
        "LLM-Artefakte (Tokenizer, Adapter, LoRA-Gewichte) versionieren und in Artefakt-Registry replizieren.",
        "Backup-Logs nach `orchestration_journal/backups/` spiegeln und in `python -m nova alerts` einbinden.",
    ]

    recovery_drills = [
        "Monatlicher Restore-Test auf isolierter Staging-Umgebung (inkl. Kubernetes-Namespace).",
        "Desaster-Szenario simulieren: Datenbank-Restore + LLM-Neustart mit dokumentiertem Zeitstempel.",
        "Netzwerk- und VPN-Konfigurationen aus Backup wiederherstellen und Tunnel-Konnektivität prüfen.",
        "Rollback-Plan für fehlgeschlagene Deployments dokumentieren (GitOps/Helm Releases).",
    ]

    validation_steps = [
        "Checksummen-Vergleich (`sha256sum`) nach jedem Backup-Lauf.",
        "`python -m nova monitor`-KPIs erweitern: Backup-Dauer, Datenvolumen, letzte erfolgreiche Ausführung.",
        "Alert-Workflow mit `python -m nova alerts --dry-run` testen (Warnung bei >24h ohne Backup).",
        "Automatisierte Benachrichtigung an Security-Team bei fehlgeschlagenen Jobs.",
    ]

    retention_policies = [
        "7 tägliche Inkrementals, 4 wöchentliche Voll-Backups, 12 Monatsarchive.",
        "Revisionssichere Ablage (WORM) für Compliance-relevante Daten (DSGVO/ISO 27001).",
        "Löschkonzept für personenbezogene Daten dokumentieren und jährlich überprüfen.",
    ]

    automation_hooks = [
        "Backup-Jobs via `cron` oder Argo Workflows orchestrieren; Status in Nova Task Queue spiegeln.",
        "CI/CD-Pipeline erweitert fehlgeschlagene Backups um automatische Ticket-Erstellung.",
        "Secrets (S3 Credentials, DB-User) im Vault verwalten und Rotation halbjährlich erzwingen.",
    ]

    integration_notes = [
        "Ergebnisse im Orchestrierungstagebuch unter `orchestration_journal/backups/` versionieren.",
        "Status der Aufgabenliste (`Agenten_Aufgaben_Uebersicht.csv`) nach erfolgreichem Drill aktualisieren.",
        "Definition-of-Done für Nova in `docs/DEFINITION_OF_DONE.md` abhaken, sobald Restore-Probe erfolgreich.",
    ]

    return BackupPlan(
        identifier="default",
        title="Default Backup & Recovery Plan",
        summary=summary,
        scope=scope,
        backup_jobs=backup_jobs,
        recovery_drills=recovery_drills,
        validation_steps=validation_steps,
        retention_policies=retention_policies,
        automation_hooks=automation_hooks,
        integration_notes=integration_notes,
    )


_PLAN_BUILDERS: dict[str, Callable[[], BackupPlan]] = {
    "default": _default_backup_plan,
}


def list_available_backup_plans() -> list[str]:
    """Return the identifiers of available backup plans."""

    return sorted(_PLAN_BUILDERS)


def build_backup_plan(plan_name: str) -> BackupPlan:
    """Return the backup plan for ``plan_name``."""

    if not plan_name:
        raise ValueError("plan_name must be provided")

    key = plan_name.strip().lower()
    builder = _PLAN_BUILDERS.get(key)
    if builder is None:
        available = ", ".join(sorted(_PLAN_BUILDERS))
        raise ValueError(
            f"Unsupported backup plan: {plan_name}. Available plans: {available}"
        )
    return builder()


def export_backup_plan(plan: BackupPlan, path: Path) -> Path:
    """Persist ``plan`` as Markdown and return the written path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.to_markdown() + "\n", encoding="utf-8")
    return path


__all__ = [
    "BackupPlan",
    "build_backup_plan",
    "export_backup_plan",
    "list_available_backup_plans",
]
