"""UI page widgets."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db.database import (
    get_dashboard_summary,
    get_last_backup_status,
    get_ticket_count_by_category,
    get_ticket_count_by_priority,
    list_recent_guides,
    list_recent_tickets,
    list_upcoming_follow_ups,
)


class PlaceholderPage(QWidget):
    """Simple placeholder content used during foundation phase."""

    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("PageRoot")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)


class SummaryCard(QFrame):
    """Small metric card used on dashboard."""

    def __init__(self, label: str) -> None:
        super().__init__()
        self.setObjectName("SummaryCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.label_widget = QLabel(label)
        self.label_widget.setObjectName("SummaryCardLabel")

        self.value_widget = QLabel("0")
        self.value_widget.setObjectName("SummaryCardValue")

        layout.addWidget(self.label_widget)
        layout.addWidget(self.value_widget)
        layout.addStretch(1)

    def set_value(self, value: int) -> None:
        self.value_widget.setText(str(value))


class DashboardPage(QWidget):
    """Live dashboard with summary cards and ticket insights."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PageRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        header_row = QHBoxLayout()
        header_title_col = QVBoxLayout()
        header_title_col.setSpacing(4)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Live overview of ticket operations and upcoming work.")
        subtitle.setObjectName("PageSubtitle")

        header_title_col.addWidget(title)
        header_title_col.addWidget(subtitle)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")

        header_row.addLayout(header_title_col, 1)
        header_row.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignTop)

        self.cards_grid = QGridLayout()
        self.cards_grid.setHorizontalSpacing(10)
        self.cards_grid.setVerticalSpacing(10)

        self.card_total = SummaryCard("Total Tickets")
        self.card_guides = SummaryCard("Total Guides")
        self.card_open = SummaryCard("Open Tickets")
        self.card_in_progress = SummaryCard("In Progress")
        self.card_pending = SummaryCard("Pending")
        self.card_resolved = SummaryCard("Resolved")
        self.card_archived = SummaryCard("Archived")

        cards = [
            self.card_total,
            self.card_guides,
            self.card_open,
            self.card_in_progress,
            self.card_pending,
            self.card_resolved,
            self.card_archived,
        ]
        for idx, card in enumerate(cards):
            self.cards_grid.addWidget(card, idx // 4, idx % 4)

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(12)
        content_grid.setVerticalSpacing(12)

        self.recent_table = self._build_table(
            "Recent Tickets",
            ["Ticket ID", "Title", "Client", "Status", "Priority", "Updated"],
        )
        self.recent_guides_table = self._build_table(
            "Recent Guides",
            ["Guide ID", "Title", "Category", "Difficulty", "Updated"],
        )
        self.follow_ups_table = self._build_table(
            "Upcoming Follow-ups",
            ["Follow-up Date", "Ticket ID", "Title", "Client", "Status"],
        )
        self.priority_table = self._build_table("By Priority", ["Priority", "Count"])
        self.category_table = self._build_table("By Category", ["Category", "Count"])

        backup_card = QFrame()
        backup_card.setObjectName("Card")
        backup_layout = QVBoxLayout(backup_card)
        backup_layout.setContentsMargins(12, 12, 12, 12)
        backup_layout.setSpacing(6)

        backup_title = QLabel("Last Backup Status")
        backup_title.setObjectName("SectionTitle")
        self.backup_status = QLabel("Placeholder")
        self.backup_status.setObjectName("SummaryCardValue")
        self.backup_label = QLabel("No backups yet")
        self.backup_label.setObjectName("MetaLabel")
        self.backup_timestamp = QLabel("-")
        self.backup_timestamp.setObjectName("MetaLabel")

        backup_layout.addWidget(backup_title)
        backup_layout.addWidget(self.backup_status)
        backup_layout.addWidget(self.backup_label)
        backup_layout.addWidget(self.backup_timestamp)
        backup_layout.addStretch(1)

        content_grid.addWidget(self.recent_table["card"], 0, 0, 1, 2)
        content_grid.addWidget(self.recent_guides_table["card"], 0, 2, 1, 2)
        content_grid.addWidget(self.follow_ups_table["card"], 1, 0, 1, 2)
        content_grid.addWidget(backup_card, 1, 2, 1, 2)
        content_grid.addWidget(self.priority_table["card"], 2, 0, 1, 2)
        content_grid.addWidget(self.category_table["card"], 2, 2, 1, 2)

        root.addLayout(header_row)
        root.addLayout(self.cards_grid)
        root.addLayout(content_grid, 1)

        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self) -> None:
        summary = get_dashboard_summary()
        self.card_total.set_value(summary["total"])
        self.card_guides.set_value(summary["guides"])
        self.card_open.set_value(summary["open"])
        self.card_in_progress.set_value(summary["in_progress"])
        self.card_pending.set_value(summary["pending"])
        self.card_resolved.set_value(summary["resolved"])
        self.card_archived.set_value(summary["archived"])

        self._fill_table(
            self.recent_table["table"],
            [
                [
                    row.get("ticket_id") or "",
                    row.get("title") or "",
                    row.get("client_name") or "",
                    row.get("status") or "",
                    row.get("priority") or "",
                    row.get("updated_at") or "",
                ]
                for row in list_recent_tickets(limit=10)
            ],
        )

        self._fill_table(
            self.recent_guides_table["table"],
            [
                [
                    row.get("guide_id") or "",
                    row.get("title") or "",
                    row.get("category") or "",
                    row.get("difficulty") or "",
                    row.get("updated_at") or "",
                ]
                for row in list_recent_guides(limit=10)
            ],
        )

        self._fill_table(
            self.follow_ups_table["table"],
            [
                [
                    row.get("follow_up_date") or "",
                    row.get("ticket_id") or "",
                    row.get("title") or "",
                    row.get("client_name") or "",
                    row.get("status") or "",
                ]
                for row in list_upcoming_follow_ups(limit=10)
            ],
        )

        self._fill_table(
            self.priority_table["table"],
            [[row.get("label") or "", row.get("count") or 0] for row in get_ticket_count_by_priority()],
        )
        self._fill_table(
            self.category_table["table"],
            [[row.get("label") or "", row.get("count") or 0] for row in get_ticket_count_by_category()],
        )

        backup = get_last_backup_status()
        self.backup_status.setText(str(backup["status"]))
        self.backup_label.setText(str(backup["label"]))
        self.backup_timestamp.setText(str(backup["timestamp"]))

    def _build_table(self, title: str, columns: list[str]) -> dict[str, Any]:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_widget = QLabel(title)
        title_widget.setObjectName("SectionTitle")

        table = QTableWidget(0, len(columns))
        table.setObjectName("DashboardTable")
        table.setHorizontalHeaderLabels(columns)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(title_widget)
        layout.addWidget(table, 1)

        return {"card": card, "table": table}

    def _fill_table(self, table: QTableWidget, rows: list[list[Any]]) -> None:
        table.setRowCount(0)
        for row_index, row_values in enumerate(rows):
            table.insertRow(row_index)
            for col_index, value in enumerate(row_values):
                table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()
