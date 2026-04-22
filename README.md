# Ticket Library Desktop (Phase 4)

Ticket Library Desktop is an offline-first Windows desktop application built with Python and PySide6.

Phase 4 adds image attachment management to tickets using local file storage (not database blobs).

## Features Implemented
- Modern desktop shell with sidebar navigation
- Full ticket CRUD and browser/search/filter/sort
- Auto-generated Ticket ID format: `TKT-YYYY-000001`
- Ticket detail editor with dedicated **Attachments** tab
- Attach multiple images per ticket (`PNG`, `JPG`, `JPEG`, `WEBP`)
- Thumbnail previews and full-size preview dialog
- Remove attachment with confirmation
- Graceful handling of missing attachment files
- Drag-and-drop image attach support
- Paste image from clipboard support
- Automatic timestamps (`created_at`, `updated_at`, `resolved_at` rules)
- SQLite schema initialization + seed defaults + sample tickets
- SQLite indexes for faster ticket browsing/search paths

## Attachment Storage Design
- Files are stored locally under: `media/attachments/<ticket_db_id>/`
- SQLite stores attachment references and metadata in `ticket_attachments`
- No blob storage is used

### Attachment Record Fields
- `id`
- `ticket_id`
- `filename`
- `file_path`
- `added_at`
- `note_label`

(Compatibility columns from earlier phases are still supported.)

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
|- data/
|  `- ticket_library.db
`- media/
   `- attachments/
```

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
