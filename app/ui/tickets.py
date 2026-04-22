"""Ticket management UI with CRUD, browsing, and attachment features."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.db.database import (
    ALLOWED_ATTACHMENT_EXTENSIONS,
    add_ticket_note,
    add_ticket_attachment,
    archive_ticket,
    create_ticket,
    delete_ticket,
    duplicate_ticket,
    generate_next_ticket_id,
    get_default_priorities,
    get_default_statuses,
    get_export_directory,
    set_export_directory,
    get_ticket_by_db_id,
    get_ticket_filter_options,
    list_categories,
    list_ticket_history,
    list_ticket_notes,
    list_subcategories,
    list_ticket_attachments,
    remove_ticket_attachment,
    set_ticket_pinned,
    set_ticket_starred,
    reopen_ticket,
    search_tickets,
    update_ticket,
)
from app.services.exports import export_ticket_to_pdf, export_tickets_to_csv, export_tickets_to_excel


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
            self.priority_input.setCurrentText(
                "Medium" if self.priority_input.findText("Medium") >= 0 else self.priority_input.itemText(0)
            )
        if self.status_input.count() > 0:
            self.status_input.setCurrentText(
                "Open" if self.status_input.findText("Open") >= 0 else self.status_input.itemText(0)
            )

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
        self._baseline_payload = self.form.get_payload().copy()

    def refresh_ticket_preview(self) -> None:
        self.form.set_ticket_preview(generate_next_ticket_id())

    def _handle_cancel(self) -> None:
        if self.form.get_payload() != self._baseline_payload:
            confirm = QMessageBox.question(
                self,
                "Discard Changes",
                "You have unsaved changes. Discard them?",
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        self.form.clear_form()
        self.refresh_ticket_preview()
        self._baseline_payload = self.form.get_payload().copy()

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
        self._baseline_payload = self.form.get_payload().copy()

        if self._on_ticket_saved:
            self._on_ticket_saved()

    def confirm_leave(self) -> bool:
        if self.form.get_payload() == self._baseline_payload:
            return True
        confirm = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes in New Ticket. Leave without saving?",
        )
        return confirm == QMessageBox.StandardButton.Yes

    def handle_save_shortcut(self) -> None:
        self._handle_save()


class AttachmentListWidget(QListWidget):
    """List widget that supports drag-and-drop image files."""

    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setIconSize(QSize(120, 120))
        self.setSpacing(10)
        self.setWordWrap(True)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        if not event.mimeData().hasUrls():
            super().dropEvent(event)
            return

        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()


class AttachmentPreviewDialog(QDialog):
    """Full-size image preview dialog for an attachment."""

    def __init__(self, attachment: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(attachment.get("filename") or "Attachment Preview"))
        self.setMinimumSize(900, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setObjectName("AttachmentPreview")
        layout.addWidget(self.image_label, 1)

        close_button = QPushButton("Close")
        close_button.setObjectName("SecondaryButton")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        file_path = Path(str(attachment.get("file_path") or ""))
        pixmap = QPixmap(str(file_path))
        if not file_path.exists() or pixmap.isNull():
            self.image_label.setText("Image file is missing or unreadable.")
            return

        self._raw_pixmap = pixmap
        self._refresh_image()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "_raw_pixmap"):
            self._refresh_image()

    def _refresh_image(self) -> None:
        scaled = self._raw_pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)


class AttachmentPanel(QWidget):
    """Attachment management tab for a ticket."""

    def __init__(self) -> None:
        super().__init__()
        self.ticket_db_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        subtitle = QLabel(
            "Attach PNG, JPG, JPEG, or WEBP images. You can add multiple files, drag-drop images, or paste from clipboard."
        )
        subtitle.setObjectName("PageSubtitle")

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note/label for newly added images")

        self.list_widget = AttachmentListWidget()
        self.list_widget.setObjectName("AttachmentList")

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.add_button = QPushButton("Add Images")
        self.add_button.setObjectName("PrimaryButton")
        self.paste_button = QPushButton("Paste Image")
        self.paste_button.setObjectName("SecondaryButton")
        self.preview_button = QPushButton("Open Preview")
        self.preview_button.setObjectName("SecondaryButton")
        self.remove_button = QPushButton("Remove")
        self.remove_button.setObjectName("DangerButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")

        actions.addWidget(self.add_button)
        actions.addWidget(self.paste_button)
        actions.addWidget(self.preview_button)
        actions.addWidget(self.remove_button)
        actions.addStretch(1)
        actions.addWidget(self.refresh_button)

        self.status_label = QLabel("0 attachments")
        self.status_label.setObjectName("MetaLabel")

        root.addWidget(subtitle)
        root.addWidget(self.note_input)
        root.addLayout(actions)
        root.addWidget(self.list_widget, 1)
        root.addWidget(self.status_label)

        self.add_button.clicked.connect(self.add_images_via_dialog)
        self.paste_button.clicked.connect(self.add_image_from_clipboard)
        self.preview_button.clicked.connect(self.open_selected_attachment)
        self.remove_button.clicked.connect(self.remove_selected_attachment)
        self.refresh_button.clicked.connect(self.reload)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self.open_selected_attachment())
        self.list_widget.files_dropped.connect(self._add_files)

    def set_ticket(self, ticket_db_id: int) -> None:
        self.ticket_db_id = ticket_db_id
        self.reload()

    def reload(self) -> None:
        self.list_widget.clear()

        if self.ticket_db_id is None:
            self.status_label.setText("No ticket selected")
            return

        attachments = list_ticket_attachments(self.ticket_db_id)
        for attachment in attachments:
            self._add_attachment_item(attachment)
        self.status_label.setText(f"{len(attachments)} attachments")

    def _add_attachment_item(self, attachment: dict[str, Any]) -> None:
        file_name = str(attachment.get("filename") or "unnamed")
        note = str(attachment.get("note_label") or "")
        added_at = str(attachment.get("added_at") or "")
        file_path = Path(str(attachment.get("file_path") or ""))

        label_lines = [file_name]
        if note:
            label_lines.append(note)
        if added_at:
            label_lines.append(added_at)
        label = "\n".join(label_lines)

        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, attachment)
        item.setToolTip(str(file_path))

        icon_pixmap = self._build_thumbnail(file_path)
        item.setIcon(QIcon(icon_pixmap))
        self.list_widget.addItem(item)

    def _build_thumbnail(self, file_path: Path) -> QPixmap:
        if file_path.exists():
            image = QPixmap(str(file_path))
            if not image.isNull():
                return image.scaled(
                    120,
                    120,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

        placeholder = QPixmap(120, 120)
        placeholder.fill(Qt.GlobalColor.darkGray)
        return placeholder

    def add_images_via_dialog(self) -> None:
        if self.ticket_db_id is None:
            return

        pattern = "Images (*.png *.jpg *.jpeg *.webp)"
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select images", "", pattern)
        if not file_paths:
            return
        self._add_files(file_paths)

    def _add_files(self, file_paths: list[str]) -> None:
        if self.ticket_db_id is None:
            return

        note = self.note_input.text().strip() or None
        added_count = 0
        errors: list[str] = []
        for path in file_paths:
            source = Path(path)
            if source.suffix.lower() not in ALLOWED_ATTACHMENT_EXTENSIONS:
                errors.append(f"{source.name}: unsupported format")
                continue

            try:
                add_ticket_attachment(self.ticket_db_id, source, note)
                added_count += 1
            except Exception as exc:
                errors.append(f"{source.name}: {exc}")

        self.reload()
        if added_count:
            QMessageBox.information(self, "Success", f"Added {added_count} attachment(s).")
        if errors:
            QMessageBox.warning(self, "Some Files Skipped", "\n".join(errors))

    def add_image_from_clipboard(self) -> None:
        if self.ticket_db_id is None:
            return

        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if image.isNull():
            QMessageBox.information(self, "Clipboard Empty", "Clipboard does not contain an image.")
            return

        note = self.note_input.text().strip() or None
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                temp_path = Path(tmp.name)
            image.save(str(temp_path), "PNG")
            add_ticket_attachment(self.ticket_db_id, temp_path, note)
        except Exception as exc:
            QMessageBox.critical(self, "Paste Failed", f"Unable to attach clipboard image.\n\n{exc}")
            return
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

        self.reload()
        QMessageBox.information(self, "Success", "Image pasted and attached.")

    def selected_attachment(self) -> dict[str, Any] | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        data = item.data(Qt.ItemDataRole.UserRole)
        return dict(data) if isinstance(data, dict) else None

    def open_selected_attachment(self) -> None:
        attachment = self.selected_attachment()
        if attachment is None:
            QMessageBox.information(self, "No Selection", "Select an attachment first.")
            return

        file_path = Path(str(attachment.get("file_path") or ""))
        if not file_path.exists():
            QMessageBox.warning(self, "Missing File", "Attachment file is missing from disk.")
            return

        dialog = AttachmentPreviewDialog(attachment, self)
        dialog.exec()

    def remove_selected_attachment(self) -> None:
        attachment = self.selected_attachment()
        if attachment is None:
            QMessageBox.information(self, "No Selection", "Select an attachment first.")
            return

        file_name = str(attachment.get("filename") or "attachment")
        prompt = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove attachment {file_name}?",
        )
        if prompt != QMessageBox.StandardButton.Yes:
            return

        try:
            remove_ticket_attachment(int(attachment["id"]))
        except Exception as exc:
            QMessageBox.critical(self, "Remove Failed", f"Unable to remove attachment.\n\n{exc}")
            return

        self.reload()
        QMessageBox.information(self, "Success", "Attachment removed.")


class NotesPanel(QWidget):
    """Internal notes management panel."""

    NOTE_TYPES = ["Internal", "Update", "Follow-up", "Escalation"]

    def __init__(self) -> None:
        super().__init__()
        self.ticket_db_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        subtitle = QLabel("Add private/internal notes related to this ticket.")
        subtitle.setObjectName("PageSubtitle")

        input_row = QHBoxLayout()
        self.note_type_input = QComboBox()
        self.note_type_input.addItems(self.NOTE_TYPES)
        self.note_type_input.setCurrentText("Internal")
        self.note_content_input = QTextEdit()
        self.note_content_input.setPlaceholderText("Write note content...")
        self.note_content_input.setFixedHeight(96)
        input_row.addWidget(self.note_type_input, 1)
        input_row.addWidget(self.note_content_input, 4)

        action_row = QHBoxLayout()
        self.add_button = QPushButton("Add Note")
        self.add_button.setObjectName("PrimaryButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")
        self.count_label = QLabel("0 notes")
        self.count_label.setObjectName("MetaLabel")

        action_row.addWidget(self.add_button)
        action_row.addWidget(self.refresh_button)
        action_row.addStretch(1)
        action_row.addWidget(self.count_label)

        self.notes_list = QListWidget()
        self.notes_list.setObjectName("NotesList")

        root.addWidget(subtitle)
        root.addLayout(input_row)
        root.addLayout(action_row)
        root.addWidget(self.notes_list, 1)

        self.add_button.clicked.connect(self.add_note)
        self.refresh_button.clicked.connect(self.reload)

    def set_ticket(self, ticket_db_id: int) -> None:
        self.ticket_db_id = ticket_db_id
        self.reload()

    def add_note(self) -> None:
        if self.ticket_db_id is None:
            return

        try:
            add_ticket_note(
                self.ticket_db_id,
                self.note_type_input.currentText(),
                self.note_content_input.toPlainText(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Add Note Failed", f"Unable to add note.\n\n{exc}")
            return

        self.note_content_input.clear()
        self.reload()
        QMessageBox.information(self, "Success", "Note added.")

    def reload(self) -> None:
        self.notes_list.clear()
        if self.ticket_db_id is None:
            self.count_label.setText("No ticket selected")
            return

        notes = list_ticket_notes(self.ticket_db_id)
        for note in notes:
            note_type = str(note.get("note_type") or "Internal")
            created_at = str(note.get("created_at") or "-")
            content = str(note.get("content") or "")
            text = f"[{created_at}] {note_type}\n{content}"
            self.notes_list.addItem(text)

        self.count_label.setText(f"{len(notes)} notes")


class HistoryPanel(QWidget):
    """Audit history display for ticket changes."""

    COLUMNS = ["Timestamp", "Field", "Old Value", "New Value"]

    def __init__(self) -> None:
        super().__init__()
        self.ticket_db_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        subtitle = QLabel("Audit trail of ticket edits. Newest changes appear first.")
        subtitle.setObjectName("PageSubtitle")

        action_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")
        self.count_label = QLabel("0 changes")
        self.count_label.setObjectName("MetaLabel")
        action_row.addWidget(self.refresh_button)
        action_row.addStretch(1)
        action_row.addWidget(self.count_label)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        root.addWidget(subtitle)
        root.addLayout(action_row)
        root.addWidget(self.table, 1)

        self.refresh_button.clicked.connect(self.reload)

    def set_ticket(self, ticket_db_id: int) -> None:
        self.ticket_db_id = ticket_db_id
        self.reload()

    def reload(self) -> None:
        self.table.setRowCount(0)
        if self.ticket_db_id is None:
            self.count_label.setText("No ticket selected")
            return

        entries = list_ticket_history(self.ticket_db_id)
        for row_index, entry in enumerate(entries):
            self.table.insertRow(row_index)
            values = [
                str(entry.get("changed_at") or "-"),
                str(entry.get("field_name") or "-"),
                str(entry.get("old_value") or ""),
                str(entry.get("new_value") or ""),
            ]
            for col_index, value in enumerate(values):
                self.table.setItem(row_index, col_index, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
        self.count_label.setText(f"{len(entries)} changes")


class TicketDetailDialog(QDialog):
    """Dialog for viewing/editing an existing ticket."""

    def __init__(self, ticket_db_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ticket_db_id = ticket_db_id
        self.setWindowTitle("Ticket Details")
        self.setMinimumSize(980, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("MetaLabel")

        self.tabs = QTabWidget()
        self.tabs.setObjectName("TicketTabs")

        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setContentsMargins(8, 8, 8, 8)
        self.form = TicketFormWidget()
        details_layout.addWidget(self.form)

        attachments_tab = QWidget()
        attachments_layout = QVBoxLayout(attachments_tab)
        attachments_layout.setContentsMargins(8, 8, 8, 8)
        self.attachment_panel = AttachmentPanel()
        attachments_layout.addWidget(self.attachment_panel)

        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(8, 8, 8, 8)
        self.notes_panel = NotesPanel()
        notes_layout.addWidget(self.notes_panel)

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(8, 8, 8, 8)
        self.history_panel = HistoryPanel()
        history_layout.addWidget(self.history_panel)

        self.tabs.addTab(details_tab, "Details")
        self.tabs.addTab(attachments_tab, "Attachments")
        self.tabs.addTab(notes_tab, "Notes")
        self.tabs.addTab(history_tab, "History")

        actions = QHBoxLayout()
        actions.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("SecondaryButton")
        save_button = QPushButton("Save Changes")
        save_button.setObjectName("PrimaryButton")

        actions.addWidget(cancel_button)
        actions.addWidget(save_button)

        layout.addWidget(self.meta_label)
        layout.addWidget(self.tabs, 1)
        layout.addLayout(actions)

        cancel_button.clicked.connect(self._cancel)
        save_button.clicked.connect(self._save)
        self._save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self._save_shortcut.activated.connect(self._save)

        self._load_ticket()
        self._baseline_payload = self.form.get_payload().copy()

    def _load_ticket(self) -> None:
        ticket = get_ticket_by_db_id(self.ticket_db_id)
        if ticket is None:
            QMessageBox.critical(self, "Not Found", "Ticket was not found.")
            self.reject()
            return

        self.form.load_ticket(ticket)
        self.attachment_panel.set_ticket(self.ticket_db_id)
        self.notes_panel.set_ticket(self.ticket_db_id)
        self.history_panel.set_ticket(self.ticket_db_id)
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
        self._baseline_payload = self.form.get_payload().copy()
        self.accept()

    def _cancel(self) -> None:
        if self.form.get_payload() != self._baseline_payload:
            confirm = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close without saving?",
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        super().reject()

    def reject(self) -> None:
        if hasattr(self, "_baseline_payload") and self.form.get_payload() != self._baseline_payload:
            confirm = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close without saving?",
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        super().reject()


class TicketsPage(QWidget):
    """Tickets browser page with search, filters, sorting, CRUD actions, and exports."""

    TABLE_COLUMNS = [
        "ID",
        "Star",
        "Pin",
        "Ticket ID",
        "Title",
        "Client",
        "VA",
        "Category",
        "Priority",
        "Status",
        "Assigned",
        "Tags",
        "Archived",
        "Attachments",
        "Updated",
        "Created",
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
        subtitle = QLabel("Browse, search, sort, manage, and export current ticket data.")
        subtitle.setObjectName("PageSubtitle")

        controls_card = QFrame()
        controls_card.setObjectName("Card")
        controls_layout = QGridLayout(controls_card)
        controls_layout.setContentsMargins(14, 14, 14, 14)
        controls_layout.setHorizontalSpacing(8)
        controls_layout.setVerticalSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by ticket ID, title, client, VA, category, priority, status, assigned, tags, or description"
        )

        self.status_filter = QComboBox()
        self.priority_filter = QComboBox()
        self.category_filter = QComboBox()
        self.client_filter = QComboBox()
        self.va_filter = QComboBox()

        self.use_date_from_check = QCheckBox("From")
        self.date_from_input = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_from_input.setDisplayFormat("yyyy-MM-dd")
        self.date_from_input.setCalendarPopup(True)
        self.date_from_input.setEnabled(False)

        self.use_date_to_check = QCheckBox("To")
        self.date_to_input = QDateEdit(QDate.currentDate())
        self.date_to_input.setDisplayFormat("yyyy-MM-dd")
        self.date_to_input.setCalendarPopup(True)
        self.date_to_input.setEnabled(False)

        self.archived_only_check = QCheckBox("Archived Only")
        self.with_attachments_only_check = QCheckBox("With Attachments Only")

        self.quick_open_button = QPushButton("Open")
        self.quick_in_progress_button = QPushButton("In Progress")
        self.quick_pending_button = QPushButton("Pending")
        self.quick_resolved_button = QPushButton("Resolved")
        self.quick_archived_button = QPushButton("Archived")

        for button in (
            self.quick_open_button,
            self.quick_in_progress_button,
            self.quick_pending_button,
            self.quick_resolved_button,
            self.quick_archived_button,
        ):
            button.setObjectName("SecondaryButton")

        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.setObjectName("SecondaryButton")

        self.results_label = QLabel("0 tickets")
        self.results_label.setObjectName("MetaLabel")

        self.export_dir_input = QLineEdit(get_export_directory())
        self.export_dir_input.setReadOnly(True)
        self.export_dir_button = QPushButton("Set Export Folder")
        self.export_dir_button.setObjectName("SecondaryButton")

        self.new_button = QPushButton("New Ticket")
        self.new_button.setObjectName("PrimaryButton")
        self.open_button = QPushButton("Open/Edit")
        self.open_button.setObjectName("SecondaryButton")
        self.star_button = QPushButton("Toggle Star")
        self.star_button.setObjectName("SecondaryButton")
        self.pin_button = QPushButton("Toggle Pin")
        self.pin_button.setObjectName("SecondaryButton")
        self.duplicate_button = QPushButton("Duplicate")
        self.duplicate_button.setObjectName("SecondaryButton")
        self.archive_button = QPushButton("Archive")
        self.archive_button.setObjectName("SecondaryButton")
        self.reopen_button = QPushButton("Reopen")
        self.reopen_button.setObjectName("SecondaryButton")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("DangerButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setObjectName("SecondaryButton")
        self.export_excel_button = QPushButton("Export Excel")
        self.export_excel_button.setObjectName("SecondaryButton")
        self.export_pdf_button = QPushButton("Export Ticket PDF")
        self.export_pdf_button.setObjectName("SecondaryButton")

        controls_layout.addWidget(self.search_input, 0, 0, 1, 6)
        controls_layout.addWidget(QLabel("Status"), 1, 0)
        controls_layout.addWidget(self.status_filter, 1, 1)
        controls_layout.addWidget(QLabel("Priority"), 1, 2)
        controls_layout.addWidget(self.priority_filter, 1, 3)
        controls_layout.addWidget(QLabel("Category"), 1, 4)
        controls_layout.addWidget(self.category_filter, 1, 5)

        controls_layout.addWidget(QLabel("Client"), 2, 0)
        controls_layout.addWidget(self.client_filter, 2, 1)
        controls_layout.addWidget(QLabel("VA"), 2, 2)
        controls_layout.addWidget(self.va_filter, 2, 3)
        controls_layout.addWidget(self.archived_only_check, 2, 4)
        controls_layout.addWidget(self.with_attachments_only_check, 2, 5)

        date_from_layout = QHBoxLayout()
        date_from_layout.setContentsMargins(0, 0, 0, 0)
        date_from_layout.addWidget(self.use_date_from_check)
        date_from_layout.addWidget(self.date_from_input)

        date_to_layout = QHBoxLayout()
        date_to_layout.setContentsMargins(0, 0, 0, 0)
        date_to_layout.addWidget(self.use_date_to_check)
        date_to_layout.addWidget(self.date_to_input)

        controls_layout.addLayout(date_from_layout, 3, 0, 1, 2)
        controls_layout.addLayout(date_to_layout, 3, 2, 1, 2)
        controls_layout.addWidget(self.clear_filters_button, 3, 4)
        controls_layout.addWidget(self.results_label, 3, 5)

        controls_layout.addWidget(QLabel("Export Folder"), 4, 0)
        controls_layout.addWidget(self.export_dir_input, 4, 1, 1, 4)
        controls_layout.addWidget(self.export_dir_button, 4, 5)

        quick_layout = QHBoxLayout()
        quick_layout.setContentsMargins(0, 0, 0, 0)
        quick_layout.setSpacing(8)
        quick_layout.addWidget(self.quick_open_button)
        quick_layout.addWidget(self.quick_in_progress_button)
        quick_layout.addWidget(self.quick_pending_button)
        quick_layout.addWidget(self.quick_resolved_button)
        quick_layout.addWidget(self.quick_archived_button)
        quick_layout.addStretch(1)
        controls_layout.addLayout(quick_layout, 5, 0, 1, 6)

        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        actions_layout.addWidget(self.new_button)
        actions_layout.addWidget(self.open_button)
        actions_layout.addWidget(self.star_button)
        actions_layout.addWidget(self.pin_button)
        actions_layout.addWidget(self.duplicate_button)
        actions_layout.addWidget(self.archive_button)
        actions_layout.addWidget(self.reopen_button)
        actions_layout.addWidget(self.delete_button)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.export_csv_button)
        actions_layout.addWidget(self.export_excel_button)
        actions_layout.addWidget(self.export_pdf_button)
        actions_layout.addWidget(self.refresh_button)
        controls_layout.addLayout(actions_layout, 6, 0, 1, 6)

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
        self.table.setSortingEnabled(True)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(controls_card)
        root.addWidget(self.table, 1)

        self.new_button.clicked.connect(self._handle_new_ticket)
        self.open_button.clicked.connect(self.open_selected_ticket)
        self.star_button.clicked.connect(self.toggle_selected_starred)
        self.pin_button.clicked.connect(self.toggle_selected_pinned)
        self.duplicate_button.clicked.connect(self.duplicate_selected_ticket)
        self.archive_button.clicked.connect(self.archive_selected_ticket)
        self.reopen_button.clicked.connect(self.reopen_selected_ticket)
        self.delete_button.clicked.connect(self.delete_selected_ticket)
        self.refresh_button.clicked.connect(self.reload_table)
        self.export_dir_button.clicked.connect(self.set_export_directory_ui)
        self.export_csv_button.clicked.connect(self.export_filtered_csv)
        self.export_excel_button.clicked.connect(self.export_filtered_excel)
        self.export_pdf_button.clicked.connect(self.export_selected_ticket_pdf)

        self.search_input.textChanged.connect(lambda _text: self.reload_table())
        self.status_filter.currentIndexChanged.connect(lambda _index: self.reload_table())
        self.priority_filter.currentIndexChanged.connect(lambda _index: self.reload_table())
        self.category_filter.currentIndexChanged.connect(lambda _index: self.reload_table())
        self.client_filter.currentIndexChanged.connect(lambda _index: self.reload_table())
        self.va_filter.currentIndexChanged.connect(lambda _index: self.reload_table())
        self.archived_only_check.stateChanged.connect(lambda _state: self.reload_table())
        self.with_attachments_only_check.stateChanged.connect(lambda _state: self.reload_table())

        self.use_date_from_check.stateChanged.connect(self._on_date_filter_toggled)
        self.use_date_to_check.stateChanged.connect(self._on_date_filter_toggled)
        self.date_from_input.dateChanged.connect(lambda _date: self.reload_table())
        self.date_to_input.dateChanged.connect(lambda _date: self.reload_table())

        self.clear_filters_button.clicked.connect(self.clear_filters)

        self.quick_open_button.clicked.connect(lambda: self._apply_quick_status("Open"))
        self.quick_in_progress_button.clicked.connect(lambda: self._apply_quick_status("In Progress"))
        self.quick_pending_button.clicked.connect(self._apply_quick_pending)
        self.quick_resolved_button.clicked.connect(lambda: self._apply_quick_status("Resolved"))
        self.quick_archived_button.clicked.connect(self._apply_quick_archived)

        self.table.cellDoubleClicked.connect(lambda _row, _col: self.open_selected_ticket())

        self.reload_filter_options()
        self.reload_table()

    def reload_filter_options(self) -> None:
        selected = {
            "status": self.status_filter.currentText(),
            "priority": self.priority_filter.currentText(),
            "category": self.category_filter.currentText(),
            "client": self.client_filter.currentText(),
            "va": self.va_filter.currentText(),
        }

        options = get_ticket_filter_options()
        self._set_combo_items(self.status_filter, options.get("statuses", []), selected["status"])
        self._set_combo_items(self.priority_filter, options.get("priorities", []), selected["priority"])
        self._set_combo_items(self.category_filter, options.get("categories", []), selected["category"])
        self._set_combo_items(self.client_filter, options.get("clients", []), selected["client"])
        self._set_combo_items(self.va_filter, options.get("vas", []), selected["va"])

    def reload_table(self) -> None:
        try:
            tickets = search_tickets(self._collect_filters())
        except Exception as exc:  # pragma: no cover - safety guard
            QMessageBox.critical(self, "Load Failed", f"Unable to load tickets.\n\n{exc}")
            return

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for row_index, ticket in enumerate(tickets):
            self.table.insertRow(row_index)
            values = [
                str(ticket.get("id") or ""),
                "★" if int(ticket.get("starred") or 0) else "",
                "📌" if int(ticket.get("pinned") or 0) else "",
                str(ticket.get("ticket_id") or ""),
                str(ticket.get("title") or ""),
                str(ticket.get("client_name") or ""),
                str(ticket.get("va_name") or ""),
                str(ticket.get("category") or ""),
                str(ticket.get("priority") or ""),
                str(ticket.get("status") or ""),
                str(ticket.get("assigned_to") or ""),
                str(ticket.get("tags_text") or ""),
                "Yes" if int(ticket.get("archived") or 0) else "No",
                "Yes" if int(ticket.get("has_attachments") or 0) else "No",
                str(ticket.get("updated_at") or ""),
                str(ticket.get("created_at") or ""),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, int(ticket["id"]))
                self.table.setItem(row_index, col_index, item)

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
        self.results_label.setText(f"{len(tickets)} tickets")

    def _collect_filters(self) -> dict[str, Any]:
        date_from = (
            self.date_from_input.date().toString("yyyy-MM-dd") if self.use_date_from_check.isChecked() else None
        )
        date_to = self.date_to_input.date().toString("yyyy-MM-dd") if self.use_date_to_check.isChecked() else None

        return {
            "search_text": self.search_input.text(),
            "status": self.status_filter.currentText(),
            "priority": self.priority_filter.currentText(),
            "category": self.category_filter.currentText(),
            "client_name": self.client_filter.currentText(),
            "va_name": self.va_filter.currentText(),
            "date_from": date_from,
            "date_to": date_to,
            "archived_only": self.archived_only_check.isChecked(),
            "with_attachments_only": self.with_attachments_only_check.isChecked(),
            "include_archived": True,
        }

    def clear_filters(self) -> None:
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.priority_filter.setCurrentIndex(0)
        self.category_filter.setCurrentIndex(0)
        self.client_filter.setCurrentIndex(0)
        self.va_filter.setCurrentIndex(0)
        self.archived_only_check.setChecked(False)
        self.with_attachments_only_check.setChecked(False)
        self.use_date_from_check.setChecked(False)
        self.use_date_to_check.setChecked(False)
        self.date_from_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_input.setDate(QDate.currentDate())
        self.reload_table()

    def _on_date_filter_toggled(self) -> None:
        self.date_from_input.setEnabled(self.use_date_from_check.isChecked())
        self.date_to_input.setEnabled(self.use_date_to_check.isChecked())
        self.reload_table()

    def _apply_quick_status(self, status_value: str) -> None:
        self.archived_only_check.setChecked(False)
        self._set_or_append_filter_text(self.status_filter, status_value)
        self.reload_table()

    def _apply_quick_pending(self) -> None:
        pending_value = "Pending" if self.status_filter.findText("Pending") >= 0 else "Waiting on Client"
        self._apply_quick_status(pending_value)

    def _apply_quick_archived(self) -> None:
        self.status_filter.setCurrentIndex(0)
        self.archived_only_check.setChecked(True)
        self.reload_table()

    def focus_search(self) -> None:
        self.search_input.setFocus()
        self.search_input.selectAll()

    def toggle_selected_starred(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return
        new_state = not bool(int(ticket.get("starred") or 0))
        set_ticket_starred(int(ticket["id"]), new_state)
        QMessageBox.information(self, "Updated", "Ticket star updated.")
        self._after_data_change()

    def toggle_selected_pinned(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return
        new_state = not bool(int(ticket.get("pinned") or 0))
        set_ticket_pinned(int(ticket["id"]), new_state)
        QMessageBox.information(self, "Updated", "Ticket pin updated.")
        self._after_data_change()

    def duplicate_selected_ticket(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return
        new_id = duplicate_ticket(int(ticket["id"]))
        new_ticket = get_ticket_by_db_id(new_id)
        QMessageBox.information(
            self,
            "Ticket Duplicated",
            f"Created {new_ticket.get('ticket_id') if new_ticket else new_id}.",
        )
        self._after_data_change()

    def set_export_directory_ui(self) -> None:
        current = self.export_dir_input.text().strip() or get_export_directory()
        directory = QFileDialog.getExistingDirectory(self, "Select Export Folder", current)
        if not directory:
            return
        saved = set_export_directory(directory)
        self.export_dir_input.setText(saved)

    def export_filtered_csv(self) -> None:
        rows = search_tickets(self._collect_filters())
        if not rows:
            QMessageBox.information(self, "No Data", "No tickets to export with current filters.")
            return
        default_path = Path(self.export_dir_input.text()) / f"tickets_export_{datetime.now():%Y%m%d_%H%M%S}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Filtered Tickets to CSV",
            str(default_path),
            "CSV Files (*.csv)",
        )
        if not file_path:
            return
        try:
            export_tickets_to_csv(rows, Path(file_path))
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"CSV export failed.\n\n{exc}")
            return
        QMessageBox.information(self, "Export Complete", f"CSV exported:\n{file_path}")

    def export_filtered_excel(self) -> None:
        rows = search_tickets(self._collect_filters())
        if not rows:
            QMessageBox.information(self, "No Data", "No tickets to export with current filters.")
            return
        default_path = Path(self.export_dir_input.text()) / f"tickets_export_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Filtered Tickets to Excel",
            str(default_path),
            "Excel Files (*.xlsx)",
        )
        if not file_path:
            return
        try:
            export_tickets_to_excel(rows, Path(file_path))
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Excel export failed.\n\n{exc}")
            return
        QMessageBox.information(self, "Export Complete", f"Excel exported:\n{file_path}")

    def export_selected_ticket_pdf(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return

        ticket_id = str(ticket.get("ticket_id") or "ticket")
        default_path = Path(self.export_dir_input.text()) / f"{ticket_id}_details.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Ticket to PDF",
            str(default_path),
            "PDF Files (*.pdf)",
        )
        if not file_path:
            return

        try:
            notes = list_ticket_notes(int(ticket["id"]))
            attachments = list_ticket_attachments(int(ticket["id"]))
            history = list_ticket_history(int(ticket["id"]))
            export_ticket_to_pdf(ticket, notes, attachments, history, Path(file_path))
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"PDF export failed.\n\n{exc}")
            return

        QMessageBox.information(self, "Export Complete", f"PDF exported:\n{file_path}")

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
            self._after_data_change()

    def archive_selected_ticket(self) -> None:
        ticket = self._selected_ticket()
        if ticket is None:
            QMessageBox.information(self, "No Selection", "Select a ticket first.")
            return

        if int(ticket.get("archived") or 0):
            QMessageBox.information(self, "Already Archived", "Selected ticket is already archived.")
            return

        prompt = QMessageBox.question(self, "Confirm Archive", f"Archive ticket {ticket.get('ticket_id')}?")
        if prompt != QMessageBox.StandardButton.Yes:
            return

        archive_ticket(int(ticket["id"]))
        QMessageBox.information(self, "Success", "Ticket archived.")
        self._after_data_change()

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
        self._after_data_change()

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
        self._after_data_change()

    def _after_data_change(self) -> None:
        self.reload_filter_options()
        self.reload_table()
        if self._on_data_changed:
            self._on_data_changed()

    @staticmethod
    def _set_combo_items(combo: QComboBox, values: list[str], selected: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("")
        combo.addItems(values)
        index = combo.findText(selected)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    @staticmethod
    def _set_or_append_filter_text(combo: QComboBox, value: str) -> None:
        if not value:
            combo.setCurrentIndex(0)
            return
        index = combo.findText(value)
        if index < 0:
            combo.addItem(value)
            index = combo.findText(value)
        combo.setCurrentIndex(index)
