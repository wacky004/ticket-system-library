# Ticket Library Desktop (Phase 6)

Ticket Library Desktop is an offline-first Windows desktop application built with Python and PySide6.

Phase 6 adds a live dashboard with operational summaries and recent activity insights.

## Features Implemented
- Modern desktop shell with sidebar navigation
- Full ticket CRUD, browsing/search/filter/sort
- Ticket detail tabs: Details, Attachments, Notes, History
- Attachment management (PNG/JPG/JPEG/WEBP) with thumbnail + preview
- Internal notes and ticket audit history
- **Live Dashboard** with:
  - summary cards (Total, Open, In Progress, Pending, Resolved, Archived)
  - recent tickets section
  - ticket counts by priority
  - ticket counts by category
  - upcoming follow-ups section
  - last backup status placeholder

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
