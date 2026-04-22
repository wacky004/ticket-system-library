"""Reports page widgets and filtered reporting views."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
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
    get_report_guide_count_by_category,
    get_report_guide_count_by_difficulty,
    get_report_priority_distribution,
    get_report_resolved_vs_unresolved,
    get_report_ticket_count_by_category,
    get_report_ticket_count_by_client,
    get_report_ticket_count_by_date,
    get_report_ticket_count_by_technician,
)


class ReportsPage(QWidget):
    """Reporting page with date-filtered ticket aggregates."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("PageRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(12)

        title = QLabel("Reports")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Date-filtered operational reporting and distribution summaries.")
        subtitle.setObjectName("PageSubtitle")

        controls = QFrame()
        controls.setObjectName("Card")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 12, 12, 12)
        controls_layout.setSpacing(10)

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

        self.refresh_button = QPushButton("Refresh Reports")
        self.refresh_button.setObjectName("PrimaryButton")
        self.clear_button = QPushButton("Clear Date Filters")
        self.clear_button.setObjectName("SecondaryButton")

        controls_layout.addWidget(self.use_date_from_check)
        controls_layout.addWidget(self.date_from_input)
        controls_layout.addWidget(self.use_date_to_check)
        controls_layout.addWidget(self.date_to_input)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.refresh_button)

        tables_grid = QGridLayout()
        tables_grid.setHorizontalSpacing(12)
        tables_grid.setVerticalSpacing(12)

        self.by_date = self._build_table_card("Ticket Count by Date", ["Date", "Count"])
        self.by_client = self._build_table_card("Ticket Count by Client", ["Client", "Count"])
        self.by_category = self._build_table_card("Ticket Count by Category", ["Category", "Count"])
        self.by_technician = self._build_table_card("Ticket Count by Technician", ["Technician", "Count"])
        self.resolved_split = self._build_table_card("Resolved vs Unresolved", ["Status Group", "Count"])
        self.priority_dist = self._build_table_card("Priority Distribution", ["Priority", "Count"])
        self.guide_by_category = self._build_table_card("Guide Count by Category", ["Category", "Count"])
        self.guide_by_difficulty = self._build_table_card("Guide Count by Difficulty", ["Difficulty", "Count"])

        tables_grid.addWidget(self.by_date["card"], 0, 0)
        tables_grid.addWidget(self.by_client["card"], 0, 1)
        tables_grid.addWidget(self.by_category["card"], 1, 0)
        tables_grid.addWidget(self.by_technician["card"], 1, 1)
        tables_grid.addWidget(self.resolved_split["card"], 2, 0)
        tables_grid.addWidget(self.priority_dist["card"], 2, 1)
        tables_grid.addWidget(self.guide_by_category["card"], 3, 0)
        tables_grid.addWidget(self.guide_by_difficulty["card"], 3, 1)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(controls)
        root.addLayout(tables_grid, 1)

        self.use_date_from_check.stateChanged.connect(self._on_date_toggle)
        self.use_date_to_check.stateChanged.connect(self._on_date_toggle)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.clear_button.clicked.connect(self.clear_filters)

        self.refresh_data()

    def _on_date_toggle(self) -> None:
        self.date_from_input.setEnabled(self.use_date_from_check.isChecked())
        self.date_to_input.setEnabled(self.use_date_to_check.isChecked())

    def clear_filters(self) -> None:
        self.use_date_from_check.setChecked(False)
        self.use_date_to_check.setChecked(False)
        self.date_from_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_input.setDate(QDate.currentDate())
        self.refresh_data()

    def _filters(self) -> tuple[str | None, str | None]:
        date_from = self.date_from_input.date().toString("yyyy-MM-dd") if self.use_date_from_check.isChecked() else None
        date_to = self.date_to_input.date().toString("yyyy-MM-dd") if self.use_date_to_check.isChecked() else None
        return date_from, date_to

    def refresh_data(self) -> None:
        date_from, date_to = self._filters()

        self._fill_table(
            self.by_date["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_ticket_count_by_date(date_from, date_to)],
        )
        self._fill_table(
            self.by_client["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_ticket_count_by_client(date_from, date_to)],
        )
        self._fill_table(
            self.by_category["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_ticket_count_by_category(date_from, date_to)],
        )
        self._fill_table(
            self.by_technician["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_ticket_count_by_technician(date_from, date_to)],
        )
        self._fill_table(
            self.resolved_split["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_resolved_vs_unresolved(date_from, date_to)],
        )
        self._fill_table(
            self.priority_dist["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_priority_distribution(date_from, date_to)],
        )
        self._fill_table(
            self.guide_by_category["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_guide_count_by_category(date_from, date_to)],
        )
        self._fill_table(
            self.guide_by_difficulty["table"],
            [[r.get("label", ""), r.get("count", 0)] for r in get_report_guide_count_by_difficulty(date_from, date_to)],
        )

    def _build_table_card(self, title: str, columns: list[str]) -> dict[str, Any]:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_widget = QLabel(title)
        title_widget.setObjectName("SectionTitle")
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
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
