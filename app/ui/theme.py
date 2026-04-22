"""Theme handling and stylesheet creation."""

from __future__ import annotations

from enum import Enum


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


PALETTES = {
    ThemeMode.DARK: {
        "bg": "#0f1722",
        "surface": "#161f2b",
        "surface_soft": "#1c2736",
        "surface_hover": "#223146",
        "text": "#e9eef7",
        "muted": "#9ba9bc",
        "accent": "#2c8ef4",
        "accent_soft": "#1d3558",
        "border": "#2a3a51",
        "shadow": "rgba(0,0,0,0.24)",
    },
    ThemeMode.LIGHT: {
        "bg": "#f3f6fb",
        "surface": "#ffffff",
        "surface_soft": "#f7f9fd",
        "surface_hover": "#edf3fc",
        "text": "#152235",
        "muted": "#5f6f85",
        "accent": "#1f76d2",
        "accent_soft": "#e3efff",
        "border": "#d7e1ef",
        "shadow": "rgba(0,0,0,0.08)",
    },
}


def build_stylesheet(mode: ThemeMode = ThemeMode.DARK) -> str:
    palette = PALETTES[mode]
    return f"""
    QWidget {{
        color: {palette['text']};
        background-color: {palette['bg']};
        font-family: "Segoe UI";
        font-size: 10pt;
    }}

    QMainWindow {{
        background-color: {palette['bg']};
    }}

    QLabel {{
        background: transparent;
    }}

    #PageRoot {{
        background-color: {palette['bg']};
    }}

    #PageTitle {{
        font-size: 18pt;
        font-weight: 700;
        color: {palette['text']};
    }}

    #PageSubtitle {{
        font-size: 10pt;
        color: {palette['muted']};
    }}

    #MainShell {{
        background-color: {palette['bg']};
    }}

    #Sidebar {{
        background-color: {palette['surface']};
        border-right: 1px solid {palette['border']};
    }}

    #SidebarHeader {{
        background-color: transparent;
        border-bottom: 1px solid {palette['border']};
    }}

    #BrandLabel {{
        font-size: 13pt;
        font-weight: 700;
    }}

    #BrandSubLabel {{
        color: {palette['muted']};
        font-size: 9pt;
    }}

    #NavButton {{
        text-align: left;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 9px 10px;
        background-color: transparent;
        font-weight: 500;
    }}

    #NavButton[compact="true"] {{
        text-align: center;
        padding: 9px 2px;
        font-size: 9.3pt;
        font-weight: 700;
        min-height: 34px;
    }}

    #NavButton:hover {{
        background-color: {palette['surface_hover']};
        border-color: {palette['border']};
    }}

    #NavButton:checked {{
        background-color: {palette['accent_soft']};
        border-color: {palette['accent']};
        color: {palette['text']};
        font-weight: 700;
    }}

    #SidebarFooter {{
        color: {palette['muted']};
        font-size: 8.8pt;
    }}

    #Sidebar[collapsed="true"] #SidebarHeader {{
        border-bottom: 0;
    }}

    QFrame#Card, QFrame#SectionBlock, QFrame#SummaryCard, QFrame#ReadableContentCard {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 12px;
    }}

    QLineEdit, QTextEdit, QTextBrowser, QComboBox, QDateEdit, QTableWidget, QListWidget {{
        background-color: {palette['surface']};
        border: 1px solid {palette['border']};
        border-radius: 10px;
        padding: 6px 8px;
        selection-background-color: {palette['accent']};
        selection-color: white;
    }}

    QTextBrowser#ReadableViewer {{
        font-size: 10.8pt;
        line-height: 1.5;
        padding: 12px;
    }}

    QTextBrowser#ReadableViewer p {{
        margin: 0 0 8px 0;
    }}

    QTextBrowser#ReadableViewer ul {{
        margin-top: 0;
        margin-bottom: 8px;
    }}

    QComboBox::drop-down, QDateEdit::drop-down {{
        border: 0;
        width: 22px;
    }}

    QHeaderView::section {{
        background-color: {palette['surface_soft']};
        border: 0;
        border-right: 1px solid {palette['border']};
        border-bottom: 1px solid {palette['border']};
        font-weight: 600;
        padding: 8px;
    }}

    QTableWidget {{
        gridline-color: {palette['border']};
        alternate-background-color: {palette['surface_soft']};
    }}

    QTableWidget::item:selected, QListWidget::item:selected {{
        background-color: {palette['accent_soft']};
        color: {palette['text']};
    }}

    QListWidget::item:hover {{
        background-color: {palette['surface_hover']};
    }}

    QPushButton {{
        border-radius: 9px;
        padding: 7px 12px;
    }}

    QPushButton#PrimaryButton {{
        background-color: {palette['accent']};
        border: 1px solid {palette['accent']};
        color: white;
        font-weight: 700;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: #1663b4;
        border-color: #1663b4;
    }}

    QPushButton#SecondaryButton {{
        background-color: {palette['surface_soft']};
        border: 1px solid {palette['border']};
    }}

    QPushButton#SecondaryButton:hover {{
        border-color: {palette['accent']};
        background-color: {palette['surface_hover']};
    }}

    QPushButton#DangerButton {{
        background-color: #b64646;
        border: 1px solid #b64646;
        color: #fff6f6;
        font-weight: 700;
    }}

    QPushButton#DangerButton:hover {{
        background-color: #9f3535;
        border-color: #9f3535;
    }}

    #MetaLabel {{
        color: {palette['muted']};
        font-size: 9.2pt;
    }}

    #SectionTitle {{
        font-size: 10.8pt;
        font-weight: 700;
    }}

    #SummaryCardLabel {{
        color: {palette['muted']};
        font-size: 9.5pt;
    }}

    #SummaryCardValue {{
        font-size: 16pt;
        font-weight: 700;
    }}

    #StatusPill, #PriorityPill {{
        border-radius: 8px;
        padding: 3px 8px;
        border: 1px solid {palette['border']};
        font-size: 9pt;
    }}

    #StatusPill[status="open"] {{ background: #d9f0ff; color: #14598c; border-color: #a8d5f6; }}
    #StatusPill[status="in_progress"] {{ background: #fff2d8; color: #8f5d00; border-color: #f0cf92; }}
    #StatusPill[status="pending"] {{ background: #f9e7ff; color: #7f379f; border-color: #ddb5ef; }}
    #StatusPill[status="resolved"] {{ background: #daf5e6; color: #1d754b; border-color: #a6dfc3; }}
    #StatusPill[status="closed"] {{ background: #e6ecf3; color: #40556e; border-color: #c8d5e5; }}
    #StatusPill[status="waiting_on_client"] {{ background: #ffe8e1; color: #9c4a32; border-color: #f5c4b5; }}

    #PriorityPill[priority="low"] {{ background: #e8f6ea; color: #2e6a3f; border-color: #b8e0c2; }}
    #PriorityPill[priority="medium"] {{ background: #e3f0ff; color: #215ea3; border-color: #b8d3f3; }}
    #PriorityPill[priority="high"] {{ background: #fff3df; color: #986100; border-color: #f0d09a; }}
    #PriorityPill[priority="urgent"] {{ background: #ffe4e4; color: #9a2d2d; border-color: #f2b1b1; }}

    QTabWidget::pane {{
        border: 1px solid {palette['border']};
        border-radius: 10px;
        top: -1px;
        background-color: {palette['surface']};
    }}

    QTabBar::tab {{
        background-color: {palette['surface_soft']};
        border: 1px solid {palette['border']};
        border-bottom: 0;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        margin-right: 4px;
        padding: 7px 12px;
        min-width: 110px;
        max-width: 220px;
        text-align: center;
    }}

    QTabBar::tab:selected {{
        background-color: {palette['surface']};
        border-color: {palette['accent']};
        font-weight: 700;
    }}

    #AttachmentList {{
        padding: 8px;
    }}
    """
