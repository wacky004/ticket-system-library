"""Application bootstrap module."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config import APP_NAME
from app.db.database import initialize_database
from app.ui.main_window import MainWindow
from app.ui.theme import ThemeMode, build_stylesheet


def run() -> int:
    """Start the desktop application."""
    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(build_stylesheet(ThemeMode.DARK))

    window = MainWindow()
    window.show()
    return app.exec()
