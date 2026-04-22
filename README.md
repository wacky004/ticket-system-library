# Ticket Library Desktop (Phase 9)

Ticket Library Desktop is an offline-first Windows desktop app using Python + PySide6.

Phase 9 adds settings, theme persistence, shortcuts, starred/pinned tickets, duplication, unsaved-change protection, and UI polish.

## Phase 9 Highlights
- Complete Settings module:
  - app theme (dark/light)
  - default backup path
  - auto backup on close
  - default export folder
  - ticket ID prefix
  - company name + display name
- Settings persist in SQLite (`app_settings`)
- Keyboard shortcuts:
  - `Ctrl+N` new ticket
  - `Ctrl+F` focus ticket search
  - `Ctrl+S` save in new-ticket and ticket-detail forms
- Unsaved changes warning:
  - New Ticket page leave/cancel checks
  - Ticket Detail dialog close/cancel checks
- Favorite/starred tickets
- Pin ticket support
- Quick duplicate ticket
- Improved table/actions polish and feedback dialogs

## Run
```powershell
cd "C:\Users\Dev1\Desktop\Ticket Library Desktop"
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
