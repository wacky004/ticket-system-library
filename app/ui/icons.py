"""SVG icon helpers for navigation and workspace UI."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICON_SIZE = 18
ICON_NORMAL = "#9db0c8"
ICON_ACTIVE = "#ffffff"

_ICON_PATHS = {
    "dashboard": '<rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="5" rx="1.5"/><rect x="13.5" y="10.5" width="7" height="10" rx="1.5"/><rect x="3.5" y="12.5" width="7" height="8" rx="1.5"/>',
    "tickets": '<rect x="3.5" y="5.5" width="17" height="13" rx="2"/><path d="M8 5.5V3.5M16 5.5V3.5"/><path d="M3.5 10.5H20.5"/>',
    "guides": '<path d="M4.5 5.5A2 2 0 0 1 6.5 3.5H20.5V19.5H6.5A2 2 0 0 0 4.5 21.5Z"/><path d="M4.5 5.5A2 2 0 0 0 2.5 3.5H0.5V19.5H4.5"/><path d="M8 8.5H17M8 12H17M8 15.5H14"/>',
    "reports": '<path d="M3.5 20.5H20.5"/><rect x="5" y="11" width="3.5" height="7.5" rx="1"/><rect x="10.25" y="7.5" width="3.5" height="11" rx="1"/><rect x="15.5" y="4.5" width="3.5" height="14" rx="1"/>',
    "backups": '<path d="M19.5 8.5V4.5H15.5"/><path d="M19.2 13A8 8 0 1 1 16.8 6.8"/><path d="M12 8V12L14.8 13.8"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2.8V5M12 19V21.2M2.8 12H5M19 12H21.2M5.5 5.5L7 7M17 17L18.5 18.5M18.5 5.5L17 7M7 17L5.5 18.5"/>',
}


def _icon_svg(path_data: str, color: str) -> QByteArray:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f'<g fill="none" stroke="{color}" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f"{path_data}</g></svg>"
    )
    return QByteArray(svg.encode("utf-8"))


def _render_icon(path_data: str, color: str, size: int = ICON_SIZE) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer = QSvgRenderer(_icon_svg(path_data, color))
    renderer.render(painter)
    painter.end()
    return pixmap


def build_nav_icon(icon_key: str, size: int = ICON_SIZE) -> QIcon:
    path_data = _ICON_PATHS.get(icon_key, _ICON_PATHS["tickets"])
    icon = QIcon()
    icon.addPixmap(_render_icon(path_data, ICON_NORMAL, size), QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(_render_icon(path_data, ICON_ACTIVE, size), QIcon.Mode.Normal, QIcon.State.On)
    icon.addPixmap(_render_icon(path_data, ICON_ACTIVE, size), QIcon.Mode.Selected, QIcon.State.On)
    return icon
