"""Data service blueprints for Lumina's responsibilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from lumina import DeploymentPlan, install_mongodb, install_postgresql, setup_vector_db


@dataclass(slots=True)
class ServiceSection:
    """Represents a concrete service slice in the data blueprint."""

    category: str
    title: str
    description: str
    plan: DeploymentPlan
    hardening: Sequence[str] = field(default_factory=list)
    follow_up: Sequence[str] = field(default_factory=list)

    def _render_plan_steps(self) -> list[str]:
        lines: list[str] = []
        if self.plan.steps:
            lines.append("**Deployment-Schritte**")
            for index, step in enumerate(self.plan.steps, start=1):
                lines.append(
                    f"{index}. `{step.command}` – {step.description}"
                )
            lines.append("")
        if self.plan.configuration:
            lines.append("**Konfigurationsempfehlungen**")
            for key, value in self.plan.configuration.items():
                lines.append(f"- `{key}` → {value}")
            lines.append("")
        if self.plan.verification:
            lines.append("**Validierung**")
            for command in self.plan.verification:
                lines.append(f"- `{command}`")
            lines.append("")
        if self.hardening:
            lines.append("**Hardening & Betriebstipps**")
            for item in self.hardening:
                lines.append(f"- {item}")
            lines.append("")
        if self.follow_up:
            lines.append("**Follow-up / Ownership**")
            for item in self.follow_up:
                lines.append(f"- {item}")
            lines.append("")
        return lines

    def to_markdown_lines(self) -> list[str]:
        lines = [f"### {self.title}", "", self.description, ""]
        lines.extend(self._render_plan_steps())
        return [line for line in lines if line is not None]


@dataclass(slots=True)
class DataBlueprint:
    """Structured blueprint for Lumina's data services."""

    identifier: str
    title: str
    summary: str
    services: Sequence[ServiceSection] = field(default_factory=list)
    operations: Sequence[str] = field(default_factory=list)
    handover: Sequence[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines: list[str] = [f"# {self.title}", "", "## Zusammenfassung", self.summary, ""]

        current_category: str | None = None
        for section in self.services:
            if section.category != current_category:
                current_category = section.category
                lines.append(f"## {current_category}")
                lines.append("")
            lines.extend(section.to_markdown_lines())

        if self.operations:
            lines.append("## Betrieb & Automatisierung")
            lines.append("")
            for item in self.operations:
                lines.append(f"- {item}")
            lines.append("")

        if self.handover:
            lines.append("## Übergabe & Dokumentation")
            lines.append("")
            for item in self.handover:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines).strip()


