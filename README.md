# Ticket Library Desktop (Phase 1)

Ticket Library Desktop is an offline-first Windows desktop application built with Python and PySide6.

This Phase 1 delivery focuses on the app foundation:
- clean project structure
- main desktop window
- sidebar navigation shell
- placeholder pages
- modern theme-ready UI
- SQLite database initialization
- schema and default seed data

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
|     `- theme.py
`- data/
   `- ticket_library.db (auto-created on first run)
```

## Implemented Navigation Pages
- Dashboard
- Tickets
- New Ticket
- Reports
- Backups
- Settings

## Database Initialization
On startup, the app creates `data/ticket_library.db` if it does not exist, then applies schema setup and seed defaults.

### Core Tables Created
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

### Seeded Defaults
- Statuses (stored in `app_settings`):
  - Open
  - In Progress
  - Waiting on Client
  - Resolved
  - Closed
- Priorities (stored in `app_settings`):
  - Low
  - Medium
  - High
  - Urgent
- Categories (stored in `categories`) with starter subcategories.

## Ticket Fields Included
The `tickets` table includes:
- id
- ticket_id
- title
- client_name
- va_name
- category
- subcategory
- priority
- status
- assigned_to
- source
- description
- troubleshooting
- resolution
- next_action
- tags_text
- follow_up_date
- device_name
- software_tools
- created_at
- updated_at
- resolved_at
- archived

## Run Instructions (Windows PowerShell)
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"

# Use Python 3.11-3.13 for PySide6 compatibility.
py -3.13 -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

If you only have Python 3.14 installed, install Python 3.13 (or 3.12/3.11) and rerun the setup.

## Notes for Next Phases
Phase 1 intentionally does not include advanced ticket workflows yet.
Future phases can add:
- ticket CRUD flows
- searching/filtering
- reporting widgets
- backup/restore actions
- settings UI controls
"# ticket-system-library" 
