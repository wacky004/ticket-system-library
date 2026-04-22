from __future__ import annotations

from pathlib import Path

import pytest

import app.db.database as db
import app.services.backup as backup


@pytest.fixture()
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    data_dir = tmp_path / "data"
    media_dir = tmp_path / "media"
    attachments_dir = media_dir / "attachments"
    exports_dir = tmp_path / "exports"
    safety_dir = data_dir / "safety_copies"
    db_path = data_dir / "ticket_library.db"
    backup_root = tmp_path / "onedrive_backups"

    backup_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(db, "DATA_DIR", data_dir)
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(db, "ATTACHMENTS_DIR", attachments_dir)
    monkeypatch.setattr(db, "EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(db, "SAFETY_COPIES_DIR", safety_dir)

    monkeypatch.setattr(backup, "DB_PATH", db_path)
    monkeypatch.setattr(backup, "MEDIA_DIR", media_dir)
    monkeypatch.setattr(backup, "ATTACHMENTS_DIR", attachments_dir)
    monkeypatch.setattr(backup, "EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(backup, "SAFETY_COPIES_DIR", safety_dir)

    db.initialize_database()
    db.set_app_setting("onedrive_backup_path", str(backup_root), "path")

    return {
        "tmp": tmp_path,
        "data_dir": data_dir,
        "db_path": db_path,
        "media_dir": media_dir,
        "attachments_dir": attachments_dir,
        "exports_dir": exports_dir,
        "safety_dir": safety_dir,
        "backup_root": backup_root,
    }