def _build_core_blueprint() -> DataBlueprint:
    mongodb_plan = install_mongodb()
    postgres_plan = install_postgresql()
    pinecone_plan = setup_vector_db("pinecone")
    faiss_plan = setup_vector_db("faiss")

    services: list[ServiceSection] = [
        ServiceSection(
            category="Relationale Datenbanken",
            title="MongoDB Cluster (Ops Ready)",
            description=(
                "Bereitet die MongoDB-Umgebung für Sophia vor und stellt sicher, dass Replica-Set "
                "und Netzwerk-Vorgaben dokumentiert sind."
            ),
            plan=mongodb_plan,
            hardening=[
                "Enable TLS/SSL and enforce SCRAM-SHA auth before produktivem Go-Live.",
                "Konfiguriere Backup-Targets (`python -m nova backup --plan data`) nach dem ersten Health-Check.",
            ],
            follow_up=[
                "Operations-Team informiert, wenn Replica-Set initialisiert wurde (`rs.initiate()`).",
                "Firewall-Regeln für Ports 27017/27018 mit Security abstimmen.",
            ],
        ),
        ServiceSection(
            category="Relationale Datenbanken",
            title="PostgreSQL Service (SOP)",
            description=(
                "Installiert PostgreSQL inkl. Basis-Konfiguration und stellt Prüfschritte für Zugänge bereit."
            ),
            plan=postgres_plan,
            hardening=[
                "Aktiviere `pg_hba.conf`-Restriktionen (nur VPN/VPC) und erzwinge Passwortrotation.",
                "Plane PITR-Backups über `pg_basebackup` oder WAL-G shipping ein.",
            ],
            follow_up=[
                "`sophia`-Role in Secrets-Management aufnehmen und mit DevOps teilen.",
                "Schema-Migrationspfad (Alembic/Flyway) mit Chronos abstimmen.",
            ],
        ),
        ServiceSection(
            category="Vector Knowledge Base",
            title="Pinecone (Managed Option)",
            description=(
                "Managed Vektorservice für schnelle Produktions-Reife. Enthält Credential-Setup und Index-Provisionierung."
            ),
            plan=pinecone_plan,
            hardening=[
                "API-Keys im Secrets-Store (1Password/Vault) hinterlegen und Rotation halbjährlich planen.",
                "Traffic-Monitoring via Pinecone Usage Dashboard aktivieren und Kosten-Limits definieren.",
            ],
            follow_up=[
                "Data-Ingestion-Pipeline (Chronos) auf Index `sophia-embeddings` zeigen lassen.",
                "Service-Kontrakt (SLA/Limits) mit Procurement und Legal dokumentieren.",
            ],
        ),
        ServiceSection(
            category="Vector Knowledge Base",
            title="FAISS (Self-Hosted Option)",
            description=(
                "On-Premise Alternative inklusive Build-Schritte und Testaufrufen für CPU-basierte Experimente."
            ),
            plan=faiss_plan,
            hardening=[
                "Index-Dateien verschlüsselt speichern (LUKS/eCryptfs) und Backup-Strategie definieren.",
                "GPU-Beschleunigung evaluieren, sobald DGX Spark verfügbar ist (CUDA Faiss-Paket).",
            ],
            follow_up=[
                "CI-Pipeline erweitern, um Index-Build Smoke-Tests auszuführen.",
                "Zugriffspfade (POSIX ACLs) für Data-Science-Team dokumentieren.",
            ],
        ),
    ]

    operations = [
        "Registriere Health-Checks (MongoDB/PostgreSQL) in `python -m nova monitor` für Availability-Alerts.",
        "Synchronisiere Backup-Zeitpläne mit Nova (`python -m nova backup --plan data --export ...`).",
        "Verknüpfe Vector-Store-Latenzen mit dem LUX-Dashboard (Aura) für Experience-KPIs.",
    ]

    handover = [
        "Exportiere dieses Blueprint nach `orchestration_journal/data/core_blueprint.md` und teile es mit Lumina/Chronos.",
        "Aktualisiere `Agenten_Aufgaben_Uebersicht.csv` sobald MongoDB/PostgreSQL Provisionierung abgeschlossen ist.",
        "Dokumentiere Zugangsdaten & Netzwerkpfade im `orchestration_journal/data/`-Verzeichnis.",
    ]

    summary = (
        "Bündelt die vorbereitenden Arbeiten für Datenbanken und Vektor-Store, damit Lumina die Plattform vor dem "
        "DGX-Spark-Go-Live stabilisieren kann."
    )

    return DataBlueprint(
        identifier="core",
        title="Sophia Data Core Blueprint",
        summary=summary,
        services=services,
        operations=operations,
        handover=handover,
    )


_BLUEPRINT_BUILDERS: dict[str, Callable[[], DataBlueprint]] = {
    "core": _build_core_blueprint
}


def list_available_data_blueprints() -> list[str]:
    """Return identifiers of available data blueprints."""

    return sorted(_BLUEPRINT_BUILDERS)


def build_data_blueprint(name: str) -> DataBlueprint:
    """Build the data blueprint associated with ``name``."""

    if not name:
        raise ValueError("Blueprint name must be provided")
    key = name.strip().lower()
    builder = _BLUEPRINT_BUILDERS.get(key)
    if builder is None:
        available = ", ".join(sorted(_BLUEPRINT_BUILDERS)) or "<keine>"
        raise ValueError(
            f"Unsupported data blueprint: {name}. Available blueprints: {available}"
        )
    return builder()


def export_data_blueprint(blueprint: DataBlueprint, path: Path) -> Path:
    """Persist ``blueprint`` as Markdown and return the written path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(blueprint.to_markdown() + "\n", encoding="utf-8")
    return path


__all__ = [
    "DataBlueprint",
    "ServiceSection",
    "build_data_blueprint",
    "export_data_blueprint",
    "list_available_data_blueprints",
]
