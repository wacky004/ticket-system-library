"""Backup and restore services for local <-> OneDrive workflows."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import (
    APP_SETTINGS_EXPORT_NAME,
    ATTACHMENTS_DIR,
    BACKUP_MANIFEST_NAME,
    DB_PATH,
    EXPORTS_DIR,
    MEDIA_DIR,
    SAFETY_COPIES_DIR,
)
from app.db.database import (
    complete_backup_log,
    get_app_setting,
    list_app_settings,
    set_app_setting,
    start_backup_log,
)


def get_configured_backup_root() -> Path | None:
    value = get_app_setting("onedrive_backup_path")
    if not value:
        return None
    return Path(value)


def set_configured_backup_root(path_value: str) -> Path:
    resolved = Path(path_value).expanduser().resolve()
    set_app_setting("onedrive_backup_path", str(resolved), "path")
    return resolved


def get_auto_backup_on_exit() -> bool:
    value = get_app_setting("auto_backup_on_exit")
    return value == "1"


def set_auto_backup_on_exit(enabled: bool) -> None:
    set_app_setting("auto_backup_on_exit", "1" if enabled else "0", "bool")


def validate_backup_root(path_value: str | Path) -> tuple[bool, str]:
    path = Path(path_value)
    if not path.exists():
        return False, "Backup path does not exist."
    if not path.is_dir():
        return False, "Backup path is not a folder."
    return True, "Path is valid."


def create_backup(backup_type: str = "manual") -> dict[str, Any]:
    backup_root = get_configured_backup_root()
    if backup_root is None:
        raise ValueError("OneDrive backup folder is not configured.")

    ok, message = validate_backup_root(backup_root)
    if not ok:
        raise ValueError(message)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ticket_library_backup_{timestamp}"
    destination = backup_root / backup_name

    log_id = start_backup_log(backup_name, str(destination), backup_type)
    try:
        destination.mkdir(parents=True, exist_ok=False)

        db_target = destination / DB_PATH.name
        _backup_sqlite(DB_PATH, db_target)

        media_target = destination / "media"
        if MEDIA_DIR.exists():
            shutil.copytree(MEDIA_DIR, media_target)
        else:
            media_target.mkdir(parents=True, exist_ok=True)

        settings_target = destination / APP_SETTINGS_EXPORT_NAME
        settings_payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "settings": list_app_settings(),
        }
        settings_target.write_text(json.dumps(settings_payload, indent=2), encoding="utf-8")

        manifest = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backup_name": backup_name,
            "database_file": db_target.name,
            "media_dir": "media",
            "settings_file": APP_SETTINGS_EXPORT_NAME,
            "local_db_mtime": _safe_mtime(DB_PATH),
            "local_media_mtime": _latest_mtime(MEDIA_DIR),
            "paths": {
                "db_path": str(db_target),
                "media_path": str(media_target),
                "exports_path": str(EXPORTS_DIR),
                "attachments_path": str(ATTACHMENTS_DIR),
            },
            "warning": "Use backup/restore only. Do not run live SQLite directly from OneDrive sync folder.",
        }
        (destination / BACKUP_MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        backup_size = _directory_size(destination)
        complete_backup_log(log_id, "success", backup_size=backup_size, notes=None)
        return {
            "name": backup_name,
            "destination": str(destination),
            "size": backup_size,
        }
    except Exception as exc:
        complete_backup_log(log_id, "failed", backup_size=None, notes=str(exc))
        raise


def list_backups(backup_root: Path | None = None) -> list[dict[str, Any]]:
    root = backup_root or get_configured_backup_root()
    if root is None or not root.exists() or not root.is_dir():
        return []

    backups: list[dict[str, Any]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        manifest_path = child / BACKUP_MANIFEST_NAME
        db_path = child / DB_PATH.name
        if not db_path.exists():
            continue

        created_at = _safe_mtime(child)
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                created_at = str(manifest.get("created_at") or created_at)
            except Exception:
                pass

        backups.append(
            {
                "path": str(child),
                "name": child.name,
                "created_at": created_at,
                "manifest": manifest,
            }
        )

    backups.sort(key=lambda b: str(b.get("created_at", "")), reverse=True)
    return backups


def latest_backup() -> dict[str, Any] | None:
    backups = list_backups()
    return backups[0] if backups else None


def local_data_timestamp() -> str:
    db_ts = _safe_mtime(DB_PATH)
    media_ts = _latest_mtime(MEDIA_DIR)
    return max(db_ts, media_ts)


def backup_is_newer_than_local(backup_info: dict[str, Any]) -> bool:
    backup_ts = str(backup_info.get("created_at") or "")
    local_ts = local_data_timestamp()
    return backup_ts > local_ts


def create_safety_copy(label: str = "pre_restore") -> Path:
    SAFETY_COPIES_DIR.mkdir(parents=True, exist_ok=True)
    target = SAFETY_COPIES_DIR / f"{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    target.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        shutil.copy2(DB_PATH, target / DB_PATH.name)
    if MEDIA_DIR.exists():
        shutil.copytree(MEDIA_DIR, target / "media")
    return target


def restore_backup(backup_path: str | Path, create_safety: bool = False) -> dict[str, Any]:
    source = Path(backup_path)
    db_source = source / DB_PATH.name
    media_source = source / "media"
    if not db_source.exists():
        raise ValueError("Backup database file not found.")

    safety_path: Path | None = None
    if create_safety:
        safety_path = create_safety_copy()

    db_tmp = DB_PATH.with_suffix(".restore_tmp")
    media_old = MEDIA_DIR.with_name(f"media_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    media_swapped = False
    try:
        db_tmp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_source, db_tmp)

        if MEDIA_DIR.exists():
            MEDIA_DIR.rename(media_old)
            media_swapped = True

        if media_source.exists():
            shutil.copytree(media_source, MEDIA_DIR)
        else:
            MEDIA_DIR.mkdir(parents=True, exist_ok=True)

        db_tmp.replace(DB_PATH)

        if media_swapped and media_old.exists():
            shutil.rmtree(media_old, ignore_errors=True)

        return {
            "restored_from": str(source),
            "safety_copy": str(safety_path) if safety_path else None,
        }
    except Exception:
        if db_tmp.exists():
            db_tmp.unlink(missing_ok=True)
        if media_swapped and media_old.exists():
            if MEDIA_DIR.exists():
                shutil.rmtree(MEDIA_DIR, ignore_errors=True)
            media_old.rename(MEDIA_DIR)
        raise


def _safe_mtime(path: Path) -> str:
    if not path.exists():
        return "1970-01-01 00:00:00"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def _latest_mtime(path: Path) -> str:
    if not path.exists():
        return "1970-01-01 00:00:00"
    latest = path.stat().st_mtime
    for file_path in path.rglob("*"):
        if file_path.is_file():
            latest = max(latest, file_path.stat().st_mtime)
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S")


def _directory_size(path: Path) -> int:
    total = 0
    for file_path in path.rglob("*"):
        if file_path.is_file():
            total += file_path.stat().st_size
    return total


def _backup_sqlite(source_path: Path, destination_path: Path) -> None:
    source_conn = sqlite3.connect(source_path)
    dest_conn = sqlite3.connect(destination_path)
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()
