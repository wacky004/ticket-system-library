"""Settings page for appearance, paths, and defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db.database import get_app_setting, set_app_setting
from app.services.backup import (
    get_auto_backup_on_exit,
    get_configured_backup_root,
    set_auto_backup_on_exit,
    set_configured_backup_root,
    validate_backup_root,
)


class SettingsPage(QWidget):
    """Application settings module."""

    def __init__(self, on_theme_changed: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.setObjectName("PageRoot")
        self._on_theme_changed = on_theme_changed

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Appearance, defaults, and backup/export preferences.")
        subtitle.setObjectName("PageSubtitle")

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.theme_mode_input = QComboBox()
        self.theme_mode_input.addItems(["dark", "light"])

        self.backup_path_input = QLineEdit()
        self.backup_path_input.setReadOnly(True)
        backup_browse_btn = QPushButton("Browse")
        backup_browse_btn.setObjectName("SecondaryButton")
        backup_validate_btn = QPushButton("Validate")
        backup_validate_btn.setObjectName("SecondaryButton")
        backup_row = QHBoxLayout()
        backup_row.addWidget(self.backup_path_input, 1)
        backup_row.addWidget(backup_browse_btn)
        backup_row.addWidget(backup_validate_btn)

        self.auto_backup_check = QCheckBox("Enable backup when app closes")

        self.export_path_input = QLineEdit()
        self.export_path_input.setReadOnly(True)
        export_browse_btn = QPushButton("Browse")
        export_browse_btn.setObjectName("SecondaryButton")
        export_row = QHBoxLayout()
        export_row.addWidget(self.export_path_input, 1)
        export_row.addWidget(export_browse_btn)

        self.ticket_prefix_input = QLineEdit()
        self.ticket_prefix_input.setPlaceholderText("TKT")

        self.company_name_input = QLineEdit()
        self.display_name_input = QLineEdit()

        form.addRow("App Theme", self.theme_mode_input)
        form.addRow("OneDrive Backup Path", backup_row)
        form.addRow("Auto Backup On Close", self.auto_backup_check)
        form.addRow("Default Export Folder", export_row)
        form.addRow("Ticket ID Prefix", self.ticket_prefix_input)
        form.addRow("Company Name", self.company_name_input)
        form.addRow("Display Name", self.display_name_input)

        warning = QLabel(
            "Warning: OneDrive is for backup/restore only. Keep one active computer at a time. "
            "Directly running live SQLite from OneDrive sync is risky."
        )
        warning.setWordWrap(True)
        warning.setObjectName("MetaLabel")

        actions = QHBoxLayout()
        actions.addStretch(1)
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("PrimaryButton")
        actions.addWidget(save_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("MetaLabel")

        card_layout.addLayout(form)
        card_layout.addWidget(warning)
        card_layout.addLayout(actions)
        card_layout.addWidget(self.status_label)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addStretch(1)

        backup_browse_btn.clicked.connect(self._browse_backup_path)
        backup_validate_btn.clicked.connect(self._validate_backup_path)
        export_browse_btn.clicked.connect(self._browse_export_path)
        save_btn.clicked.connect(self._save_settings)

        self.load_settings()

    def load_settings(self) -> None:
        theme = (get_app_setting("theme_mode") or "dark").lower()
        self.theme_mode_input.setCurrentText("light" if theme == "light" else "dark")

        backup_path = get_configured_backup_root()
        self.backup_path_input.setText(str(backup_path) if backup_path else "")

        self.auto_backup_check.setChecked(get_auto_backup_on_exit())

        self.export_path_input.setText(get_app_setting("export_directory") or "")
        self.ticket_prefix_input.setText(get_app_setting("ticket_id_prefix") or "TKT")
        self.company_name_input.setText(get_app_setting("company_name") or "Ticket Library")
        self.display_name_input.setText(get_app_setting("display_name") or "Support User")

    def _browse_backup_path(self) -> None:
        current = self.backup_path_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select OneDrive Backup Folder", current)
        if folder:
            self.backup_path_input.setText(folder)

    def _validate_backup_path(self) -> None:
        path = self.backup_path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation", "Please choose a backup folder first.")
            return
        ok, message = validate_backup_root(path)
        if ok:
            QMessageBox.information(self, "Validation", message)
        else:
            QMessageBox.warning(self, "Validation", message)

    def _browse_export_path(self) -> None:
        current = self.export_path_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder", current)
        if folder:
            self.export_path_input.setText(str(Path(folder).resolve()))

    def _save_settings(self) -> None:
        backup_path = self.backup_path_input.text().strip()
        if backup_path:
            ok, message = validate_backup_root(backup_path)
            if not ok:
                QMessageBox.warning(self, "Invalid Backup Path", message)
                return
            set_configured_backup_root(backup_path)
        else:
            set_app_setting("onedrive_backup_path", "", "path")

        export_path = self.export_path_input.text().strip()
        if export_path:
            export_dir = Path(export_path).expanduser().resolve()
            export_dir.mkdir(parents=True, exist_ok=True)
            set_app_setting("export_directory", str(export_dir), "path")

        prefix = self.ticket_prefix_input.text().strip().upper()
        cleaned_prefix = "".join(ch for ch in prefix if ch.isalnum())[:10] or "TKT"
        set_app_setting("ticket_id_prefix", cleaned_prefix, "string")

        company_name = self.company_name_input.text().strip() or "Ticket Library"
        display_name = self.display_name_input.text().strip() or "Support User"
        set_app_setting("company_name", company_name, "string")
        set_app_setting("display_name", display_name, "string")

        theme_mode = self.theme_mode_input.currentText().strip().lower()
        set_app_setting("theme_mode", "light" if theme_mode == "light" else "dark", "string")
        set_auto_backup_on_exit(self.auto_backup_check.isChecked())

        if self._on_theme_changed:
            self._on_theme_changed(theme_mode)

        self.status_label.setText("Settings saved.")
        QMessageBox.information(self, "Settings", "Settings saved successfully.")
