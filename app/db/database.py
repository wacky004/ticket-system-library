"""SQLite database initialization and ticket CRUD operations."""

from __future__ import annotations

import mimetypes
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from app.config import ATTACHMENTS_DIR, DB_PATH, DATA_DIR, EXPORTS_DIR


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
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    starred INTEGER NOT NULL DEFAULT 0 CHECK (starred IN (0, 1)),
    pinned INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1))
);

CREATE TABLE IF NOT EXISTS ticket_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    note_type TEXT NOT NULL DEFAULT 'Internal',
    content TEXT,
    note_text TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ticket_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    filename TEXT,
    file_path TEXT NOT NULL,
    note_label TEXT,
    mime_type TEXT,
    file_size INTEGER,
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
    added_at TEXT,
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

CREATE TRIGGER IF NOT EXISTS trg_tickets_updated_at
AFTER UPDATE ON tickets
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE tickets
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

CREATE INDEX IF NOT EXISTS idx_tickets_ticket_id ON tickets(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_client_name ON tickets(client_name);
CREATE INDEX IF NOT EXISTS idx_tickets_va_name ON tickets(va_name);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tickets_archived ON tickets(archived);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_follow_up_date ON tickets(follow_up_date);
CREATE INDEX IF NOT EXISTS idx_ticket_attachments_ticket_id ON ticket_attachments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_notes_ticket_id ON ticket_notes(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket_id ON ticket_history(ticket_id);
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
    ("export_directory", str(EXPORTS_DIR), "path"),
    ("onedrive_backup_path", "", "path"),
    ("auto_backup_on_exit", "0", "bool"),
    ("ticket_id_prefix", "TKT", "string"),
    ("display_name", "Support User", "string"),
    ("company_name", "Ticket Library", "string"),
]

ALLOWED_ATTACHMENT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

SAMPLE_TICKETS = [
    {
        "title": "VPN client fails to connect",
        "client_name": "Acme Logistics",
        "va_name": "Jordan Lee",
        "category": "Technical",
        "subcategory": "Network",
        "priority": "High",
        "status": "In Progress",
        "assigned_to": "Tech A",
        "source": "Email",
        "description": "User reports VPN timeout from remote office.",
        "troubleshooting": "Verified internet link and reset adapter.",
        "resolution": "",
        "next_action": "Review firewall allow-list with network team.",
        "tags_text": "vpn,network,remote",
        "follow_up_date": "",
        "device_name": "ACME-LT-119",
        "software_tools": "OpenVPN, Windows 11",
    },
    {
        "title": "Reset Microsoft 365 password",
        "client_name": "Bright Dental",
        "va_name": "Sam Cruz",
        "category": "Account",
        "subcategory": "Password Reset",
        "priority": "Medium",
        "status": "Resolved",
        "assigned_to": "Tech B",
        "source": "Phone",
        "description": "User locked out after multiple failed attempts.",
        "troubleshooting": "Validated identity and checked MFA contact methods.",
        "resolution": "Password reset completed and login verified.",
        "next_action": "",
        "tags_text": "m365,password",
        "follow_up_date": "",
        "device_name": "BRD-PC-22",
        "software_tools": "Microsoft 365 Admin",
    },
    {
        "title": "Invoice mismatch for March",
        "client_name": "Northline Retail",
        "va_name": "Ari Gomez",
        "category": "Billing",
        "subcategory": "Invoice Issue",
        "priority": "Low",
        "status": "Open",
        "assigned_to": "Billing Ops",
        "source": "Portal",
        "description": "Client flagged mismatch between quote and posted invoice.",
        "troubleshooting": "Checked contract revision and payment records.",
        "resolution": "",
        "next_action": "Confirm discount amendment with finance lead.",
        "tags_text": "billing,invoice",
        "follow_up_date": "",
        "device_name": "",
        "software_tools": "QuickBooks",
    },
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
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        _migrate_schema(conn)
        _seed_defaults(conn)
        _seed_sample_tickets(conn)
        conn.commit()


def get_default_priorities() -> list[str]:
    return _get_csv_setting("default_priorities", ["Low", "Medium", "High", "Urgent"])


def get_default_statuses() -> list[str]:
    return _get_csv_setting(
        "default_statuses",
        ["Open", "In Progress", "Waiting on Client", "Resolved", "Closed"],
    )


def list_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM categories WHERE is_active = 1 ORDER BY name;"
        ).fetchall()
    return [str(row["name"]) for row in rows]


def list_subcategories(category_name: str | None = None) -> list[str]:
    query = """
        SELECT s.name
        FROM subcategories s
        JOIN categories c ON c.id = s.category_id
        WHERE s.is_active = 1
    """
    params: tuple[Any, ...] = ()

    if category_name:
        query += " AND c.name = ?"
        params = (category_name,)

    query += " ORDER BY s.name;"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [str(row["name"]) for row in rows]


def generate_next_ticket_id() -> str:
    with get_connection() as conn:
        return _generate_next_ticket_id(conn)


def list_tickets(include_archived: bool = True) -> list[dict[str, Any]]:
    return search_tickets({"include_archived": include_archived})


def has_any_tickets() -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM tickets;").fetchone()
    return bool(row and int(row["count"]) > 0)


def search_tickets(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    active_filters = filters or {}

    query = """
        SELECT
            t.id,
            t.ticket_id,
            t.title,
            t.client_name,
            t.va_name,
            t.category,
            t.subcategory,
            t.priority,
            t.status,
            t.assigned_to,
            t.tags_text,
            t.description,
            t.follow_up_date,
            t.archived,
            t.starred,
            t.pinned,
            t.created_at,
            t.updated_at,
            t.resolved_at,
            EXISTS(SELECT 1 FROM ticket_attachments ta WHERE ta.ticket_id = t.id) AS has_attachments
        FROM tickets t
        WHERE 1 = 1
    """
    params: list[Any] = []

    search_text = _normalize(active_filters.get("search_text"))
    if search_text:
        like_value = f"%{search_text}%"
        query += """
            AND (
                t.ticket_id LIKE ? COLLATE NOCASE OR
                t.title LIKE ? COLLATE NOCASE OR
                t.client_name LIKE ? COLLATE NOCASE OR
                t.va_name LIKE ? COLLATE NOCASE OR
                t.category LIKE ? COLLATE NOCASE OR
                t.priority LIKE ? COLLATE NOCASE OR
                t.status LIKE ? COLLATE NOCASE OR
                t.assigned_to LIKE ? COLLATE NOCASE OR
                t.tags_text LIKE ? COLLATE NOCASE OR
                t.description LIKE ? COLLATE NOCASE
            )
        """
        params.extend(
            [
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
            ]
        )

    status = _normalize(active_filters.get("status"))
    if status:
        query += " AND t.status = ?"
        params.append(status)

    priority = _normalize(active_filters.get("priority"))
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)

    category = _normalize(active_filters.get("category"))
    if category:
        query += " AND t.category = ?"
        params.append(category)

    client_name = _normalize(active_filters.get("client_name"))
    if client_name:
        query += " AND t.client_name = ?"
        params.append(client_name)

    va_name = _normalize(active_filters.get("va_name"))
    if va_name:
        query += " AND t.va_name = ?"
        params.append(va_name)

    date_from = _normalize(active_filters.get("date_from"))
    if date_from:
        query += " AND date(t.created_at) >= date(?)"
        params.append(date_from)

    date_to = _normalize(active_filters.get("date_to"))
    if date_to:
        query += " AND date(t.created_at) <= date(?)"
        params.append(date_to)

    archived_only = bool(active_filters.get("archived_only", False))
    include_archived = bool(active_filters.get("include_archived", True))
    if archived_only:
        query += " AND t.archived = 1"
    elif not include_archived:
        query += " AND t.archived = 0"

    if bool(active_filters.get("with_attachments_only", False)):
        query += " AND EXISTS(SELECT 1 FROM ticket_attachments ta2 WHERE ta2.ticket_id = t.id)"

    query += " ORDER BY t.pinned DESC, t.created_at DESC, t.id DESC;"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_ticket_filter_options() -> dict[str, list[str]]:
    with get_connection() as conn:
        client_rows = conn.execute(
            """
            SELECT DISTINCT client_name
            FROM tickets
            WHERE client_name IS NOT NULL AND trim(client_name) <> ''
            ORDER BY client_name;
            """
        ).fetchall()
        va_rows = conn.execute(
            """
            SELECT DISTINCT va_name
            FROM tickets
            WHERE va_name IS NOT NULL AND trim(va_name) <> ''
            ORDER BY va_name;
            """
        ).fetchall()

    return {
        "statuses": get_default_statuses(),
        "priorities": get_default_priorities(),
        "categories": list_categories(),
        "clients": [str(row["client_name"]) for row in client_rows],
        "vas": [str(row["va_name"]) for row in va_rows],
    }


def get_export_directory() -> str:
    value = get_app_setting("export_directory")
    directory = Path(value) if value else EXPORTS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


def set_export_directory(path_value: str) -> str:
    normalized = str(Path(path_value).expanduser().resolve())
    Path(normalized).mkdir(parents=True, exist_ok=True)
    set_app_setting("export_directory", normalized, "path")
    return normalized


def get_app_setting(setting_key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = ?;",
            (setting_key,),
        ).fetchone()
    if row is None:
        return None
    return _normalize(row["setting_value"])


def set_app_setting(setting_key: str, setting_value: str, setting_type: str = "string") -> None:
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, setting_type, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(setting_key)
            DO UPDATE SET
                setting_value = excluded.setting_value,
                setting_type = excluded.setting_type,
                updated_at = excluded.updated_at;
            """,
            (setting_key, setting_value, setting_type, updated_at),
        )
        conn.commit()


def get_dashboard_summary() -> dict[str, int]:
    with get_connection() as conn:
        total = int(conn.execute("SELECT COUNT(*) AS count FROM tickets;").fetchone()["count"])
        open_count = int(
            conn.execute("SELECT COUNT(*) AS count FROM tickets WHERE status = 'Open' AND archived = 0;").fetchone()[
                "count"
            ]
        )
        in_progress_count = int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM tickets WHERE status = 'In Progress' AND archived = 0;"
            ).fetchone()["count"]
        )
        pending_count = int(
            conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM tickets
                WHERE archived = 0 AND (status = 'Pending' OR status = 'Waiting on Client');
                """
            ).fetchone()["count"]
        )
        resolved_count = int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM tickets WHERE archived = 0 AND (status = 'Resolved' OR status = 'Closed');"
            ).fetchone()["count"]
        )
        archived_count = int(
            conn.execute("SELECT COUNT(*) AS count FROM tickets WHERE archived = 1;").fetchone()["count"]
        )

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress_count,
        "pending": pending_count,
        "resolved": resolved_count,
        "archived": archived_count,
    }


