"""Export services for tickets and reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_tickets_to_csv(rows: list[dict[str, Any]], destination: Path) -> Path:
    import pandas as pd

    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(destination, index=False)
    return destination


def export_tickets_to_excel(rows: list[dict[str, Any]], destination: Path) -> Path:
    import pandas as pd

    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_excel(destination, index=False, engine="openpyxl")
    return destination


def export_ticket_to_pdf(
    ticket: dict[str, Any],
    notes: list[dict[str, Any]],
    attachments: list[dict[str, Any]],
    history: list[dict[str, Any]],
    destination: Path,
) -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(destination), pagesize=letter)
    styles = getSampleStyleSheet()
    content: list[Any] = []

    content.append(Paragraph(f"Ticket Details: {ticket.get('ticket_id', '-')}", styles["Heading1"]))
    content.append(Spacer(1, 8))

    ticket_rows = []
    for key, value in ticket.items():
        if key == "id":
            continue
        ticket_rows.append([str(key), str(value or "")])

    details_table = Table(ticket_rows, colWidths=[170, 360])
    details_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, "#4a4a4a"),
                ("GRID", (0, 0), (-1, -1), 0.25, "#777777"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    content.append(details_table)
    content.append(Spacer(1, 14))

    content.append(Paragraph("Notes", styles["Heading2"]))
    if notes:
        note_rows = [["Type", "Created", "Content"]]
        for note in notes:
            note_rows.append(
                [
                    str(note.get("note_type") or ""),
                    str(note.get("created_at") or ""),
                    str(note.get("content") or ""),
                ]
            )
        note_table = Table(note_rows, colWidths=[90, 120, 320])
        note_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, "#4a4a4a"),
                    ("GRID", (0, 0), (-1, -1), 0.25, "#777777"),
                    ("BACKGROUND", (0, 0), (-1, 0), "#e8e8e8"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        content.append(note_table)
    else:
        content.append(Paragraph("No notes.", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Attachments", styles["Heading2"]))
    if attachments:
        for attachment in attachments:
            content.append(
                Paragraph(
                    f"- {attachment.get('filename', '')} ({attachment.get('added_at', '')})",
                    styles["Normal"],
                )
            )
    else:
        content.append(Paragraph("No attachments.", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Recent History", styles["Heading2"]))
    if history:
        history_rows = [["Timestamp", "Field", "Old", "New"]]
        for entry in history[:30]:
            history_rows.append(
                [
                    str(entry.get("changed_at") or ""),
                    str(entry.get("field_name") or ""),
                    str(entry.get("old_value") or ""),
                    str(entry.get("new_value") or ""),
                ]
            )
        history_table = Table(history_rows, colWidths=[120, 100, 150, 160])
        history_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, "#4a4a4a"),
                    ("GRID", (0, 0), (-1, -1), 0.25, "#777777"),
                    ("BACKGROUND", (0, 0), (-1, 0), "#e8e8e8"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        content.append(history_table)
    else:
        content.append(Paragraph("No history entries.", styles["Normal"]))

    doc.build(content)
    return destination
