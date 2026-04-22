# Ticket Library Desktop (Phase 8)

Ticket Library Desktop is an offline-first Windows desktop application built with Python and PySide6.

Phase 8 adds safe OneDrive backup and restore support while keeping the live SQLite database local.

## Safety Rule
- Live active database remains local.
- OneDrive is used only for backup and restore workflows.
- Running live SQLite directly from OneDrive sync is risky and not recommended.

## Phase 8 Features
- Settings page option for OneDrive backup folder path
- Backup path validation (must exist and be a directory)
- Manual backup button (Backups page)
- Automatic backup on app exit option (Settings page)
- Backup package includes:
  - SQLite database snapshot
  - media folder
  - app settings metadata JSON
  - backup manifest JSON
- Backup logs written to `backup_logs` and shown in Backups page
- Backups page with:
  - last backup time
  - result
  - destination folder
  - restore latest button
  - restore from selected folder button
- Startup backup detection when configured
- Local-vs-backup timestamp comparison
- Startup prompt if backup is newer (or local appears fresh):
  - Restore backup
  - Keep local
  - Safety copy + restore
- Restore workflow with optional safety copy + rollback-minded media swap

## Existing Features (prior phases)
- Ticket CRUD
- Search/filter/sort
- Attachments with preview
- Notes and audit history
- Dashboard
- Reports page
- CSV/Excel/PDF export support

## Run Instructions (Windows PowerShell)
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"

# Use Python 3.11-3.13 for compatibility.
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