def list_recent_tickets(limit: int = 8) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ticket_id, title, client_name, status, priority, updated_at
            FROM tickets
            ORDER BY datetime(updated_at) DESC, id DESC
            LIMIT ?;
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_ticket_count_by_priority() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT COALESCE(priority, 'Unspecified') AS label, COUNT(*) AS count
            FROM tickets
            GROUP BY COALESCE(priority, 'Unspecified')
            ORDER BY count DESC, label ASC;
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_ticket_count_by_category() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT COALESCE(category, 'Uncategorized') AS label, COUNT(*) AS count
            FROM tickets
            GROUP BY COALESCE(category, 'Uncategorized')
            ORDER BY count DESC, label ASC;
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_upcoming_follow_ups(limit: int = 8) -> list[dict[str, Any]]:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ticket_id, title, client_name, status, follow_up_date
            FROM tickets
            WHERE archived = 0
              AND follow_up_date IS NOT NULL
              AND trim(follow_up_date) <> ''
              AND date(follow_up_date) >= date(?)
            ORDER BY date(follow_up_date) ASC, id ASC
            LIMIT ?;
            """,
            (today, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_last_backup_status() -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT backup_name, status, started_at, completed_at
            FROM backup_logs
            ORDER BY datetime(started_at) DESC, id DESC
            LIMIT 1;
            """
        ).fetchone()

    if row is None:
        return {
            "label": "No backups yet",
            "status": "Placeholder",
            "timestamp": "-",
        }

    completed = row["completed_at"] if row["completed_at"] else row["started_at"]
    return {
        "label": row["backup_name"] or "Backup job",
        "status": row["status"] or "unknown",
        "timestamp": completed or "-",
    }


