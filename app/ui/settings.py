"""Settings page for backup configuration and safety controls."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from app.services.backup import (
    get_auto_backup_on_exit,
    get_configured_backup_root,
    set_auto_backup_on_exit,
    set_configured_backup_root,
    validate_backup_root,
)


class SettingsPage(QWidget):
    """Application settings page."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PageRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Configure OneDrive backup destination and backup safety behavior.")
        subtitle.setObjectName("PageSubtitle")

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        folder_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("Select OneDrive backup folder")
        browse_button = QPushButton("Browse")
        browse_button.setObjectName("SecondaryButton")
        validate_button = QPushButton("Validate")
        validate_button.setObjectName("SecondaryButton")
        save_button = QPushButton("Save")
        save_button.setObjectName("PrimaryButton")

        folder_row.addWidget(self.path_input, 1)
        folder_row.addWidget(browse_button)
        folder_row.addWidget(validate_button)
        folder_row.addWidget(save_button)

        self.auto_backup_check = QCheckBox("Automatic backup on app exit")
        self.auto_backup_check.setChecked(get_auto_backup_on_exit())

        warning = QLabel(
            "Warning: OneDrive is for backup/restore only. Keep one active computer at a time. "
            "Running live SQLite directly from OneDrive sync can corrupt data."
        )
        warning.setWordWrap(True)
        warning.setObjectName("MetaLabel")

        self.status_label = QLabel("")
        self.status_label.setObjectName("MetaLabel")

        card_layout.addWidget(QLabel("OneDrive Backup Folder"))
        card_layout.addLayout(folder_row)
        card_layout.addWidget(self.auto_backup_check)
        card_layout.addWidget(warning)
        card_layout.addWidget(self.status_label)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(card)
        root.addStretch(1)

        browse_button.clicked.connect(self._browse_folder)
        validate_button.clicked.connect(self._validate_path)
        save_button.clicked.connect(self._save_settings)

        configured = get_configured_backup_root()
        if configured:
            self.path_input.setText(str(configured))

    def _browse_folder(self) -> None:
        current = self.path_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select OneDrive Backup Folder", current)
        if folder:
            self.path_input.setText(folder)

    def _validate_path(self) -> None:
        path = self.path_input.text().strip()
        if not path:
            QMessageBox.warning(self, "Validation", "Please choose a backup folder first.")
            return
        ok, message = validate_backup_root(path)
        if ok:
            QMessageBox.information(self, "Validation", message)
        else:
            QMessageBox.warning(self, "Validation", message)

    def _save_settings(self) -> None:
        path = self.path_input.text().strip()
        if path:
            ok, message = validate_backup_root(path)
            if not ok:
                QMessageBox.warning(self, "Invalid Folder", message)
                return
            saved = set_configured_backup_root(path)
            self.path_input.setText(str(saved))

        set_auto_backup_on_exit(self.auto_backup_check.isChecked())
        self.status_label.setText("Settings saved.")
