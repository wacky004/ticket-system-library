"""SQLite database initialization and schema management."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import DB_PATH, DATA_DIR


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    client_name TEXT,
    va_name TEXT,
    category TEXT,
    subcategory TEXT,
    priority TEXT NOT NULL DEFAULT 'Medium',
    status TEXT NOT NULL DEFAULT 'Open',
    assigned_to TEXT,
    source TEXT,
    description TEXT,
    troubleshooting TEXT,
    resolution TEXT,
    next_action TEXT,
    tags_text TEXT,
    follow_up_date TEXT,
    device_name TEXT,
    software_tools TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1))
);

CREATE TABLE IF NOT EXISTS ticket_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    note_text TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ticket_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER,
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ticket_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subcategories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (category_id, name),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ticket_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (ticket_id, tag_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type TEXT NOT NULL DEFAULT 'string',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS backup_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    backup_size INTEGER,
    backup_type TEXT NOT NULL DEFAULT 'manual',
    status TEXT NOT NULL DEFAULT 'started',
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    notes TEXT
);
"""

DEFAULT_CATEGORIES = [
    ("Technical", "Technical troubleshooting and support tickets."),
    ("Account", "Account access, profile, and permissions-related tickets."),
    ("Billing", "Invoices, charges, and payment-related tickets."),
    ("Operations", "Internal operations and workflow improvement tickets."),
    ("General Inquiry", "General questions and uncategorized requests."),
]

DEFAULT_SUBCATEGORIES = {
    "Technical": ["Desktop App", "Mobile App", "Network", "Hardware"],
    "Account": ["Password Reset", "User Provisioning", "Permissions"],
    "Billing": ["Invoice Issue", "Refund Request", "Payment Failure"],
    "Operations": ["Process Update", "Escalation", "Internal Tooling"],
    "General Inquiry": ["Information Request", "Other"],
}

DEFAULT_SETTINGS = [
    ("default_statuses", "Open,In Progress,Waiting on Client,Resolved,Closed", "csv"),
    ("default_priorities", "Low,Medium,High,Urgent", "csv"),
    ("theme_mode", "dark", "string"),
]


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Provide a SQLite connection with FK support enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    """Create database file, schema, and defaults."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        _seed_defaults(conn)
        conn.commit()


def _seed_defaults(conn: sqlite3.Connection) -> None:
    """Insert default statuses, priorities, and categories only when missing."""
    conn.executemany(
        """
        INSERT INTO app_settings (setting_key, setting_value, setting_type)
        VALUES (?, ?, ?)
        ON CONFLICT(setting_key) DO NOTHING;
        """,
        DEFAULT_SETTINGS,
    )

    conn.executemany(
        """
        INSERT INTO categories (name, description)
        VALUES (?, ?)
        ON CONFLICT(name) DO NOTHING;
        """,
        DEFAULT_CATEGORIES,
    )

    category_rows = conn.execute("SELECT id, name FROM categories;").fetchall()
    category_map = {row["name"]: row["id"] for row in category_rows}

    subcategory_rows: list[tuple[int, str, str]] = []
    for category_name, names in DEFAULT_SUBCATEGORIES.items():
        category_id = category_map.get(category_name)
        if category_id is None:
            continue
        for subcategory_name in names:
            subcategory_rows.append((category_id, subcategory_name, f"{subcategory_name} tasks"))

    conn.executemany(
        """
        INSERT INTO subcategories (category_id, name, description)
        VALUES (?, ?, ?)
        ON CONFLICT(category_id, name) DO NOTHING;
        """,
        subcategory_rows,
    )
