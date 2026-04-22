"""Backups page for manual backup, status, and restore workflows."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from app.db.database import get_last_backup_log, list_backup_logs
from app.services.backup import (
    create_backup,
    get_configured_backup_root,
    list_backups,
    restore_backup,
)


class BackupsPage(QWidget):
    """Backup/restore operational page."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PageRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        title = QLabel("Backups")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Manual backup and restore for OneDrive backup folders.")
        subtitle.setObjectName("PageSubtitle")

        info_card = QFrame()
        info_card.setObjectName("Card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(6)

        self.destination_label = QLabel("Destination: Not configured")
        self.last_time_label = QLabel("Last Backup Time: -")
        self.last_result_label = QLabel("Result: -")
        self.warning_label = QLabel(
            "Warning: Keep one active computer at a time. OneDrive is backup/restore only."
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setObjectName("MetaLabel")

        info_layout.addWidget(self.destination_label)
        info_layout.addWidget(self.last_time_label)
        info_layout.addWidget(self.last_result_label)
        info_layout.addWidget(self.warning_label)

        action_row = QHBoxLayout()
        self.manual_backup_button = QPushButton("Run Manual Backup")
        self.manual_backup_button.setObjectName("PrimaryButton")
        self.restore_latest_button = QPushButton("Restore Latest Backup")
        self.restore_latest_button.setObjectName("SecondaryButton")
        self.restore_pick_button = QPushButton("Restore From Folder")
        self.restore_pick_button.setObjectName("SecondaryButton")
        self.safety_copy_check = QCheckBox("Create safety copy before restore")
        self.safety_copy_check.setChecked(True)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")

        action_row.addWidget(self.manual_backup_button)
        action_row.addWidget(self.restore_latest_button)
        action_row.addWidget(self.restore_pick_button)
        action_row.addWidget(self.safety_copy_check)
        action_row.addStretch(1)
        action_row.addWidget(self.refresh_button)

        logs_card = QFrame()
        logs_card.setObjectName("Card")
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(12, 12, 12, 12)
        logs_layout.setSpacing(8)
        logs_layout.addWidget(QLabel("Recent Backup Logs"))

        self.logs_table = QTableWidget(0, 5)
        self.logs_table.setHorizontalHeaderLabels(["Started", "Status", "Type", "Destination", "Notes"])
        self.logs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.logs_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setAlternatingRowColors(True)
        logs_layout.addWidget(self.logs_table)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(info_card)
        root.addLayout(action_row)
        root.addWidget(logs_card, 1)

        self.manual_backup_button.clicked.connect(self._run_manual_backup)
        self.restore_latest_button.clicked.connect(self._restore_latest)
        self.restore_pick_button.clicked.connect(self._restore_pick)
        self.refresh_button.clicked.connect(self.refresh_data)

        self.refresh_data()

    def refresh_data(self) -> None:
        configured = get_configured_backup_root()
        self.destination_label.setText(
            f"Destination: {configured}" if configured else "Destination: Not configured"
        )

        last = get_last_backup_log()
        if last:
            self.last_time_label.setText(f"Last Backup Time: {last.get('completed_at') or last.get('started_at')}")
            self.last_result_label.setText(f"Result: {last.get('status')} | {last.get('backup_path')}")
        else:
            self.last_time_label.setText("Last Backup Time: -")
            self.last_result_label.setText("Result: -")

        logs = list_backup_logs(limit=40)
        self.logs_table.setRowCount(0)
        for index, row in enumerate(logs):
            self.logs_table.insertRow(index)
            values = [
                row.get("started_at") or "",
                row.get("status") or "",
                row.get("backup_type") or "",
                row.get("backup_path") or "",
                row.get("notes") or "",
            ]
            for col, value in enumerate(values):
                self.logs_table.setItem(index, col, QTableWidgetItem(str(value)))
        self.logs_table.resizeColumnsToContents()

    def _run_manual_backup(self) -> None:
        try:
            result = create_backup(backup_type="manual")
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", f"Backup failed.\n\n{exc}")
            return
        QMessageBox.information(self, "Backup Complete", f"Backup created at:\n{result['destination']}")
        self.refresh_data()

    def _restore_latest(self) -> None:
        backups = list_backups()
        if not backups:
            QMessageBox.warning(self, "No Backups", "No backup folders found.")
            return
        self._run_restore(Path(str(backups[0]["path"])))

    def _restore_pick(self) -> None:
        start = str(get_configured_backup_root() or Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder", start)
        if not folder:
            return
        self._run_restore(Path(folder))

    def _run_restore(self, backup_folder: Path) -> None:
        confirm = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Restore from backup folder?\n{backup_folder}",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            result = restore_backup(backup_folder, create_safety=self.safety_copy_check.isChecked())
        except Exception as exc:
            QMessageBox.critical(self, "Restore Failed", f"Restore failed.\n\n{exc}")
            return
        QMessageBox.information(
            self,
            "Restore Complete",
            f"Restored from:\n{result['restored_from']}\nSafety copy: {result.get('safety_copy') or 'none'}",
        )
        self.refresh_data()
