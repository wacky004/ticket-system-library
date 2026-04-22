"""Guides / Knowledge Base UI."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import (
    archive_guide,
    create_guide,
    delete_guide,
    generate_next_guide_id,
    get_guide_by_db_id,
    restore_guide,
    search_guides,
    update_guide,
)
from app.ui.tickets import AttachmentPanel


class GuideFormWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.guide_id_label = QLabel("Auto-generated on save")
        self.guide_id_label.setObjectName("MetaLabel")

        id_row = QHBoxLayout()
        id_row.addWidget(QLabel("Guide ID"))
        id_row.addWidget(self.guide_id_label, 1)
        layout.addLayout(id_row)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.title_input = QLineEdit()
        self.category_input = QLineEdit()
        self.subcategory_input = QLineEdit()
        self.difficulty_input = QLineEdit()
        self.summary_input = QTextEdit()
        self.problem_input = QTextEdit()
        self.installation_input = QTextEdit()
        self.troubleshooting_input = QTextEdit()
        self.solution_input = QTextEdit()
        self.notes_input = QTextEdit()
        self.tags_input = QLineEdit()
        self.related_software_input = QLineEdit()

        for field in (
            self.summary_input,
            self.problem_input,
            self.installation_input,
            self.troubleshooting_input,
            self.solution_input,
            self.notes_input,
        ):
            field.setFixedHeight(78)

        form.addRow("Title *", self.title_input)
        form.addRow("Category", self.category_input)
        form.addRow("Subcategory", self.subcategory_input)
        form.addRow("Difficulty", self.difficulty_input)
        form.addRow("Summary", self.summary_input)
        form.addRow("Problem Description", self.problem_input)
        form.addRow("Installation Steps", self.installation_input)
        form.addRow("Troubleshooting Steps", self.troubleshooting_input)
        form.addRow("Solution Steps", self.solution_input)
        form.addRow("Notes", self.notes_input)
        form.addRow("Tags", self.tags_input)
        form.addRow("Related Software", self.related_software_input)
        layout.addLayout(form)

    def set_guide_preview(self) -> None:
        self.guide_id_label.setText(generate_next_guide_id())

    def load_guide(self, guide: dict[str, Any]) -> None:
        self.guide_id_label.setText(str(guide.get("guide_id") or ""))
        self.title_input.setText(str(guide.get("title") or ""))
        self.category_input.setText(str(guide.get("category") or ""))
        self.subcategory_input.setText(str(guide.get("subcategory") or ""))
        self.difficulty_input.setText(str(guide.get("difficulty") or ""))
        self.summary_input.setPlainText(str(guide.get("summary") or ""))
        self.problem_input.setPlainText(str(guide.get("problem_description") or ""))
        self.installation_input.setPlainText(str(guide.get("installation_steps") or ""))
        self.troubleshooting_input.setPlainText(str(guide.get("troubleshooting_steps") or ""))
        self.solution_input.setPlainText(str(guide.get("solution_steps") or ""))
        self.notes_input.setPlainText(str(guide.get("notes") or ""))
        self.tags_input.setText(str(guide.get("tags_text") or ""))
        self.related_software_input.setText(str(guide.get("related_software") or ""))

    def payload(self) -> dict[str, Any]:
        return {
            "title": self.title_input.text(),
            "category": self.category_input.text(),
            "subcategory": self.subcategory_input.text(),
            "difficulty": self.difficulty_input.text(),
            "summary": self.summary_input.toPlainText(),
            "problem_description": self.problem_input.toPlainText(),
            "installation_steps": self.installation_input.toPlainText(),
            "troubleshooting_steps": self.troubleshooting_input.toPlainText(),
            "solution_steps": self.solution_input.toPlainText(),
            "notes": self.notes_input.toPlainText(),
            "tags_text": self.tags_input.text(),
            "related_software": self.related_software_input.text(),
        }


class GuideDetailDialog(QDialog):
    def __init__(self, guide_db_id: int | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.guide_db_id = guide_db_id
        self.setWindowTitle("Guide Details")
        self.setMinimumSize(900, 740)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.form = GuideFormWidget()
        self.attachments_panel = AttachmentPanel("guide", allow_clipboard=True)

        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setContentsMargins(8, 8, 8, 8)
        details_layout.addWidget(self.form)

        attachments_tab = QWidget()
        attachments_layout = QVBoxLayout(attachments_tab)
        attachments_layout.setContentsMargins(8, 8, 8, 8)
        attachments_layout.addWidget(self.attachments_panel)

        self.tabs.addTab(details_tab, "Details")
        self.tabs.addTab(attachments_tab, "Attachments")

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("SecondaryButton")
        save_button = QPushButton("Save")
        save_button.setObjectName("PrimaryButton")
        actions.addWidget(cancel_button)
        actions.addWidget(save_button)

        layout.addWidget(self.tabs, 1)
        layout.addLayout(actions)

        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self._save)

        if self.guide_db_id is None:
            self.form.set_guide_preview()
            self.attachments_panel.set_parent_record(None)
        else:
            guide = get_guide_by_db_id(self.guide_db_id)
            if guide is not None:
                self.form.load_guide(guide)
            self.attachments_panel.set_parent_record(self.guide_db_id)

    def _save(self) -> None:
        try:
            if self.guide_db_id is None:
                self.guide_db_id = create_guide(self.form.payload())
            else:
                update_guide(self.guide_db_id, self.form.payload())
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", f"Unable to save guide.\n\n{exc}")
            return
        self.accept()


class GuidesPage(QWidget):
    COLUMNS = [
        "ID",
        "Guide ID",
        "Title",
        "Category",
        "Subcategory",
        "Difficulty",
        "Archived",
        "Updated",
    ]

    def __init__(self, on_data_changed: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._on_data_changed = on_data_changed
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        title = QLabel("Guides")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Knowledge Base guides for installation, troubleshooting, and solution workflows.")
        subtitle.setObjectName("PageSubtitle")

        controls = QFrame()
        controls.setObjectName("Card")
        controls_layout = QGridLayout(controls)
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setHorizontalSpacing(8)
        controls_layout.setVerticalSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search guides by id, title, category, tags, and steps...")

        self.new_button = QPushButton("New Guide")
        self.new_button.setObjectName("PrimaryButton")
        self.open_button = QPushButton("Open/Edit")
        self.open_button.setObjectName("SecondaryButton")
        self.archive_button = QPushButton("Archive")
        self.archive_button.setObjectName("SecondaryButton")
        self.restore_button = QPushButton("Restore")
        self.restore_button.setObjectName("SecondaryButton")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("DangerButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")

        controls_layout.addWidget(self.search_input, 0, 0, 1, 6)
        controls_layout.addWidget(self.new_button, 1, 0)
        controls_layout.addWidget(self.open_button, 1, 1)
        controls_layout.addWidget(self.archive_button, 1, 2)
        controls_layout.addWidget(self.restore_button, 1, 3)
        controls_layout.addWidget(self.delete_button, 1, 4)
        controls_layout.addWidget(self.refresh_button, 1, 5)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(controls)
        root.addWidget(self.table, 1)

        self.search_input.textChanged.connect(lambda _text: self.reload_table())
        self.new_button.clicked.connect(self.new_guide)
        self.open_button.clicked.connect(self.open_selected)
        self.archive_button.clicked.connect(self.archive_selected)
        self.restore_button.clicked.connect(self.restore_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.refresh_button.clicked.connect(self.reload_table)
        self.table.cellDoubleClicked.connect(lambda _r, _c: self.open_selected())

        self.reload_table()

    def reload_table(self) -> None:
        guides = search_guides(self.search_input.text(), include_archived=True)
        self.table.setRowCount(0)
        for row_index, guide in enumerate(guides):
            self.table.insertRow(row_index)
            values = [
                str(guide.get("id") or ""),
                str(guide.get("guide_id") or ""),
                str(guide.get("title") or ""),
                str(guide.get("category") or ""),
                str(guide.get("subcategory") or ""),
                str(guide.get("difficulty") or ""),
                "Yes" if int(guide.get("archived") or 0) else "No",
                str(guide.get("updated_at") or ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, int(guide["id"]))
                self.table.setItem(row_index, col, item)
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def new_guide(self) -> None:
        dialog = GuideDetailDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success", "Guide created.")
            self.reload_table()
            if self._on_data_changed:
                self._on_data_changed()

    def open_selected(self) -> None:
        db_id = self._selected_id()
        if db_id is None:
            QMessageBox.information(self, "No Selection", "Select a guide first.")
            return
        dialog = GuideDetailDialog(db_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success", "Guide updated.")
            self.reload_table()
            if self._on_data_changed:
                self._on_data_changed()

    def archive_selected(self) -> None:
        db_id = self._selected_id()
        if db_id is None:
            QMessageBox.information(self, "No Selection", "Select a guide first.")
            return
        archive_guide(db_id)
        QMessageBox.information(self, "Success", "Guide archived.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()

    def restore_selected(self) -> None:
        db_id = self._selected_id()
        if db_id is None:
            QMessageBox.information(self, "No Selection", "Select a guide first.")
            return
        restore_guide(db_id)
        QMessageBox.information(self, "Success", "Guide restored.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()

    def delete_selected(self) -> None:
        db_id = self._selected_id()
        if db_id is None:
            QMessageBox.information(self, "No Selection", "Select a guide first.")
            return
        confirm = QMessageBox.question(self, "Delete Guide", "Delete selected guide?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        delete_guide(db_id)
        QMessageBox.information(self, "Success", "Guide deleted.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()
