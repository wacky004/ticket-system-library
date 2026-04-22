"""Ticket management UI for Phase 2 CRUD features."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import (
    archive_ticket,
    create_ticket,
    delete_ticket,
    generate_next_ticket_id,
    get_default_priorities,
    get_default_statuses,
    get_ticket_by_db_id,
    list_categories,
    list_subcategories,
    list_tickets,
    reopen_ticket,
    update_ticket,
)


class TicketFormWidget(QWidget):
    """Reusable ticket form used by new/edit flows."""

    def __init__(self) -> None:
        super().__init__()
        self.ticket_db_id: int | None = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content_layout.setSpacing(16)

        self.ticket_id_label = QLabel("Auto-generated on save")
        self.ticket_id_label.setObjectName("MetaLabel")

        ticket_id_row = QHBoxLayout()
        ticket_id_title = QLabel("Ticket ID")
        ticket_id_title.setObjectName("FieldLabel")
        ticket_id_row.addWidget(ticket_id_title)
        ticket_id_row.addWidget(self.ticket_id_label, 1)
        self._content_layout.addLayout(ticket_id_row)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(12)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter ticket title")

        self.client_name_input = QLineEdit()
        self.va_name_input = QLineEdit()

        self.category_input = QComboBox()
        self.category_input.setEditable(False)
        self.subcategory_input = QComboBox()
        self.subcategory_input.setEditable(False)

        self.priority_input = QComboBox()
        self.status_input = QComboBox()

        self.assigned_to_input = QLineEdit()
        self.source_input = QLineEdit()

        self.description_input = QTextEdit()
        self.troubleshooting_input = QTextEdit()
        self.resolution_input = QTextEdit()
        self.next_action_input = QTextEdit()

        for field in (
            self.description_input,
            self.troubleshooting_input,
            self.resolution_input,
            self.next_action_input,
        ):
            field.setFixedHeight(88)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Example: vpn,network,urgent")

        self.follow_up_input = QLineEdit()
        self.follow_up_input.setPlaceholderText("YYYY-MM-DD")

        self.device_name_input = QLineEdit()
        self.software_tools_input = QLineEdit()

        form_layout.addRow("Title *", self.title_input)
        form_layout.addRow("Client Name", self.client_name_input)
        form_layout.addRow("VA Name", self.va_name_input)
        form_layout.addRow("Category", self.category_input)
        form_layout.addRow("Subcategory", self.subcategory_input)
        form_layout.addRow("Priority *", self.priority_input)
        form_layout.addRow("Status *", self.status_input)
        form_layout.addRow("Assigned Technician", self.assigned_to_input)
        form_layout.addRow("Source", self.source_input)
        form_layout.addRow("Description", self.description_input)
        form_layout.addRow("Troubleshooting", self.troubleshooting_input)
        form_layout.addRow("Resolution", self.resolution_input)
        form_layout.addRow("Next Action", self.next_action_input)
        form_layout.addRow("Tags", self.tags_input)
        form_layout.addRow("Follow-up Date", self.follow_up_input)
        form_layout.addRow("Device/System", self.device_name_input)
        form_layout.addRow("Software/Tools", self.software_tools_input)

        self._content_layout.addLayout(form_layout)
        self._content_layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self.category_input.currentTextChanged.connect(self._reload_subcategories)
        self.load_reference_data()

    def load_reference_data(self) -> None:
        categories = list_categories()
        priorities = get_default_priorities()
        statuses = get_default_statuses()

        self.category_input.blockSignals(True)
        self.priority_input.blockSignals(True)
        self.status_input.blockSignals(True)

        self.category_input.clear()
        self.category_input.addItem("")
        self.category_input.addItems(categories)

        self.priority_input.clear()
        self.priority_input.addItems(priorities)

        self.status_input.clear()
        self.status_input.addItems(statuses)

        self.category_input.blockSignals(False)
        self.priority_input.blockSignals(False)
        self.status_input.blockSignals(False)

        if priorities:
            self.priority_input.setCurrentText("Medium" if "Medium" in priorities else priorities[0])
        if statuses:
            self.status_input.setCurrentText("Open" if "Open" in statuses else statuses[0])

        self._reload_subcategories(self.category_input.currentText())

    def _reload_subcategories(self, category_name: str) -> None:
        subcategories = list_subcategories(category_name if category_name else None)
        self.subcategory_input.clear()
        self.subcategory_input.addItem("")
        self.subcategory_input.addItems(subcategories)

    def set_ticket_preview(self, ticket_id: str) -> None:
        self.ticket_id_label.setText(ticket_id)

    def clear_form(self) -> None:
        self.ticket_db_id = None
        self.ticket_id_label.setText("Auto-generated on save")

        self.title_input.clear()
        self.client_name_input.clear()
        self.va_name_input.clear()
        self.category_input.setCurrentIndex(0)
        self._reload_subcategories("")

        if self.priority_input.count() > 0:
            self.priority_input.setCurrentText("Medium" if self.priority_input.findText("Medium") >= 0 else self.priority_input.itemText(0))
        if self.status_input.count() > 0:
            self.status_input.setCurrentText("Open" if self.status_input.findText("Open") >= 0 else self.status_input.itemText(0))

        self.assigned_to_input.clear()
        self.source_input.clear()
        self.description_input.clear()
        self.troubleshooting_input.clear()
        self.resolution_input.clear()
        self.next_action_input.clear()
        self.tags_input.clear()
        self.follow_up_input.clear()
        self.device_name_input.clear()
        self.software_tools_input.clear()

    def load_ticket(self, ticket: dict[str, Any]) -> None:
        self.ticket_db_id = int(ticket["id"])
        self.ticket_id_label.setText(str(ticket.get("ticket_id") or ""))

        self.title_input.setText(str(ticket.get("title") or ""))
        self.client_name_input.setText(str(ticket.get("client_name") or ""))
        self.va_name_input.setText(str(ticket.get("va_name") or ""))

        category = str(ticket.get("category") or "")
        self._set_or_append_combo_text(self.category_input, category)
        self._reload_subcategories(category)
        self._set_or_append_combo_text(self.subcategory_input, str(ticket.get("subcategory") or ""))

        self._set_or_append_combo_text(self.priority_input, str(ticket.get("priority") or "Medium"))
        self._set_or_append_combo_text(self.status_input, str(ticket.get("status") or "Open"))

        self.assigned_to_input.setText(str(ticket.get("assigned_to") or ""))
        self.source_input.setText(str(ticket.get("source") or ""))
        self.description_input.setPlainText(str(ticket.get("description") or ""))
        self.troubleshooting_input.setPlainText(str(ticket.get("troubleshooting") or ""))
        self.resolution_input.setPlainText(str(ticket.get("resolution") or ""))
        self.next_action_input.setPlainText(str(ticket.get("next_action") or ""))
        self.tags_input.setText(str(ticket.get("tags_text") or ""))
        self.follow_up_input.setText(str(ticket.get("follow_up_date") or ""))
        self.device_name_input.setText(str(ticket.get("device_name") or ""))
        self.software_tools_input.setText(str(ticket.get("software_tools") or ""))

    def get_payload(self) -> dict[str, Any]:
        return {
            "title": self.title_input.text(),
            "client_name": self.client_name_input.text(),
            "va_name": self.va_name_input.text(),
            "category": self.category_input.currentText(),
            "subcategory": self.subcategory_input.currentText(),
            "priority": self.priority_input.currentText(),
            "status": self.status_input.currentText(),
            "assigned_to": self.assigned_to_input.text(),
            "source": self.source_input.text(),
            "description": self.description_input.toPlainText(),
            "troubleshooting": self.troubleshooting_input.toPlainText(),
            "resolution": self.resolution_input.toPlainText(),
            "next_action": self.next_action_input.toPlainText(),
            "tags_text": self.tags_input.text(),
            "follow_up_date": self.follow_up_input.text(),
            "device_name": self.device_name_input.text(),
            "software_tools": self.software_tools_input.text(),
        }

    @staticmethod
    def _set_or_append_combo_text(combo: QComboBox, value: str) -> None:
        if not value:
            combo.setCurrentIndex(0)
            return

        index = combo.findText(value)
        if index < 0:
            combo.addItem(value)
            index = combo.findText(value)
        combo.setCurrentIndex(index)


class NewTicketPage(QWidget):
    """Page used for creating new tickets."""

    def __init__(self, on_ticket_saved: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._on_ticket_saved = on_ticket_saved

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel("New Ticket")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Create a new support ticket. Fields marked with * are required.")
        subtitle.setObjectName("PageSubtitle")

        self.form = TicketFormWidget()

        actions = QHBoxLayout()
        actions.addStretch(1)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("SecondaryButton")

        self.save_button = QPushButton("Save Ticket")
        self.save_button.setObjectName("PrimaryButton")

        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.form, 1)
        layout.addLayout(actions)

        self.cancel_button.clicked.connect(self._handle_cancel)
        self.save_button.clicked.connect(self._handle_save)

        self.refresh_ticket_preview()

    def refresh_ticket_preview(self) -> None:
        self.form.set_ticket_preview(generate_next_ticket_id())

    def _handle_cancel(self) -> None:
        self.form.clear_form()
        self.refresh_ticket_preview()

    def _handle_save(self) -> None:
        try:
            ticket_db_id = create_ticket(self.form.get_payload())
            saved_ticket = get_ticket_by_db_id(ticket_db_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:  # pragma: no cover - safety guard
            QMessageBox.critical(self, "Save Failed", f"Unable to save ticket.\n\n{exc}")
            return

        ticket_label = saved_ticket["ticket_id"] if saved_ticket else f"ID {ticket_db_id}"
        QMessageBox.information(self, "Success", f"Ticket {ticket_label} was created.")

        self.form.clear_form()
        self.refresh_ticket_preview()

        if self._on_ticket_saved:
            self._on_ticket_saved()


class TicketDetailDialog(QDialog):
    """Dialog for viewing/editing an existing ticket."""

    def __init__(self, ticket_db_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ticket_db_id = ticket_db_id
        self.setWindowTitle("Ticket Details")
        self.setMinimumSize(860, 740)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("MetaLabel")

        self.form = TicketFormWidget()

        actions = QHBoxLayout()
        actions.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("SecondaryButton")
        save_button = QPushButton("Save Changes")
        save_button.setObjectName("PrimaryButton")

        actions.addWidget(cancel_button)
        actions.addWidget(save_button)

        layout.addWidget(self.meta_label)
        layout.addWidget(self.form, 1)
        layout.addLayout(actions)

        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self._save)

        self._load_ticket()

    def _load_ticket(self) -> None:
        ticket = get_ticket_by_db_id(self.ticket_db_id)
        if ticket is None:
            QMessageBox.critical(self, "Not Found", "Ticket was not found.")
            self.reject()
            return

        self.form.load_ticket(ticket)
        self._refresh_meta(ticket)

    def _refresh_meta(self, ticket: dict[str, Any]) -> None:
        created = ticket.get("created_at") or "-"
        updated = ticket.get("updated_at") or "-"
        resolved = ticket.get("resolved_at") or "-"
        archived = "Yes" if int(ticket.get("archived") or 0) else "No"
        self.meta_label.setText(
            f"Created: {created}    Updated: {updated}    Resolved: {resolved}    Archived: {archived}"
        )

    def _save(self) -> None:
        try:
            update_ticket(self.ticket_db_id, self.form.get_payload())
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:  # pragma: no cover - safety guard
            QMessageBox.critical(self, "Update Failed", f"Unable to update ticket.\n\n{exc}")
            return

        QMessageBox.information(self, "Success", "Ticket updated successfully.")
        self.accept()


class TicketsPage(QWidget):
    """Tickets table page with CRUD actions."""

    TABLE_COLUMNS = [
        "ID",
        "Ticket ID",
        "Title",
        "Client",
        "Category",
        "Subcategory",
        "Priority",
        "Status",
        "Assigned",
        "Archived",
        "Updated",
    ]

    def __init__(
        self,
        on_request_new_ticket: Callable[[], None] | None = None,
        on_data_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._on_request_new_ticket = on_request_new_ticket
        self._on_data_changed = on_data_changed

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        title = QLabel("Tickets")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Manage, edit, archive, and reopen tickets.")
        subtitle.setObjectName("PageSubtitle")

        controls_card = QFrame()
        controls_card.setObjectName("Card")
        controls_layout = QGridLayout(controls_card)
        controls_layout.setContentsMargins(14, 14, 14, 14)
        controls_layout.setHorizontalSpacing(8)
        controls_layout.setVerticalSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tickets (coming in next phase)")
        self.search_input.setEnabled(False)

        self.new_button = QPushButton("New Ticket")
        self.new_button.setObjectName("PrimaryButton")
        self.open_button = QPushButton("Open/Edit")
        self.open_button.setObjectName("SecondaryButton")
        self.archive_button = QPushButton("Archive")
        self.archive_button.setObjectName("SecondaryButton")
        self.reopen_button = QPushButton("Reopen")
        self.reopen_button.setObjectName("SecondaryButton")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("DangerButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")

        controls_layout.addWidget(self.search_input, 0, 0, 1, 4)
        controls_layout.addWidget(self.new_button, 1, 0)
        controls_layout.addWidget(self.open_button, 1, 1)
        controls_layout.addWidget(self.archive_button, 1, 2)
        controls_layout.addWidget(self.reopen_button, 1, 3)
        controls_layout.addWidget(self.delete_button, 2, 2)
        controls_layout.addWidget(self.refresh_button, 2, 3)

        self.table = QTableWidget(0, len(self.TABLE_COLUMNS))
        self.table.setObjectName("TicketsTable")
        self.table.setHorizontalHeaderLabels(self.TABLE_COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(controls_card)
        root.addWidget(self.table, 1)

        self.new_button.clicked.connect(self._handle_new_ticket)
        self.open_button.clicked.connect(self.open_selected_ticket)
        self.archive_button.clicked.connect(self.archive_selected_ticket)
        self.reopen_button.clicked.connect(self.reopen_selected_ticket)
        self.delete_button.clicked.connect(self.delete_selected_ticket)
        self.refresh_button.clicked.connect(self.reload_table)
        self.table.cellDoubleClicked.connect(lambda _row, _col: self.open_selected_ticket())

        self.reload_table()

    def reload_table(self) -> None:
        try:
            tickets = list_tickets(include_archived=True)
        except Exception as exc:  # pragma: no cover - safety guard
            QMessageBox.critical(self, "Load Failed", f"Unable to load tickets.\n\n{exc}")
            return

        self.table.setRowCount(0)

        for row_index, ticket in enumerate(tickets):
            self.table.insertRow(row_index)

            values = [
                str(ticket.get("id") or ""),
                str(ticket.get("ticket_id") or ""),
                str(ticket.get("title") or ""),
                str(ticket.get("client_name") or ""),
                str(ticket.get("category") or ""),
                str(ticket.get("subcategory") or ""),
                str(ticket.get("priority") or ""),
                str(ticket.get("status") or ""),
                str(ticket.get("assigned_to") or ""),
                "Yes" if int(ticket.get("archived") or 0) else "No",
                str(ticket.get("updated_at") or ""),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, int(ticket["id"]))
                self.table.setItem(row_index, col_index, item)

        self.table.resizeColumnsToContents()

    def _selected_ticket_db_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if item is None:
            return None

        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def _selected_ticket(self) -> dict[str, Any] | None:
        db_id = self._selected_ticket_db_id()
        if db_id is None:
            return None
        return get_ticket_by_db_id(db_id)

    def _handle_new_ticket(self) -> None:
        if self._on_request_new_ticket:
            self._on_request_new_ticket()

    def open_selected_ticket(self) -> None:
        db_id = self._selected_ticket_db_id()
        if db_id is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return

        dialog = TicketDetailDialog(db_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.reload_table()
            if self._on_data_changed:
                self._on_data_changed()

    def archive_selected_ticket(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return

        if int(ticket.get("archived") or 0):
            QMessageBox.information(self, "Already Archived", "Selected ticket is already archived.")
            return

        prompt = QMessageBox.question(
            self,
            "Confirm Archive",
            f"Archive ticket {ticket.get('ticket_id')}?",
        )
        if prompt != QMessageBox.StandardButton.Yes:
            return

        archive_ticket(int(ticket["id"]))
        QMessageBox.information(self, "Success", "Ticket archived.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()

    def reopen_selected_ticket(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return

        if not int(ticket.get("archived") or 0):
            QMessageBox.information(self, "Not Archived", "Selected ticket is already active.")
            return

        prompt = QMessageBox.question(
            self,
            "Confirm Reopen",
            f"Reopen ticket {ticket.get('ticket_id')}? This sets status back to Open.",
        )
        if prompt != QMessageBox.StandardButton.Yes:
            return

        reopen_ticket(int(ticket["id"]))
        QMessageBox.information(self, "Success", "Ticket reopened.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()

    def delete_selected_ticket(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return

        prompt = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete ticket {ticket.get('ticket_id')} permanently?",
        )
        if prompt != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_ticket(int(ticket["id"]))
        except Exception as exc:  # pragma: no cover - safety guard
            QMessageBox.critical(self, "Delete Failed", f"Unable to delete ticket.\n\n{exc}")
            return

        QMessageBox.information(self, "Success", "Ticket deleted.")
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()
