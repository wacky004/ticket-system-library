"""Main application window and navigation shell."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.config import APP_NAME
from app.ui.backups import BackupsPage
from app.ui.pages import DashboardPage, PlaceholderPage
from app.ui.reports import ReportsPage
from app.ui.settings import SettingsPage
from app.ui.tickets import NewTicketPage, TicketsPage
from app.services.backup import create_backup, get_auto_backup_on_exit, get_configured_backup_root


@dataclass(frozen=True)
class NavItem:
    name: str
    subtitle: str


NAV_ITEMS = [
    NavItem("Dashboard", "Overview metrics and startup insights will live here."),
    NavItem("Tickets", "Ticket list, filters, and search will be built in the next phase."),
    NavItem("New Ticket", "Ticket creation form and validation will be added next."),
    NavItem("Reports", "Reporting widgets and exports will be added in a later phase."),
    NavItem("Backups", "Backup tools and restore workflow will be implemented later."),
    NavItem("Settings", "Theme, profile, and system settings controls are coming soon."),
]


class MainWindow(QMainWindow):
    """Primary application shell with left navigation and stacked pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1100, 700)

        container = QWidget()
        container.setObjectName("MainContainer")
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        self.stack = self._build_pages()

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack, 1)

        self.setCentralWidget(container)

        self._nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        brand = QLabel("Ticket Library")
        brand.setObjectName("BrandLabel")

        version = QLabel("Desktop")
        version.setObjectName("BrandSubLabel")

        layout.addWidget(brand)
        layout.addWidget(version)

        self._nav_buttons: list[QPushButton] = []
        for index, item in enumerate(NAV_ITEMS):
            button = QPushButton(item.name)
            button.setObjectName("NavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self._set_page(i))

            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)

        footer = QLabel("Phase 7 Exports")
        footer.setObjectName("SidebarFooter")
        layout.addWidget(footer)

        return sidebar

    def _build_pages(self) -> QStackedWidget:
        stack = QStackedWidget()
        stack.setObjectName("MainStack")
        stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tickets_page = TicketsPage(
            on_request_new_ticket=lambda: self._set_page(2),
            on_data_changed=self._sync_ticket_views,
        )
        self.new_ticket_page = NewTicketPage(on_ticket_saved=self._sync_ticket_views)
        self.dashboard_page = DashboardPage()
        self.reports_page = ReportsPage()
        self.backups_page = BackupsPage()
        self.settings_page = SettingsPage()

        for item in NAV_ITEMS:
            if item.name == "Dashboard":
                stack.addWidget(self.dashboard_page)
            elif item.name == "Tickets":
                stack.addWidget(self.tickets_page)
            elif item.name == "New Ticket":
                stack.addWidget(self.new_ticket_page)
            elif item.name == "Reports":
                stack.addWidget(self.reports_page)
            elif item.name == "Backups":
                stack.addWidget(self.backups_page)
            elif item.name == "Settings":
                stack.addWidget(self.settings_page)
            else:
                stack.addWidget(PlaceholderPage(item.name, item.subtitle))

        return stack

    def _set_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self._nav_buttons):
            button.setChecked(button_index == index)

        if NAV_ITEMS[index].name == "New Ticket":
            self.new_ticket_page.refresh_ticket_preview()
        elif NAV_ITEMS[index].name == "Dashboard":
            self.dashboard_page.refresh_data()
        elif NAV_ITEMS[index].name == "Reports":
            self.reports_page.refresh_data()
        elif NAV_ITEMS[index].name == "Backups":
            self.backups_page.refresh_data()

    def _sync_ticket_views(self) -> None:
        self.tickets_page.reload_table()
        self.new_ticket_page.refresh_ticket_preview()
        self.dashboard_page.refresh_data()
        self.reports_page.refresh_data()
        self.backups_page.refresh_data()

    def closeEvent(self, event: QCloseEvent) -> None:
        if get_auto_backup_on_exit() and get_configured_backup_root() is not None:
            try:
                create_backup(backup_type="auto_exit")
            except Exception as exc:
                QMessageBox.warning(self, "Auto Backup Failed", f"Automatic backup failed.\n\n{exc}")
        super().closeEvent(event)
