# CA File Manager — INFO.md

## Project Overview
Desktop application for Chartered Accountants (CAs) in India.
Core feature: when creating a file inside a folder, the filename automatically encodes the full folder path from root — making files self-describing and easy to locate even after being moved to cloud storage, email, or shared drives.

**Example:** Navigating to `Clients/ABC_Pvt_Ltd/FY2025/GST_Returns/` and creating a file produces:
```
Clients_ABC_Pvt_Ltd_FY2025_GST_Returns_GST_Return_20250401.pdf
```

## Tech Stack
- **Language:** Python 3.11+
- **UI:** CustomTkinter (modern Tkinter wrapper)
- **Distribution:** PyInstaller → single `.exe` for Windows
- **Target platform:** Windows (primary), macOS (development)
- **No database, no cloud API** — all state is the local filesystem

## Project Structure
```
AnkitDa/
├── main.py                  # Entry point
├── app.py                   # CTk main window + event wiring (controller)
├── requirements.txt
├── build.bat                # Windows: pyinstaller → dist/CAFileManager.exe
├── build.sh                 # macOS: pyinstaller → dist/CAFileManager
├── modules/
│   ├── file_engine.py       # Core: path → filename generation + sanitization
│   ├── settings_manager.py  # Load/save ~/.ca_file_manager/settings.json
│   └── file_creator.py      # Create empty file, copy to clipboard
└── ui/
    ├── sidebar.py           # Expandable folder tree (Canvas + CTkFrame)
    ├── file_panel.py        # File list for selected folder + Create button
    ├── create_file_dialog.py # Modal: doc type, date, live preview, create
    └── settings_dialog.py   # Modal: root folder, theme toggle
```

## Settings & Persistence
- User settings stored at `~/.ca_file_manager/settings.json`
- Document type presets at `~/.ca_file_manager/document_types.json`
- No settings files are committed to the repo — they are auto-created on first run

## File Naming Convention
```
{FolderSegment1}_{FolderSegment2}_{...}_{DocumentType}_{YYYYMMDD}.{ext}
```
- Path segments are sanitized: spaces → `_`, special chars removed, consecutive `__` collapsed
- Collision detection: appends `_v2`, `_v3` if filename already exists
- Warns (but does not block) if filename exceeds 200 characters

## Document Type Presets
CA-specific presets (editable by user):
`GST_Return, GST_Annual_Return, GSTR_3B, GSTR_9, GST_Notice_Reply, ITR_1, ITR_3, ITR_4, ITR_6, Balance_Sheet, Profit_Loss, Audit_Report, TDS_Return, Form_26AS, Tax_Computation`

## Running Locally
```bash
pip install customtkinter
python main.py
```

**macOS note:** Use Python from python.org (not Homebrew) to avoid Tk rendering issues.

## Building the Executable
**Windows:**
```bat
build.bat
# → dist/CAFileManager.exe (~35 MB, no install needed)
```

**macOS:**
```bash
pip install pyinstaller
bash build.sh
# → dist/CAFileManager
```

## Key Design Decisions
- **No cloud API:** App writes files to a local folder that the user syncs via Google Drive / OneDrive. No OAuth, no API keys, no sync logic needed.
- **No database:** All state is the filesystem. Settings are plain JSON files.
- **Sidebar uses Canvas, not CTkScrollableFrame:** CTkScrollableFrame has macOS rendering issues with dynamically added widgets. The sidebar uses `tkinter.Canvas` + inner `CTkFrame` for reliability.
- **Modal dialogs use `self.after(50, self.lift)` + `self.after(100, self.grab_set)`:** Required for correct focus behavior on macOS.

## Known Issues / TODOs
- [ ] macOS: window may appear blank when using Homebrew Python — use python.org build instead
- [ ] No file rename feature yet (right-click to rename existing file to convention)
- [ ] No search/filter for files in the file panel
- [ ] Document types are not editable via the UI yet (edit `~/.ca_file_manager/document_types.json` directly)
