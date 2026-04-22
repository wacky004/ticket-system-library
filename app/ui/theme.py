"""Theme handling and stylesheet creation."""

from __future__ import annotations

from enum import Enum


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


PALETTES = {
    ThemeMode.DARK: {
        "bg": "#0f141d",
        "surface": "#171f2b",
        "surface_2": "#1e2838",
        "text": "#f2f5fa",
        "muted": "#93a4bb",
        "accent": "#4fc3f7",
        "accent_soft": "#2f4f64",
        "border": "#2a3a4f",
    },
    ThemeMode.LIGHT: {
        "bg": "#f3f6fb",
        "surface": "#ffffff",
        "surface_2": "#eef3fb",
        "text": "#111827",
        "muted": "#56657a",
        "accent": "#0f8ecf",
        "accent_soft": "#d7eefa",
        "border": "#d6deea",
    },
}


def build_stylesheet(mode: ThemeMode = ThemeMode.DARK) -> str:
    """Return an application stylesheet for the requested mode."""
    palette = PALETTES[mode]

    return f"""
    QWidget {{
        color: {palette['text']};
        background-color: {palette['bg']};
        font-family: 'Segoe UI';
        font-size: 10.5pt;
    }}

    QMainWindow {{
        background-color: {palette['bg']};
    }}

    #Sidebar {{
        background-color: {palette['surface']};
        border-right: 1px solid {palette['border']};
    }}

    #BrandLabel {{
        font-size: 16pt;
        font-weight: 700;
        color: {palette['text']};
    }}

    #BrandSubLabel {{
        margin-bottom: 14px;
        color: {palette['muted']};
        font-size: 10pt;
    }}

    #NavButton {{
        text-align: left;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px 12px;
        background-color: transparent;
        color: {palette['text']};
    }}

    #NavButton:hover {{
        border-color: {palette['border']};
        background-color: {palette['surface_2']};
    }}

    #NavButton:checked {{
        border-color: {palette['accent']};
        background-color: {palette['accent_soft']};
        color: {palette['text']};
        font-weight: 600;
    }}

    #SidebarFooter {{
        color: {palette['muted']};
        padding-top: 6px;
    }}

    #MainStack {{
        background-color: {palette['bg']};
    }}

    #PageRoot {{
        background-color: {palette['bg']};
    }}

    #PageTitle {{
        font-size: 21pt;
        font-weight: 700;
        color: {palette['text']};
    }}

    #PageSubtitle {{
        font-size: 11pt;
        color: {palette['muted']};
        max-width: 700px;
    }}

    QLabel {{
        background: transparent;
    }}

    QFrame#Card {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 10px;
    }}

    QLineEdit, QTextEdit, QComboBox, QTableWidget {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 8px;
        padding: 6px 8px;
        selection-background-color: {palette['accent']};
        selection-color: {palette['text']};
    }}

    QTextEdit {{
        padding-top: 8px;
    }}

    QComboBox::drop-down {{
        border: 0px;
        width: 20px;
    }}

    QHeaderView::section {{
        background-color: {palette['surface_2']};
        color: {palette['text']};
        border: 0px;
        border-right: 1px solid {palette['border']};
        border-bottom: 1px solid {palette['border']};
        padding: 8px;
        font-weight: 600;
    }}

    QTableWidget {{
        gridline-color: {palette['border']};
    }}

    QPushButton#PrimaryButton {{
        border: 1px solid {palette['accent']};
        border-radius: 8px;
        background-color: {palette['accent']};
        color: {palette['bg']};
        font-weight: 600;
        padding: 8px 14px;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: {palette['text']};
        border-color: {palette['text']};
    }}

    QPushButton#SecondaryButton {{
        border: 1px solid {palette['border']};
        border-radius: 8px;
        background-color: {palette['surface_2']};
        color: {palette['text']};
        padding: 8px 14px;
    }}

    QPushButton#SecondaryButton:hover {{
        border-color: {palette['accent']};
    }}

    QPushButton#DangerButton {{
        border: 1px solid #d86060;
        border-radius: 8px;
        background-color: #6b2f2f;
        color: #ffdede;
        padding: 8px 14px;
        font-weight: 600;
    }}

    QPushButton#DangerButton:hover {{
        background-color: #8e3b3b;
    }}

    #MetaLabel {{
        color: {palette['muted']};
        font-size: 9.5pt;
    }}

    QTabWidget::pane {{
        border: 1px solid {palette['border']};
        border-radius: 8px;
        top: -1px;
        background-color: {palette['bg']};
    }}

    QTabBar::tab {{
        background-color: {palette['surface_2']};
        border: 1px solid {palette['border']};
        border-bottom: 0;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 14px;
        margin-right: 4px;
        color: {palette['text']};
    }}

    QTabBar::tab:selected {{
        background-color: {palette['surface']};
        border-color: {palette['accent']};
    }}

    QListWidget#AttachmentList {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 8px;
        padding: 8px;
    }}

    QLabel#AttachmentPreview {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 8px;
    }}

    QFrame#SummaryCard {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 10px;
    }}

    #SummaryCardLabel {{
        color: {palette['muted']};
        font-size: 10pt;
    }}

    #SummaryCardValue {{
        color: {palette['text']};
        font-size: 18pt;
        font-weight: 700;
    }}

    #SectionTitle {{
        color: {palette['text']};
        font-size: 11pt;
        font-weight: 600;
    }}

    QTableWidget#DashboardTable {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 8px;
        gridline-color: {palette['border']};
    }}
    """
