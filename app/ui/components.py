"""Reusable UI components for workspace-style pages."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


def _text_to_readable_html(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    html_parts: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_parts.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.strip()
        if not line:
            close_list()
            html_parts.append("<p></p>")
            continue
        if line.startswith(("- ", "* ")):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{escape(line[2:])}</li>")
            continue
        close_list()
        html_parts.append(f"<p>{escape(line)}</p>")

    close_list()
    if not html_parts:
        return "<p><i>No content.</i></p>"
    return "".join(html_parts)


class SectionBlock(QFrame):
    """Card-like section wrapper with header area."""

    def __init__(self, title: str, subtitle: str | None = None) -> None:
        super().__init__()
        self.setObjectName("SectionBlock")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        root.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("MetaLabel")
            subtitle_label.setWordWrap(True)
            root.addWidget(subtitle_label)


class StatusPill(QLabel):
    """Colored status chip."""

    def __init__(self, text: str) -> None:
        super().__init__(text or "Unknown")
        self.setObjectName("StatusPill")
        self.setProperty("status", (text or "unknown").lower().replace(" ", "_"))


class PriorityPill(QLabel):
    """Colored priority chip."""

    def __init__(self, text: str) -> None:
        super().__init__(text or "Unspecified")
        self.setObjectName("PriorityPill")
        self.setProperty("priority", (text or "unspecified").lower())


class ReadableContentCard(QFrame):
    """Readable long-form content card with copy action."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("ReadableContentCard")
        self._raw_text = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        self.copy_button = QPushButton("Copy")
        self.copy_button.setObjectName("SecondaryButton")
        self.copy_button.clicked.connect(self._copy_to_clipboard)

        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.copy_button)

        self.viewer = QTextBrowser()
        self.viewer.setObjectName("ReadableViewer")
        self.viewer.setOpenExternalLinks(True)

        root.addLayout(header)
        root.addWidget(self.viewer, 1)

    def set_text(self, text: str | None) -> None:
        self._raw_text = (text or "").strip()
        self.viewer.setHtml(_text_to_readable_html(self._raw_text))

    def _copy_to_clipboard(self) -> None:
        QGuiApplication.clipboard().setText(self._raw_text)


class EmptyStateWidget(QWidget):
    """Simple centered empty state."""

    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(6)
        root.addStretch(1)

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)

        root.addWidget(title_label)
        root.addWidget(subtitle_label)
        root.addStretch(1)


def configure_tab_widget(widget) -> None:
    """Make tab bars readable and scrollable when labels overflow."""
    bar = widget.tabBar()
    bar.setExpanding(False)
    bar.setUsesScrollButtons(True)
    bar.setElideMode(Qt.TextElideMode.ElideRight)
    bar.setMovable(False)
