"""Backup and recovery automation helpers for Nova."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..monitoring.logging import log_info, log_warning


@dataclass(slots=True)
class BackupSnapshot:
    """Metadata describing a backup snapshot."""

    timestamp: str
    location: Path
    artifacts: List[Path]

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "location": str(self.location),
            "artifacts": [str(path) for path in self.artifacts],
        }


class BackupManager:
    """Simple orchestrator for periodic Nova backups."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.backup_dir = base_path / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = base_path / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_backup(self) -> BackupSnapshot:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        snapshot_dir = self.backup_dir / timestamp
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        artifacts = [
            snapshot_dir / "postgres.sql",
            snapshot_dir / "vector-store.snapshot",
        ]
        artifacts[0].write_text("-- simulated pg_dump output --\n", encoding="utf-8")
        artifacts[1].write_text("{\"vectors\": []}\n", encoding="utf-8")
        summary = BackupSnapshot(timestamp=timestamp, location=snapshot_dir, artifacts=artifacts)
        self._write_summary(summary)
        log_info(f"Backup snapshot created at {snapshot_dir}")
        return summary

    def restore(self, timestamp: str) -> Path:
        snapshot_dir = self.backup_dir / timestamp
        if not snapshot_dir.exists():
            raise FileNotFoundError(f"Snapshot {timestamp} not found under {self.backup_dir}")
        marker = snapshot_dir / "restore.log"
        marker.write_text(
            json.dumps({"restored_at": datetime.utcnow().isoformat()}),
            encoding="utf-8",
        )
        log_info(f"Restore marker written to {marker}")
        return marker

    def list_snapshots(self) -> List[BackupSnapshot]:
        snapshots: List[BackupSnapshot] = []
        for directory in sorted(self.backup_dir.iterdir()):
            if not directory.is_dir():
                continue
            timestamp = directory.name
            artifacts = list(directory.glob("*"))
            snapshots.append(BackupSnapshot(timestamp=timestamp, location=directory, artifacts=artifacts))
        return snapshots

    def _write_summary(self, snapshot: BackupSnapshot) -> None:
        report_path = self.reports_dir / "weekly_backup_summary.md"
        existing = []
        if report_path.exists():
            existing.append(report_path.read_text(encoding="utf-8"))
        header = "# Weekly Backup Summary\n\n" if not existing else ""
        entry_lines = [
            f"## Snapshot {snapshot.timestamp}",
            f"- Location: {snapshot.location}",
            "- Artifacts:",
        ]
        entry_lines.extend(f"  - {artifact.name}" for artifact in snapshot.artifacts)
        entry_lines.append("")
        report_path.write_text(header + "\n".join(existing + ["\n".join(entry_lines)]), encoding="utf-8")
        journal = self.base_path / "logs" / "backups.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        with journal.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot.to_dict()) + "\n")


def run_backup(base_path: Path) -> BackupSnapshot:
    """Execute a backup and return the produced snapshot metadata."""

    manager = BackupManager(base_path)
    return manager.run_backup()


def restore_backup(base_path: Path, timestamp: str) -> Path:
    """Restore a snapshot identified by ``timestamp``."""

    manager = BackupManager(base_path)
    return manager.restore(timestamp)


def ensure_weekly_backup(base_path: Path) -> Optional[BackupSnapshot]:
    """Ensure that at least one snapshot exists for the current ISO week."""

    manager = BackupManager(base_path)
    snapshots = manager.list_snapshots()
    current_week = datetime.utcnow().isocalendar()[:2]
    for snapshot in snapshots:
        snapshot_week = datetime.strptime(snapshot.timestamp, "%Y%m%d%H%M%S").isocalendar()[:2]
        if snapshot_week == current_week:
            return None
    log_warning("No backup found for current week; creating one automatically.")
    return manager.run_backup()


__all__ = [
    "BackupManager",
    "BackupSnapshot",
    "ensure_weekly_backup",
    "restore_backup",
    "run_backup",
]
