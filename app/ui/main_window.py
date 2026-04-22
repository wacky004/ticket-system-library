"""Main application window and navigation shell."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME
from app.db.database import get_app_setting
from app.services.backup import create_backup, get_auto_backup_on_exit, get_configured_backup_root
from app.ui.backups import BackupsPage
from app.ui.guides import GuidesPage
from app.ui.pages import DashboardPage
from app.ui.reports import ReportsPage
from app.ui.settings import SettingsPage
from app.ui.theme import ThemeMode, build_stylesheet
from app.ui.tickets import NewTicketPage, TicketsPage


@dataclass(frozen=True)
class NavItem:
    name: str
    icon: str


NAV_ITEMS = [
    NavItem("Dashboard", "▦"),
    NavItem("Tickets", "◫"),
    NavItem("Guides", "◧"),
    NavItem("Reports", "◷"),
    NavItem("Backups", "⤓"),
    NavItem("Settings", "⚙"),
]


class MainWindow(QMainWindow):
    """Workspace shell with collapsible sidebar and page stack."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1280, 760)
        self._sidebar_expanded = True

        container = QWidget()
        container.setObjectName("MainShell")
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        self.stack = self._build_pages()

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(container)

        self._set_page(0)
        self._configure_shortcuts()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QFrame()
        header.setObjectName("SidebarHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(4, 4, 4, 8)
        header_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.setSpacing(6)

        self.brand_label = QLabel("Ticket Library Desktop")
        self.brand_label.setObjectName("BrandLabel")
        self.toggle_sidebar_button = QPushButton("⟨")
        self.toggle_sidebar_button.setObjectName("SecondaryButton")
        self.toggle_sidebar_button.setFixedWidth(34)
        self.toggle_sidebar_button.clicked.connect(self._toggle_sidebar)

        brand_row.addWidget(self.brand_label, 1)
        brand_row.addWidget(self.toggle_sidebar_button)

        company_name = get_app_setting("company_name") or "Ticket Library"
        self.brand_sub_label = QLabel(company_name)
        self.brand_sub_label.setObjectName("BrandSubLabel")

        header_layout.addLayout(brand_row)
        header_layout.addWidget(self.brand_sub_label)
        layout.addWidget(header)

        self._nav_buttons: list[QPushButton] = []
        for index, item in enumerate(NAV_ITEMS):
            button = QPushButton(f"{item.icon}  {item.name}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, i=index: self._set_page(i))
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)
        self.footer_label = QLabel("Support Workspace")
        self.footer_label.setObjectName("SidebarFooter")
        layout.addWidget(self.footer_label)
        return sidebar

    def _build_pages(self) -> QStackedWidget:
        stack = QStackedWidget()
        stack.setObjectName("MainStack")
        stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.dashboard_page = DashboardPage()
        self.tickets_page = TicketsPage(on_request_new_ticket=self._open_new_ticket_page, on_data_changed=self._sync_views)
        self.guides_page = GuidesPage(on_data_changed=self._sync_views)
        self.reports_page = ReportsPage()
        self.backups_page = BackupsPage()
        self.settings_page = SettingsPage(on_theme_changed=self._apply_theme)
        self.new_ticket_page = NewTicketPage(on_ticket_saved=self._sync_views)

        stack.addWidget(self.dashboard_page)
        stack.addWidget(self.tickets_page)
        stack.addWidget(self.guides_page)
        stack.addWidget(self.reports_page)
        stack.addWidget(self.backups_page)
        stack.addWidget(self.settings_page)
        stack.addWidget(self.new_ticket_page)
        self._new_ticket_page_index = 6
        return stack

    def _toggle_sidebar(self) -> None:
        self._sidebar_expanded = not self._sidebar_expanded
        if self._sidebar_expanded:
            self.sidebar.setFixedWidth(250)
            self.brand_label.show()
            self.brand_sub_label.show()
            self.footer_label.show()
            self.toggle_sidebar_button.setText("⟨")
            for i, item in enumerate(NAV_ITEMS):
                self._nav_buttons[i].setText(f"{item.icon}  {item.name}")
        else:
            self.sidebar.setFixedWidth(74)
            self.brand_label.hide()
            self.brand_sub_label.hide()
            self.footer_label.hide()
            self.toggle_sidebar_button.setText("⟩")
            for i, item in enumerate(NAV_ITEMS):
                self._nav_buttons[i].setText(item.icon)

    def _set_page(self, index: int) -> None:
        current_index = self.stack.currentIndex()
        if current_index == self._new_ticket_page_index and index != self._new_ticket_page_index:
            if not self.new_ticket_page.confirm_leave():
                return

        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self._nav_buttons):
            button.setChecked(button_index == index)

        current_name = NAV_ITEMS[index].name
        if current_name == "Dashboard":
            self.dashboard_page.refresh_data()
        elif current_name == "Tickets":
            self.tickets_page.reload_table()
        elif current_name == "Guides":
            self.guides_page.reload_table()
        elif current_name == "Reports":
            self.reports_page.refresh_data()
        elif current_name == "Backups":
            self.backups_page.refresh_data()

    def _open_new_ticket_page(self) -> None:
        self.stack.setCurrentIndex(self._new_ticket_page_index)
        self.new_ticket_page.refresh_ticket_preview()
        for button in self._nav_buttons:
            button.setChecked(False)

    def _sync_views(self) -> None:
        self.tickets_page.reload_filter_options()
        self.tickets_page.reload_table()
        self.guides_page.reload_table()
        self.dashboard_page.refresh_data()
        self.reports_page.refresh_data()
        self.backups_page.refresh_data()
        self.new_ticket_page.refresh_ticket_preview()

    def _apply_theme(self, mode: str) -> None:
        app = QApplication.instance()
        if app is None:
            return
        theme = ThemeMode.LIGHT if str(mode).lower() == "light" else ThemeMode.DARK
        app.setStyleSheet(build_stylesheet(theme))

    def _configure_shortcuts(self) -> None:
        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(self._open_new_ticket_page)

        shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_find.activated.connect(self._focus_ticket_search)

        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self._handle_save_shortcut)

    def _focus_ticket_search(self) -> None:
        self._set_page(1)
        self.tickets_page.focus_search()

    def _handle_save_shortcut(self) -> None:
        if self.stack.currentIndex() == self._new_ticket_page_index:
            self.new_ticket_page.handle_save_shortcut()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.stack.currentIndex() == self._new_ticket_page_index:
            if not self.new_ticket_page.confirm_leave():
                event.ignore()
                return

        if get_auto_backup_on_exit() and get_configured_backup_root() is not None:
            try:
                create_backup(backup_type="auto_exit")
            except Exception as exc:
                QMessageBox.warning(self, "Auto Backup Failed", f"Automatic backup failed.\n\n{exc}")
        super().closeEvent(event)
