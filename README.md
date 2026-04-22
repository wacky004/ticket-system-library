# Ticket Library Desktop (Phase 2)

Ticket Library Desktop is an offline-first Windows desktop application built with Python and PySide6.

Phase 2 delivers full ticket CRUD on top of the Phase 1 foundation.

## Features Implemented
- Modern desktop shell with sidebar navigation
- New Ticket form with validation
- Auto-generated Ticket ID format: `TKT-YYYY-000001`
- Ticket list table (with search placeholder for next phase)
- Open/Edit ticket detail dialog
- Delete with confirmation
- Archive and Reopen flows
- Automatic timestamps (`created_at`, `updated_at`, `resolved_at` rules)
- SQLite schema initialization + seed defaults + sample tickets

## Tech Stack
- Python 3.11+ (recommended: 3.11-3.13 for current PySide6 wheel compatibility)
- PySide6
- SQLite (built into Python)
- Windows 10/11

## Project Structure
```text
Ticket Library Desktop/
|- main.py
|- requirements.txt
|- README.md
|- app/
|  |- __init__.py
|  |- application.py
|  |- config.py
|  |- db/
|  |  |- __init__.py
|  |  `- database.py
|  `- ui/
|     |- __init__.py
|     |- main_window.py
|     |- pages.py
|     |- theme.py
|     `- tickets.py
`- data/
   `- ticket_library.db (auto-created on first run)
```

## Navigation
- Dashboard (placeholder)
- Tickets (CRUD table/actions)
- New Ticket (full form)
- Reports (placeholder)
- Backups (placeholder)
- Settings (placeholder)

## Core Tables
- `tickets`
- `ticket_notes`
- `ticket_attachments`
- `ticket_history`
- `categories`
- `subcategories`
- `tags`
- `ticket_tags`
- `app_settings`
- `backup_logs`

## Seed Data
- Default statuses (`app_settings`): Open, In Progress, Waiting on Client, Resolved, Closed
- Default priorities (`app_settings`): Low, Medium, High, Urgent
- Default categories + subcategories
- Sample tickets for immediate testing

## Run Instructions (Windows PowerShell)
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"

# Use Python 3.11-3.13 for PySide6 compatibility.
py -3.13 -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## Git Save Commands
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"
git add .
git commit -m "Describe your changes"
git push
```
