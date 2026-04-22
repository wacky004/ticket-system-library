"""Guides / Knowledge Base workspace UI."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
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
    list_tickets_for_guide,
    restore_guide,
    search_guides,
    update_guide,
)
from app.ui.components import ReadableContentCard, configure_tab_widget
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
        self.difficulty_input = QComboBox()
        self.difficulty_input.addItems(["", "Beginner", "Intermediate", "Advanced"])
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
            field.setFixedHeight(86)
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
        self.difficulty_input.setCurrentText(str(guide.get("difficulty") or ""))
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
            "difficulty": self.difficulty_input.currentText(),
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
        self.setMinimumSize(980, 760)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        configure_tab_widget(self.tabs)
        self.form = GuideFormWidget()
        self.attachments_panel = AttachmentPanel("guide", allow_clipboard=True)

        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setContentsMargins(8, 8, 8, 8)
        details_layout.addWidget(self.form)
        self.tabs.addTab(details_tab, "Details")
        self.tabs.addTab(self.attachments_panel, "Attachments")

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


class GuideWorkspaceDetail(QWidget):
    """Right panel for guide content reading and linked tickets."""

    def __init__(self) -> None:
        super().__init__()
        self.guide_db_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QFrame()
        header.setObjectName("Card")
        h = QVBoxLayout(header)
        h.setContentsMargins(10, 10, 10, 10)
        h.setSpacing(6)
        self.guide_id_label = QLabel("No guide selected")
        self.guide_id_label.setObjectName("SectionTitle")
        self.title_label = QLabel("Select a guide from the list to inspect details.")
        self.title_label.setObjectName("PageSubtitle")
        self.title_label.setWordWrap(True)
        self.meta_label = QLabel("-")
        self.meta_label.setObjectName("MetaLabel")
        h.addWidget(self.guide_id_label)
        h.addWidget(self.title_label)
        h.addWidget(self.meta_label)

        self.tabs = QTabWidget()
        configure_tab_widget(self.tabs)
        self.overview_card = ReadableContentCard("Overview")
        self.installation_card = ReadableContentCard("Installation Steps")
        self.troubleshooting_card = ReadableContentCard("Troubleshooting")
        self.solution_card = ReadableContentCard("Solution")
        self.attachments_panel = AttachmentPanel("guide", allow_clipboard=True)
        self.linked_tickets_table = QTableWidget(0, 6)
        self.linked_tickets_table.setHorizontalHeaderLabels(
            ["Ticket ID", "Title", "Client", "Status", "Priority", "Linked At"]
        )
        self.linked_tickets_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.linked_tickets_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.linked_tickets_table.verticalHeader().setVisible(False)
        self.linked_tickets_table.horizontalHeader().setStretchLastSection(True)
        self.linked_tickets_table.setAlternatingRowColors(True)

        self.tabs.addTab(self.overview_card, "Overview")
        self.tabs.addTab(self.installation_card, "Installation")
        self.tabs.addTab(self.troubleshooting_card, "Troubleshooting")
        self.tabs.addTab(self.solution_card, "Solution")
        self.tabs.addTab(self.attachments_panel, "Attachments")
        self.tabs.addTab(self.linked_tickets_table, "Linked Tickets")

        root.addWidget(header)
        root.addWidget(self.tabs, 1)

    def set_guide(self, guide_db_id: int | None) -> None:
        self.guide_db_id = guide_db_id
        if guide_db_id is None:
            self.guide_id_label.setText("No guide selected")
            self.title_label.setText("Select a guide from the list to inspect details.")
            self.meta_label.setText("-")
            self.overview_card.set_text("")
            self.installation_card.set_text("")
            self.troubleshooting_card.set_text("")
            self.solution_card.set_text("")
            self.linked_tickets_table.setRowCount(0)
            self.attachments_panel.set_parent_record(None)
            return

        guide = get_guide_by_db_id(guide_db_id)
        if guide is None:
            self.set_guide(None)
            return

        self.guide_id_label.setText(str(guide.get("guide_id") or "Guide"))
        self.title_label.setText(str(guide.get("title") or ""))
        self.meta_label.setText(
            f"Category: {guide.get('category') or '-'}   Difficulty: {guide.get('difficulty') or '-'}   Updated: {guide.get('updated_at') or '-'}"
        )

        overview_text = (
            f"Summary:\n{guide.get('summary') or ''}\n\n"
            f"Problem Description:\n{guide.get('problem_description') or ''}\n\n"
            f"Notes:\n{guide.get('notes') or ''}"
        )
        self.overview_card.set_text(overview_text)
        self.installation_card.set_text(str(guide.get("installation_steps") or ""))
        self.troubleshooting_card.set_text(str(guide.get("troubleshooting_steps") or ""))
        self.solution_card.set_text(str(guide.get("solution_steps") or ""))
        self.attachments_panel.set_parent_record(guide_db_id)

        linked_tickets = list_tickets_for_guide(guide_db_id)
        self.linked_tickets_table.setRowCount(0)
        for row_index, ticket in enumerate(linked_tickets):
            self.linked_tickets_table.insertRow(row_index)
            values = [
                ticket.get("ticket_id"),
                ticket.get("title"),
                ticket.get("client_name"),
                ticket.get("status"),
                ticket.get("priority"),
                ticket.get("created_at"),
            ]
            for col_index, value in enumerate(values):
                self.linked_tickets_table.setItem(row_index, col_index, QTableWidgetItem(str(value or "")))
        self.linked_tickets_table.resizeColumnsToContents()


class GuidesPage(QWidget):
    COLUMNS = ["ID", "Guide ID", "Title", "Category", "Difficulty", "Related Software", "Updated", "Archived"]

    def __init__(self, on_data_changed: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._on_data_changed = on_data_changed
        self._current_rows: list[dict[str, Any]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)
        title = QLabel("Guides Workspace")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Knowledge base browsing with category filters, readable details, and linked tickets.")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_panel = QFrame()
        left_panel.setObjectName("Card")
        l = QVBoxLayout(left_panel)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(8)
        l.addWidget(QLabel("Guide Filters"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search guides by id, title, category, steps, and tags...")
        self.category_list = QListWidget()
        self.category_list.addItem("All Categories")
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItems(["", "Beginner", "Intermediate", "Advanced"])
        self.archived_only_check = QCheckBox("Archived only")
        self.favorites_check = QCheckBox("Favorites only (placeholder)")
        l.addWidget(self.search_input)
        l.addWidget(self.category_list, 1)
        l.addWidget(QLabel("Difficulty"))
        l.addWidget(self.difficulty_filter)
        l.addWidget(self.archived_only_check)
        l.addWidget(self.favorites_check)
        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.setObjectName("SecondaryButton")
        l.addWidget(self.clear_filters_button)

        center_panel = QWidget()
        c = QVBoxLayout(center_panel)
        c.setContentsMargins(0, 0, 0, 0)
        c.setSpacing(8)
        toolbar = QFrame()
        toolbar.setObjectName("Card")
        t = QHBoxLayout(toolbar)
        t.setContentsMargins(10, 10, 10, 10)
        t.setSpacing(8)
        self.count_label = QLabel("0 guides")
        self.count_label.setObjectName("MetaLabel")
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
        t.addWidget(self.count_label)
        t.addStretch(1)
        for btn in (
            self.new_button,
            self.open_button,
            self.archive_button,
            self.restore_button,
            self.delete_button,
            self.refresh_button,
        ):
            t.addWidget(btn)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        c.addWidget(toolbar)
        c.addWidget(self.table, 1)

        self.detail_panel = GuideWorkspaceDetail()
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([250, 600, 500])
        root.addWidget(splitter, 1)

        self.search_input.textChanged.connect(lambda _text: self.reload_table())
        self.category_list.itemSelectionChanged.connect(self.reload_table)
        self.difficulty_filter.currentIndexChanged.connect(lambda _i: self.reload_table())
        self.archived_only_check.stateChanged.connect(lambda _s: self.reload_table())
        self.favorites_check.stateChanged.connect(lambda _s: self.reload_table())
        self.clear_filters_button.clicked.connect(self._clear_filters)
        self.new_button.clicked.connect(self.new_guide)
        self.open_button.clicked.connect(self.open_selected)
        self.archive_button.clicked.connect(self.archive_selected)
        self.restore_button.clicked.connect(self.restore_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.refresh_button.clicked.connect(self.reload_table)
        self.table.cellDoubleClicked.connect(lambda _r, _c: self.open_selected())
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        self.reload_table()

    def _selected_category(self) -> str | None:
        item = self.category_list.currentItem()
        if item is None:
            return None
        text = item.text().strip()
        if text == "All Categories":
            return None
        return text

    def _clear_filters(self) -> None:
        self.search_input.clear()
        self.difficulty_filter.setCurrentIndex(0)
        self.archived_only_check.setChecked(False)
        self.favorites_check.setChecked(False)
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
        self.reload_table()

    def reload_table(self) -> None:
        guides = search_guides(self.search_input.text(), include_archived=True)
        category = self._selected_category()
        difficulty = self.difficulty_filter.currentText().strip()
        archived_only = self.archived_only_check.isChecked()

        filtered: list[dict[str, Any]] = []
        for guide in guides:
            if category and str(guide.get("category") or "") != category:
                continue
            if difficulty and str(guide.get("difficulty") or "") != difficulty:
                continue
            if archived_only and not int(guide.get("archived") or 0):
                continue
            filtered.append(guide)
        self._current_rows = filtered

        self.table.setRowCount(0)
        categories = sorted(
            {str(g.get("category") or "") for g in guides if str(g.get("category") or "").strip()},
            key=lambda x: x.lower(),
        )
        selected = self._selected_category()
        self.category_list.blockSignals(True)
        self.category_list.clear()
        self.category_list.addItem("All Categories")
        for cat in categories:
            self.category_list.addItem(cat)
        if selected:
            items = self.category_list.findItems(selected, Qt.MatchFlag.MatchExactly)
            if items:
                self.category_list.setCurrentItem(items[0])
            else:
                self.category_list.setCurrentRow(0)
        elif self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
        self.category_list.blockSignals(False)

        for row_index, guide in enumerate(filtered):
            self.table.insertRow(row_index)
            values = [
                str(guide.get("id") or ""),
                str(guide.get("guide_id") or ""),
                str(guide.get("title") or ""),
                str(guide.get("category") or ""),
                str(guide.get("difficulty") or ""),
                str(guide.get("related_software") or ""),
                str(guide.get("updated_at") or ""),
                "Yes" if int(guide.get("archived") or 0) else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, int(guide["id"]))
                self.table.setItem(row_index, col, item)
        self.table.resizeColumnsToContents()
        self.count_label.setText(f"{len(filtered)} guides")
        if filtered:
            self.table.setCurrentCell(0, 0)
        else:
            self.detail_panel.set_guide(None)

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def _on_selection_changed(self) -> None:
        self.detail_panel.set_guide(self._selected_id())

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
        if QMessageBox.question(self, "Delete Guide", "Delete selected guide?") != QMessageBox.StandardButton.Yes:
            return
        delete_guide(db_id)
        QMessageBox.information(self, "Success", "Guide deleted.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()
