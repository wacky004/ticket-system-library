"""Application configuration values."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "Ticket Library Desktop"
APP_VERSION = "0.1.0"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ticket_library.db"
MEDIA_DIR = BASE_DIR / "media"
ATTACHMENTS_DIR = MEDIA_DIR / "attachments"