def start_backup_log(backup_name: str, backup_path: str, backup_type: str = "manual") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO backup_logs (backup_name, backup_path, backup_type, status, started_at)
            VALUES (?, ?, ?, 'started', datetime('now'));
            """,
            (backup_name, backup_path, backup_type),
        )
        conn.commit()
    return int(cursor.lastrowid)


def complete_backup_log(
    log_id: int,
    status: str,
    backup_size: int | None = None,
    notes: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE backup_logs
            SET status = ?,
                backup_size = ?,
                notes = ?,
                completed_at = datetime('now')
            WHERE id = ?;
            """,
            (status, backup_size, notes, log_id),
        )
        conn.commit()


def get_last_backup_log() -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, backup_name, backup_path, backup_size, backup_type, status, started_at, completed_at, notes
            FROM backup_logs
            ORDER BY id DESC
            LIMIT 1;
            """
        ).fetchone()
    return dict(row) if row else None


def list_backup_logs(limit: int = 30) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, backup_name, backup_path, backup_size, backup_type, status, started_at, completed_at, notes
            FROM backup_logs
            ORDER BY id DESC
            LIMIT ?;
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_app_settings() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT setting_key, setting_value, setting_type, updated_at
            FROM app_settings
            ORDER BY setting_key ASC;
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_report_ticket_count_by_date(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    where_sql, params = _build_date_range_filter(date_from, date_to)
    query = f"""
        SELECT date(created_at) AS label, COUNT(*) AS count
        FROM tickets
        {where_sql}
        GROUP BY date(created_at)
        ORDER BY date(created_at) ASC;
    """
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_report_ticket_count_by_client(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    where_sql, params = _build_date_range_filter(date_from, date_to)
    query = f"""
        SELECT COALESCE(NULLIF(trim(client_name), ''), 'Unknown Client') AS label, COUNT(*) AS count
        FROM tickets
        {where_sql}
        GROUP BY COALESCE(NULLIF(trim(client_name), ''), 'Unknown Client')
        ORDER BY count DESC, label ASC;
    """
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_report_ticket_count_by_category(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    where_sql, params = _build_date_range_filter(date_from, date_to)
    query = f"""
        SELECT COALESCE(NULLIF(trim(category), ''), 'Uncategorized') AS label, COUNT(*) AS count
        FROM tickets
        {where_sql}
        GROUP BY COALESCE(NULLIF(trim(category), ''), 'Uncategorized')
        ORDER BY count DESC, label ASC;
    """
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_report_ticket_count_by_technician(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    where_sql, params = _build_date_range_filter(date_from, date_to)
    query = f"""
        SELECT COALESCE(NULLIF(trim(assigned_to), ''), 'Unassigned') AS label, COUNT(*) AS count
        FROM tickets
        {where_sql}
        GROUP BY COALESCE(NULLIF(trim(assigned_to), ''), 'Unassigned')
        ORDER BY count DESC, label ASC;
    """
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_report_resolved_vs_unresolved(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    where_sql, params = _build_date_range_filter(date_from, date_to)
    query = f"""
        SELECT
            CASE
                WHEN status IN ('Resolved', 'Closed') THEN 'Resolved'
                ELSE 'Unresolved'
            END AS label,
            COUNT(*) AS count
        FROM tickets
        {where_sql}
        GROUP BY
            CASE
                WHEN status IN ('Resolved', 'Closed') THEN 'Resolved'
                ELSE 'Unresolved'
            END
        ORDER BY label ASC;
    """
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_report_priority_distribution(
    date_from: str | None = None, date_to: str | None = None
) -> list[dict[str, Any]]:
    where_sql, params = _build_date_range_filter(date_from, date_to)
    query = f"""
        SELECT COALESCE(NULLIF(trim(priority), ''), 'Unspecified') AS label, COUNT(*) AS count
        FROM tickets
        {where_sql}
        GROUP BY COALESCE(NULLIF(trim(priority), ''), 'Unspecified')
        ORDER BY count DESC, label ASC;
    """
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_ticket_by_db_id(db_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?;", (db_id,)).fetchone()
    return dict(row) if row else None


def list_ticket_notes(ticket_db_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                ticket_id,
                COALESCE(note_type, 'Internal') AS note_type,
                COALESCE(content, note_text) AS content,
                created_at
            FROM ticket_notes
            WHERE ticket_id = ?
            ORDER BY id DESC;
            """,
            (ticket_db_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_ticket_note(ticket_db_id: int, note_type: str, content: str) -> int:
    normalized_type = _normalize(note_type) or "Internal"
    normalized_content = _normalize(content)
    if not normalized_content:
        raise ValueError("Note content is required.")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        ticket_exists = conn.execute("SELECT 1 FROM tickets WHERE id = ?;", (ticket_db_id,)).fetchone()
        if ticket_exists is None:
            raise ValueError("Ticket not found.")

        cursor = conn.execute(
            """
            INSERT INTO ticket_notes (
                ticket_id, note_type, content, note_text, created_at
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (ticket_db_id, normalized_type, normalized_content, normalized_content, created_at),
        )
        conn.commit()
    return int(cursor.lastrowid)


def list_ticket_history(ticket_db_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, ticket_id, field_name, old_value, new_value, changed_at
            FROM ticket_history
            WHERE ticket_id = ?
            ORDER BY id DESC;
            """,
            (ticket_db_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_ticket_attachments(ticket_db_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                ticket_id,
                COALESCE(filename, file_name) AS filename,
                file_path,
                COALESCE(added_at, uploaded_at) AS added_at,
                note_label
            FROM ticket_attachments
            WHERE ticket_id = ?
            ORDER BY id DESC;
            """,
            (ticket_db_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_ticket_attachment(ticket_db_id: int, source_path: str | Path, note_label: str | None = None) -> int:
    source = Path(source_path)
    if not source.exists() or not source.is_file():
        raise ValueError("Attachment file was not found.")

    extension = source.suffix.lower()
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise ValueError("Unsupported image format. Use PNG, JPG, JPEG, or WEBP.")

    safe_stem = _sanitize_file_name(source.stem)
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}_{safe_stem}{extension}"

    ticket_dir = ATTACHMENTS_DIR / str(ticket_db_id)
    ticket_dir.mkdir(parents=True, exist_ok=True)
    destination = ticket_dir / unique_name

    shutil.copy2(source, destination)

    mime_type, _ = mimetypes.guess_type(destination.name)
    file_size = destination.stat().st_size
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    normalized_note = _normalize(note_label)

    with get_connection() as conn:
        ticket_exists = conn.execute("SELECT 1 FROM tickets WHERE id = ?;", (ticket_db_id,)).fetchone()
        if ticket_exists is None:
            destination.unlink(missing_ok=True)
            raise ValueError("Ticket not found.")

        cursor = conn.execute(
            """
            INSERT INTO ticket_attachments (
                ticket_id, file_name, filename, file_path, note_label,
                mime_type, file_size, uploaded_at, added_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ticket_db_id,
                source.name,
                source.name,
                str(destination),
                normalized_note,
                mime_type,
                file_size,
                now_text,
                now_text,
            ),
        )
        conn.commit()
    return int(cursor.lastrowid)


def remove_ticket_attachment(attachment_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT file_path FROM ticket_attachments WHERE id = ?;",
            (attachment_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Attachment not found.")

        conn.execute("DELETE FROM ticket_attachments WHERE id = ?;", (attachment_id,))
        conn.commit()

    file_path = Path(str(row["file_path"]))
    file_path.unlink(missing_ok=True)


def create_ticket(values: dict[str, Any]) -> int:
    payload = _validate_ticket_payload(values)

    with get_connection() as conn:
        ticket_id = _generate_next_ticket_id(conn)
        resolved_at = _derive_resolved_at(payload.get("status"))

        cursor = conn.execute(
            """
            INSERT INTO tickets (
                ticket_id, title, client_name, va_name, category, subcategory,
                priority, status, assigned_to, source, description, troubleshooting,
                resolution, next_action, tags_text, follow_up_date, device_name,
                software_tools, resolved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ticket_id,
                payload["title"],
                payload["client_name"],
                payload["va_name"],
                payload["category"],
                payload["subcategory"],
                payload["priority"],
                payload["status"],
                payload["assigned_to"],
                payload["source"],
                payload["description"],
                payload["troubleshooting"],
                payload["resolution"],
                payload["next_action"],
                payload["tags_text"],
                payload["follow_up_date"],
                payload["device_name"],
                payload["software_tools"],
                resolved_at,
            ),
        )

        ticket_db_id = int(cursor.lastrowid)
        conn.commit()
    return ticket_db_id


def update_ticket(db_id: int, values: dict[str, Any]) -> None:
    payload = _validate_ticket_payload(values)

    with get_connection() as conn:
        current = conn.execute("SELECT * FROM tickets WHERE id = ?;", (db_id,)).fetchone()
        if current is None:
            raise ValueError("Ticket not found.")

        resolved_at = _derive_resolved_at(payload.get("status"), current["resolved_at"])
        updated_fields: dict[str, Any] = {
            "title": payload["title"],
            "client_name": payload["client_name"],
            "va_name": payload["va_name"],
            "category": payload["category"],
            "subcategory": payload["subcategory"],
            "priority": payload["priority"],
            "status": payload["status"],
            "assigned_to": payload["assigned_to"],
            "source": payload["source"],
            "description": payload["description"],
            "troubleshooting": payload["troubleshooting"],
            "resolution": payload["resolution"],
            "next_action": payload["next_action"],
            "tags_text": payload["tags_text"],
            "follow_up_date": payload["follow_up_date"],
            "device_name": payload["device_name"],
            "software_tools": payload["software_tools"],
            "resolved_at": resolved_at,
        }

        conn.execute(
            """
            UPDATE tickets
            SET title = ?,
                client_name = ?,
                va_name = ?,
                category = ?,
                subcategory = ?,
                priority = ?,
                status = ?,
                assigned_to = ?,
                source = ?,
                description = ?,
                troubleshooting = ?,
                resolution = ?,
                next_action = ?,
                tags_text = ?,
                follow_up_date = ?,
                device_name = ?,
                software_tools = ?,
                resolved_at = ?,
                updated_at = datetime('now')
            WHERE id = ?;
            """,
            (
                updated_fields["title"],
                updated_fields["client_name"],
                updated_fields["va_name"],
                updated_fields["category"],
                updated_fields["subcategory"],
                updated_fields["priority"],
                updated_fields["status"],
                updated_fields["assigned_to"],
                updated_fields["source"],
                updated_fields["description"],
                updated_fields["troubleshooting"],
                updated_fields["resolution"],
                updated_fields["next_action"],
                updated_fields["tags_text"],
                updated_fields["follow_up_date"],
                updated_fields["device_name"],
                updated_fields["software_tools"],
                updated_fields["resolved_at"],
                db_id,
            ),
        )

        history_rows = _build_ticket_history_rows(db_id, dict(current), updated_fields)
        if history_rows:
            conn.executemany(
                """
                INSERT INTO ticket_history (ticket_id, field_name, old_value, new_value, changed_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                history_rows,
            )

        conn.commit()


def delete_ticket(db_id: int) -> None:
    with get_connection() as conn:
        attachment_rows = conn.execute(
            "SELECT file_path FROM ticket_attachments WHERE ticket_id = ?;",
            (db_id,),
        ).fetchall()
        conn.execute("DELETE FROM tickets WHERE id = ?;", (db_id,))
        conn.commit()

    for row in attachment_rows:
        Path(str(row["file_path"])).unlink(missing_ok=True)


def archive_ticket(db_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT archived FROM tickets WHERE id = ?;", (db_id,)).fetchone()
        if row is None:
            raise ValueError("Ticket not found.")

        conn.execute(
            "UPDATE tickets SET archived = 1, updated_at = datetime('now') WHERE id = ?;",
            (db_id,),
        )
        if int(row["archived"] or 0) != 1:
            changed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                """
                INSERT INTO ticket_history (ticket_id, field_name, old_value, new_value, changed_at)
                VALUES (?, 'archived', ?, '1', ?);
                """,
                (db_id, _stringify(row["archived"]), changed_at),
            )
        conn.commit()


def reopen_ticket(db_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT archived, status, resolved_at FROM tickets WHERE id = ?;",
            (db_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Ticket not found.")

        conn.execute(
            """
            UPDATE tickets
            SET archived = 0,
                status = 'Open',
                resolved_at = NULL,
                updated_at = datetime('now')
            WHERE id = ?;
            """,
            (db_id,),
        )

        history_rows = _build_ticket_history_rows(
            db_id,
            dict(row),
            {"archived": 0, "status": "Open", "resolved_at": None},
        )
        if history_rows:
            conn.executemany(
                """
                INSERT INTO ticket_history (ticket_id, field_name, old_value, new_value, changed_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                history_rows,
            )
        conn.commit()


def set_ticket_starred(db_id: int, starred: bool) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT starred FROM tickets WHERE id = ?;", (db_id,)).fetchone()
        if row is None:
            raise ValueError("Ticket not found.")

        new_value = 1 if starred else 0
        conn.execute("UPDATE tickets SET starred = ?, updated_at = datetime('now') WHERE id = ?;", (new_value, db_id))
        if int(row["starred"] or 0) != new_value:
            conn.execute(
                """
                INSERT INTO ticket_history (ticket_id, field_name, old_value, new_value, changed_at)
                VALUES (?, 'starred', ?, ?, datetime('now'));
                """,
                (db_id, _stringify(row["starred"]), _stringify(new_value)),
            )
        conn.commit()


def set_ticket_pinned(db_id: int, pinned: bool) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT pinned FROM tickets WHERE id = ?;", (db_id,)).fetchone()
        if row is None:
            raise ValueError("Ticket not found.")

        new_value = 1 if pinned else 0
        conn.execute("UPDATE tickets SET pinned = ?, updated_at = datetime('now') WHERE id = ?;", (new_value, db_id))
        if int(row["pinned"] or 0) != new_value:
            conn.execute(
                """
                INSERT INTO ticket_history (ticket_id, field_name, old_value, new_value, changed_at)
                VALUES (?, 'pinned', ?, ?, datetime('now'));
                """,
                (db_id, _stringify(row["pinned"]), _stringify(new_value)),
            )
        conn.commit()


def duplicate_ticket(db_id: int) -> int:
    ticket = get_ticket_by_db_id(db_id)
    if ticket is None:
        raise ValueError("Ticket not found.")

    payload = {
        "title": f"{ticket.get('title') or 'Ticket'} (Copy)",
        "client_name": ticket.get("client_name"),
        "va_name": ticket.get("va_name"),
        "category": ticket.get("category"),
        "subcategory": ticket.get("subcategory"),
        "priority": ticket.get("priority"),
        "status": ticket.get("status") if ticket.get("status") else "Open",
        "assigned_to": ticket.get("assigned_to"),
        "source": ticket.get("source"),
        "description": ticket.get("description"),
        "troubleshooting": ticket.get("troubleshooting"),
        "resolution": ticket.get("resolution"),
        "next_action": ticket.get("next_action"),
        "tags_text": ticket.get("tags_text"),
        "follow_up_date": ticket.get("follow_up_date"),
        "device_name": ticket.get("device_name"),
        "software_tools": ticket.get("software_tools"),
    }
    return create_ticket(payload)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    ticket_columns = _get_table_columns(conn, "tickets")
    if "starred" not in ticket_columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN starred INTEGER NOT NULL DEFAULT 0;")
    if "pinned" not in ticket_columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_starred ON tickets(starred);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_pinned ON tickets(pinned);")

    note_columns = _get_table_columns(conn, "ticket_notes")
    if "note_type" not in note_columns:
        conn.execute("ALTER TABLE ticket_notes ADD COLUMN note_type TEXT;")
    if "content" not in note_columns:
        conn.execute("ALTER TABLE ticket_notes ADD COLUMN content TEXT;")

    conn.execute(
        """
        UPDATE ticket_notes
        SET note_type = 'Internal'
        WHERE note_type IS NULL OR trim(note_type) = '';
        """
    )
    conn.execute(
        """
        UPDATE ticket_notes
        SET content = note_text
        WHERE content IS NULL OR trim(content) = '';
        """
    )

    attachment_columns = _get_table_columns(conn, "ticket_attachments")

    if "filename" not in attachment_columns:
        conn.execute("ALTER TABLE ticket_attachments ADD COLUMN filename TEXT;")

    if "note_label" not in attachment_columns:
        conn.execute("ALTER TABLE ticket_attachments ADD COLUMN note_label TEXT;")

    if "added_at" not in attachment_columns:
        conn.execute("ALTER TABLE ticket_attachments ADD COLUMN added_at TEXT;")

    conn.execute(
        """
        UPDATE ticket_attachments
        SET filename = file_name
        WHERE filename IS NULL OR trim(filename) = '';
        """
    )
    conn.execute(
        """
        UPDATE ticket_attachments
        SET added_at = uploaded_at
        WHERE added_at IS NULL OR trim(added_at) = '';
        """
    )


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
    return {str(row["name"]) for row in rows}


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


def _seed_sample_tickets(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS count FROM tickets;").fetchone()
    if row is None or int(row["count"]) > 0:
        return

    for sample in SAMPLE_TICKETS:
        payload = _validate_ticket_payload(sample)
        resolved_at = _derive_resolved_at(payload["status"])
        conn.execute(
            """
            INSERT INTO tickets (
                ticket_id, title, client_name, va_name, category, subcategory,
                priority, status, assigned_to, source, description, troubleshooting,
                resolution, next_action, tags_text, follow_up_date, device_name,
                software_tools, resolved_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                _generate_next_ticket_id(conn),
                payload["title"],
                payload["client_name"],
                payload["va_name"],
                payload["category"],
                payload["subcategory"],
                payload["priority"],
                payload["status"],
                payload["assigned_to"],
                payload["source"],
                payload["description"],
                payload["troubleshooting"],
                payload["resolution"],
                payload["next_action"],
                payload["tags_text"],
                payload["follow_up_date"],
                payload["device_name"],
                payload["software_tools"],
                resolved_at,
            ),
        )


def _get_csv_setting(setting_key: str, fallback: list[str]) -> list[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = ?;",
            (setting_key,),
        ).fetchone()

    if row is None or not row["setting_value"]:
        return fallback

    parsed = [part.strip() for part in str(row["setting_value"]).split(",") if part.strip()]
    return parsed or fallback


def _get_ticket_id_prefix(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "SELECT setting_value FROM app_settings WHERE setting_key = 'ticket_id_prefix';"
    ).fetchone()
    raw = str(row["setting_value"]).strip().upper() if row and row["setting_value"] else "TKT"
    cleaned = "".join(ch for ch in raw if ch.isalnum())
    return cleaned[:10] or "TKT"


def _generate_next_ticket_id(conn: sqlite3.Connection) -> str:
    year = datetime.now().year
    id_prefix = _get_ticket_id_prefix(conn)
    full_prefix = f"{id_prefix}-{year}-"

    rows = conn.execute(
        "SELECT ticket_id FROM tickets WHERE ticket_id LIKE ?;",
        (f"{full_prefix}%",),
    ).fetchall()

    max_seq = 0
    for row in rows:
        ticket_id = str(row["ticket_id"])
        parts = ticket_id.split("-")
        if len(parts) < 3:
            continue
        try:
            seq = int(parts[-1])
        except ValueError:
            continue
        max_seq = max(max_seq, seq)

    next_seq = max_seq + 1
    return f"{full_prefix}{next_seq:06d}"


def _validate_ticket_payload(values: dict[str, Any]) -> dict[str, str | None]:
    payload = {
        "title": _normalize(values.get("title")),
        "client_name": _normalize(values.get("client_name")),
        "va_name": _normalize(values.get("va_name")),
        "category": _normalize(values.get("category")),
        "subcategory": _normalize(values.get("subcategory")),
        "priority": _normalize(values.get("priority")) or "Medium",
        "status": _normalize(values.get("status")) or "Open",
        "assigned_to": _normalize(values.get("assigned_to")),
        "source": _normalize(values.get("source")),
        "description": _normalize(values.get("description")),
        "troubleshooting": _normalize(values.get("troubleshooting")),
        "resolution": _normalize(values.get("resolution")),
        "next_action": _normalize(values.get("next_action")),
        "tags_text": _normalize(values.get("tags_text")),
        "follow_up_date": _normalize(values.get("follow_up_date")),
        "device_name": _normalize(values.get("device_name")),
        "software_tools": _normalize(values.get("software_tools")),
    }

    if not payload["title"]:
        raise ValueError("Title is required.")

    follow_up = payload["follow_up_date"]
    if follow_up:
        try:
            datetime.strptime(follow_up, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Follow-up date must use YYYY-MM-DD format.") from exc

    return payload


def _normalize(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sanitize_file_name(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in {"-", "_"})
    return cleaned[:80] or "image"


def _build_date_range_filter(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if _normalize(date_from):
        clauses.append("date(created_at) >= date(?)")
        params.append(date_from)
    if _normalize(date_to):
        clauses.append("date(created_at) <= date(?)")
        params.append(date_to)

    if not clauses:
        return "", []
    return "WHERE " + " AND ".join(clauses), params


def _build_ticket_history_rows(
    ticket_id: int,
    old_ticket: dict[str, Any],
    new_fields: dict[str, Any],
) -> list[tuple[int, str, str | None, str | None, str]]:
    changed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[tuple[int, str, str | None, str | None, str]] = []

    for field_name, new_value in new_fields.items():
        old_value = old_ticket.get(field_name)
        if not _values_differ(old_value, new_value):
            continue
        rows.append((ticket_id, field_name, _stringify(old_value), _stringify(new_value), changed_at))

    return rows


def _values_differ(old_value: Any, new_value: Any) -> bool:
    old_text = _stringify(old_value)
    new_text = _stringify(new_value)
    return old_text != new_text


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _derive_resolved_at(status: str | None, current_resolved_at: Any = None) -> str | None:
    if status in {"Resolved", "Closed"}:
        return str(current_resolved_at) if current_resolved_at else datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    return None
