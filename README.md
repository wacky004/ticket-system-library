# Ticket Library Desktop (Phase 10 Finalization)

Ticket Library Desktop is an offline-first Windows desktop application for ticket operations.

## Core Design
- Live active database stays local.
- OneDrive is used for backup and restore, not as the live SQLite location.
- Intended for one active computer at a time.

## Guides / Knowledge Base
- Sidebar now includes **Guides** module.
- Guide records support:
  - `guide_id`, title/category/subcategory/difficulty
  - summary/problem/install/troubleshooting/solution/notes
  - tags, related software, archived state, timestamps
- `guide_id` format: `GDE-YYYY-######`.
- Tickets can link/unlink related guides from ticket detail view.

## Workspace Redesign
- The desktop UI now uses a modern help-desk workspace pattern:
  - collapsible global left navigation
  - Tickets 3-column layout:
    - views/filters panel
    - ticket list workspace (table + compact modes)
    - readable ticket detail/context panel
  - Guides 3-column layout:
    - category/difficulty filters
    - searchable guide list
    - readable detail tabs with attachments and linked tickets
- Readability improvements:
  - long content shown in reusable readable cards
  - preserved line breaks and paragraph spacing
  - copy-to-clipboard actions in content cards
  - cleaner notes/history/attachments viewing flow

## Project Structure
```text
Ticket Library Desktop/
|- main.py
|- requirements.txt
|- README.md
|- app/
|  |- application.py
|  |- config.py
|  |- db/
|  |  `- database.py
|  |- services/
|  |  |- backup.py
|  |  `- exports.py
|  `- ui/
|     |- main_window.py
|     |- pages.py
|     |- reports.py
|     |- settings.py
|     |- backups.py
|     `- tickets.py
|- scripts/
|  `- seed_sample_data.py
`- tests/
   |- conftest.py
   `- test_phase10_core.py
```

## Installation (Windows)
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"

# Recommended Python: 3.11–3.13
py -3.13 -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

## Run the App
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"
.venv\Scripts\activate
python main.py
```

## Seed Sample Data
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"
.venv\Scripts\activate
python scripts\seed_sample_data.py --count 20
```

## Tests
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"
.venv\Scripts\activate
pytest -q
```

Covered basic tests:
- database initialization
- ticket insert
- ticket update
- attachment linking
- backup creation
- restore process

## Backup and Restore
1. Open **Settings** and configure the OneDrive backup folder.
2. Validate and save settings.
3. Open **Backups** page to run manual backup or restore.
4. Optional: enable auto backup on close.

### OneDrive Safety Note
- Do not point live SQLite to a OneDrive-synced active DB file.
- Use backup/restore workflows only.
- Keep one active computer at a time to avoid conflicts.

## Export and Reporting
- Export filtered tickets to CSV/Excel from Tickets page.
- Export selected ticket details to PDF.
- Use Reports page for date-filtered aggregates.
- Reports now include guide distribution by category and difficulty.

## Attachments
- Managed local attachments support:
  - Tickets
  - Ticket notes
  - Guides
- Supported file types:
  - PNG, JPG, JPEG, WEBP, PDF, DOCX, XLSX, TXT, ZIP
- Attachment UI supports:
  - add/remove
  - drag and drop
  - clipboard image paste
  - open file
  - reveal containing folder
  - image preview for image formats

## Package as EXE (PyInstaller Example)
Install PyInstaller:
```powershell
pip install pyinstaller
```

Build command example:
```powershell
pyinstaller --noconfirm --clean --windowed --name "Ticket Library Desktop" main.py
```

Optional data-folder bundling example:
```powershell
pyinstaller --noconfirm --clean --windowed --name "Ticket Library Desktop" --add-data "app;app" main.py
```

## Daily Git Save Commands
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"
git add .
git commit -m "Describe your changes"
git push
```
