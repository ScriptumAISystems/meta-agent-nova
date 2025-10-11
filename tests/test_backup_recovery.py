from pathlib import Path

from nova.security.backup_recovery import BackupManager, ensure_weekly_backup


def test_backup_manager_creates_snapshot(tmp_path: Path) -> None:
    manager = BackupManager(tmp_path)
    snapshot = manager.run_backup()
    assert snapshot.location.exists()
    for artifact in snapshot.artifacts:
        assert artifact.exists()
    restored = manager.restore(snapshot.timestamp)
    assert restored.exists()


def test_ensure_weekly_backup(tmp_path: Path) -> None:
    manager = BackupManager(tmp_path)
    manager.run_backup()
    result = ensure_weekly_backup(tmp_path)
    assert result is None or result.location.exists()
