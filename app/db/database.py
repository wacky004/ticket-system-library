"""SQLite database initialization and ticket CRUD operations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

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
CREATE INDEX IF NOT EXISTS idx_ticket_attachments_ticket_id ON ticket_attachments(ticket_id);
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

    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
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

    query += " ORDER BY t.created_at DESC, t.id DESC;"

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


def get_ticket_by_db_id(db_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?;", (db_id,)).fetchone()
    return dict(row) if row else None


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
        current = conn.execute(
            "SELECT status, resolved_at FROM tickets WHERE id = ?;", (db_id,)
        ).fetchone()
        if current is None:
            raise ValueError("Ticket not found.")

        resolved_at = _derive_resolved_at(payload.get("status"), current["resolved_at"])

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
                db_id,
            ),
        )

        conn.commit()


def delete_ticket(db_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM tickets WHERE id = ?;", (db_id,))
        conn.commit()


def archive_ticket(db_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tickets SET archived = 1, updated_at = datetime('now') WHERE id = ?;",
            (db_id,),
        )
        conn.commit()


def reopen_ticket(db_id: int) -> None:
    with get_connection() as conn:
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


def _generate_next_ticket_id(conn: sqlite3.Connection) -> str:
    year = datetime.now().year
    prefix = f"TKT-{year}-"

    row = conn.execute(
        """
        SELECT MAX(CAST(SUBSTR(ticket_id, 10) AS INTEGER)) AS max_seq
        FROM tickets
        WHERE ticket_id LIKE ?;
        """,
        (f"{prefix}%",),
    ).fetchone()

    max_seq = int(row["max_seq"] or 0) if row else 0
    next_seq = max_seq + 1
    return f"{prefix}{next_seq:06d}"


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


def _derive_resolved_at(status: str | None, current_resolved_at: Any = None) -> str | None:
    if status in {"Resolved", "Closed"}:
        return str(current_resolved_at) if current_resolved_at else datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    return None
