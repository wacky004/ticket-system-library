from __future__ import annotations

from pathlib import Path

import app.db.database as db
import app.services.backup as backup


def test_database_initialization_creates_db(isolated_env: dict[str, Path]) -> None:
    assert isolated_env["db_path"].exists()


def test_ticket_insert(isolated_env: dict[str, Path]) -> None:
    ticket_db_id = db.create_ticket({"title": "Test Insert Ticket"})
    inserted = db.get_ticket_by_db_id(ticket_db_id)
    assert inserted is not None
    assert inserted["title"] == "Test Insert Ticket"
    assert str(inserted["ticket_id"]).startswith("TKT-")


def test_ticket_update(isolated_env: dict[str, Path]) -> None:
    ticket_db_id = db.create_ticket({"title": "Before Update", "status": "Open"})
    db.update_ticket(ticket_db_id, {"title": "After Update", "status": "Resolved"})
    updated = db.get_ticket_by_db_id(ticket_db_id)
    history = db.list_ticket_history(ticket_db_id)

    assert updated is not None
    assert updated["title"] == "After Update"
    assert updated["status"] == "Resolved"
    assert any(row["field_name"] == "title" for row in history)
    assert any(row["field_name"] == "status" for row in history)


def test_attachment_linking(isolated_env: dict[str, Path]) -> None:
    ticket_db_id = db.create_ticket({"title": "Attachment Ticket"})
    image_path = isolated_env["tmp"] / "sample.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    attachment_id = db.add_ticket_attachment(ticket_db_id, image_path, "Sample")
    attachments = db.list_ticket_attachments(ticket_db_id)

    assert any(int(a["id"]) == attachment_id for a in attachments)
    linked = next(a for a in attachments if int(a["id"]) == attachment_id)
    assert Path(str(linked["file_path"])).exists()


def test_backup_creation(isolated_env: dict[str, Path]) -> None:
    result = backup.create_backup("manual_test")
    backup_dir = Path(result["destination"])

    assert backup_dir.exists()
    assert (backup_dir / "ticket_library.db").exists()
    assert (backup_dir / "backup_manifest.json").exists()
    assert (backup_dir / "app_settings_metadata.json").exists()


def test_restore_process(isolated_env: dict[str, Path]) -> None:
    baseline_backup = backup.create_backup("baseline")

    db.create_ticket({"title": "Created After Backup"})
    assert any(t["title"] == "Created After Backup" for t in db.list_tickets())

    restore_result = backup.restore_backup(baseline_backup["destination"], create_safety=True)
    restored_tickets = db.list_tickets()

    assert isinstance(restore_result["restored_from"], str)
    assert restore_result["safety_copy"] is not None
    assert not any(t["title"] == "Created After Backup" for t in restored_tickets)
