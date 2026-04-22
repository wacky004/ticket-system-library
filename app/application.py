"""Application bootstrap module."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import APP_NAME
from app.db.database import has_any_tickets, initialize_database
from app.services.backup import (
    backup_is_newer_than_local,
    get_configured_backup_root,
    latest_backup,
    restore_backup,
)
from app.ui.main_window import MainWindow
from app.ui.theme import ThemeMode, build_stylesheet


def run() -> int:
    """Start the desktop application."""
    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(build_stylesheet(ThemeMode.DARK))

    _handle_startup_backup_prompt()

    window = MainWindow()
    window.show()
    return app.exec()


def _handle_startup_backup_prompt() -> None:
    configured_root = get_configured_backup_root()
    if configured_root is None:
        return

    backup = latest_backup()
    if backup is None:
        return

    local_empty = not has_any_tickets()
    newer = backup_is_newer_than_local(backup)
    if not newer and not local_empty:
        return

    message = QMessageBox()
    message.setIcon(QMessageBox.Icon.Warning)
    message.setWindowTitle("Backup Restore Check")
    message.setText(
        "A backup was detected and appears newer than local data, or this computer looks like a fresh setup."
    )
    message.setInformativeText(
        "Choose restore behavior:\n"
        "- Restore Backup: overwrite local data with backup\n"
        "- Keep Local: continue using local data\n"
        "- Safety Copy + Restore: create local safety snapshot first, then restore\n\n"
        "Important: Use one active computer at a time. Running live SQLite directly from OneDrive sync is risky."
    )
    restore_button = message.addButton("Restore Backup", QMessageBox.ButtonRole.AcceptRole)
    keep_button = message.addButton("Keep Local", QMessageBox.ButtonRole.RejectRole)
    safe_restore_button = message.addButton("Safety Copy + Restore", QMessageBox.ButtonRole.DestructiveRole)
    message.setDefaultButton(safe_restore_button)
    message.exec()

    clicked = message.clickedButton()
    if clicked == keep_button:
        return

    create_safety = clicked == safe_restore_button
    if clicked in {restore_button, safe_restore_button}:
        try:
            restore_backup(str(backup["path"]), create_safety=create_safety)
            initialize_database()
            QMessageBox.information(
                None,
                "Restore Complete",
                "Backup restored successfully. Local data has been refreshed.",
            )
        except Exception as exc:  # pragma: no cover - UI guard
            QMessageBox.critical(None, "Restore Failed", f"Restore failed.\n\n{exc}")
