import os
import customtkinter as ctk
from pathlib import Path
from datetime import datetime
from tkinter import messagebox


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


class FilePanel(ctk.CTkFrame):
    """
    Right panel showing files in the currently selected folder,
    a 'Create File Here' button, and a 'New Folder' inline input.
    """

    def __init__(self, master, on_create, on_new_folder=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_create = on_create
        self.on_new_folder = on_new_folder
        self.current_folder: Path | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)   # file list expands

        # --- Header row ---
        self._header = ctk.CTkFrame(self, height=44, corner_radius=0, fg_color=("gray96", "gray14"))
        self._header.grid(row=0, column=0, sticky="ew")
        self._header.columnconfigure(0, weight=1)
        self._header.grid_propagate(False)

        self._header_label = ctk.CTkLabel(
            self._header,
            text="Select a folder to view its files",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray55"),
            anchor="w",
        )
        self._header_label.grid(row=0, column=0, padx=14, pady=10, sticky="w")

        # Action buttons in header (right-aligned)
        hdr_btns = ctk.CTkFrame(self._header, fg_color="transparent")
        hdr_btns.grid(row=0, column=1, padx=(0, 10), pady=8, sticky="e")

        self._new_folder_btn = ctk.CTkButton(
            hdr_btns,
            text="＋ New Folder",
            width=110,
            height=28,
            state="disabled",
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray75"),
            hover_color=("gray84", "gray28"),
            font=ctk.CTkFont(size=11),
            command=self._show_new_folder_bar,
        )
        self._new_folder_btn.grid(row=0, column=0, padx=(0, 6))

        self._explorer_btn = ctk.CTkButton(
            hdr_btns,
            text="Open in Explorer",
            width=130,
            height=28,
            state="disabled",
            fg_color="transparent",
            border_width=1,
            text_color=("gray30", "gray75"),
            hover_color=("gray84", "gray28"),
            font=ctk.CTkFont(size=11),
            command=self._open_in_explorer,
        )
        self._explorer_btn.grid(row=0, column=1)

        # --- Inline "New Folder" input bar (hidden by default) ---
        self._new_folder_bar = ctk.CTkFrame(
            self, height=48, corner_radius=0,
            fg_color=("gray90", "gray16"),
        )
        self._new_folder_bar.columnconfigure(0, weight=1)
        self._new_folder_bar.grid_propagate(False)
        # Not gridded initially

        ctk.CTkLabel(
            self._new_folder_bar,
            text="Folder name:",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
        ).grid(row=0, column=0, padx=(14, 6), pady=10, sticky="w")

        self._folder_name_entry = ctk.CTkEntry(
            self._new_folder_bar,
            placeholder_text="e.g. FY2026-27",
            height=30,
            font=ctk.CTkFont(size=13),
        )
        self._folder_name_entry.grid(row=0, column=1, pady=10, sticky="ew", padx=(0, 6))
        self._folder_name_entry.bind("<Return>", lambda _: self._confirm_new_folder())
        self._folder_name_entry.bind("<Escape>", lambda _: self._hide_new_folder_bar())

        ctk.CTkButton(
            self._new_folder_bar,
            text="Create",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            command=self._confirm_new_folder,
        ).grid(row=0, column=2, padx=(0, 4), pady=10)

        ctk.CTkButton(
            self._new_folder_bar,
            text="✕",
            width=30,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray40", "gray65"),
            command=self._hide_new_folder_bar,
        ).grid(row=0, column=3, padx=(0, 8), pady=10)

        self._new_folder_bar_visible = False

        # --- Scrollable file list ---
        self._list = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color=("white", "gray12"))
        self._list.grid(row=2, column=0, sticky="nsew")
        self._list.columnconfigure(0, weight=1)

        # --- Bottom bar ---
        bottom = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=("gray96", "gray14"))
        bottom.grid(row=3, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        bottom.grid_propagate(False)

        self._create_btn = ctk.CTkButton(
            bottom,
            text="＋  Create File Here",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            state="disabled",
            command=self._on_create_click,
        )
        self._create_btn.grid(row=0, column=0, padx=14, pady=11, sticky="ew")

        self._show_placeholder("Select a folder from the left panel\nto view files and create new ones.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_folder(self, folder: Path):
        self.current_folder = folder
        self._create_btn.configure(state="normal")
        self._explorer_btn.configure(state="normal")
        self._new_folder_btn.configure(state="normal")
        folder_name = folder.name or str(folder)
        self._header_label.configure(
            text=f"📁  {folder_name}",
            text_color=("gray15", "gray90"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._hide_new_folder_bar()
        self._load_files()

    def refresh(self):
        if self.current_folder:
            self._load_files()

    # ------------------------------------------------------------------
    # New Folder inline bar
    # ------------------------------------------------------------------

    def _show_new_folder_bar(self):
        if not self._new_folder_bar_visible:
            self._new_folder_bar.grid(row=1, column=0, sticky="ew")
            self._new_folder_bar_visible = True
        self._folder_name_entry.delete(0, "end")
        self.after(50, self._folder_name_entry.focus)

    def _hide_new_folder_bar(self):
        if self._new_folder_bar_visible:
            self._new_folder_bar.grid_remove()
            self._new_folder_bar_visible = False

    def _confirm_new_folder(self):
        name = self._folder_name_entry.get().strip()
        if not name:
            return
        # Basic sanitization — no path separators
        invalid = set(r'\/:*?"<>|')
        bad = [c for c in name if c in invalid]
        if bad:
            messagebox.showerror(
                "Invalid Name",
                f"Folder name cannot contain: {' '.join(sorted(set(bad)))}",
                parent=self,
            )
            return
        new_path = self.current_folder / name
        if new_path.exists():
            messagebox.showerror("Already Exists", f'A folder named "{name}" already exists here.', parent=self)
            return
        try:
            new_path.mkdir()
        except OSError as e:
            messagebox.showerror("Could Not Create Folder", str(e), parent=self)
            return
        self._hide_new_folder_bar()
        if self.on_new_folder:
            self.on_new_folder(new_path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_files(self):
        for w in self._list.winfo_children():
            w.destroy()

        try:
            files = sorted(
                [f for f in self.current_folder.iterdir() if f.is_file() and not f.name.startswith(".")],
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )
        except (PermissionError, OSError):
            files = []

        if not files:
            self._show_placeholder(
                "No files here yet.\n\nClick  ＋ Create File Here  to add one.",
                parent=self._list,
            )
            return

        # Column headers
        hdr = ctk.CTkFrame(self._list, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text="Name", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(hdr, text="Type", font=ctk.CTkFont(size=12, weight="bold"), anchor="w", width=48).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        ctk.CTkLabel(hdr, text="Modified", font=ctk.CTkFont(size=12, weight="bold"), anchor="w", width=100).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        ctk.CTkLabel(hdr, text="Size", font=ctk.CTkFont(size=12, weight="bold"), anchor="e", width=60).grid(
            row=0, column=3, sticky="e", padx=(8, 4)
        )

        # Separator
        ctk.CTkFrame(self._list, height=1, fg_color=("gray80", "gray30")).grid(
            row=1, column=0, sticky="ew", padx=10, pady=(0, 4)
        )

        for i, f in enumerate(files):
            bg = ("gray97", "gray16") if i % 2 == 0 else ("white", "gray13")
            row_frame = ctk.CTkFrame(self._list, fg_color=bg, corner_radius=4)
            row_frame.grid(row=i + 2, column=0, sticky="ew", padx=10, pady=1)
            row_frame.columnconfigure(0, weight=1)

            try:
                stat = f.stat()
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%d %b %Y")
                size = _format_size(stat.st_size)
            except OSError:
                modified = "—"
                size = "—"

            name = f.name
            ext_label = f.suffix.upper().lstrip(".") or "—"
            display = name if len(name) <= 52 else name[:49] + "…"

            ctk.CTkLabel(
                row_frame, text=display,
                font=ctk.CTkFont(size=12), anchor="w",
            ).grid(row=0, column=0, padx=8, pady=7, sticky="w")

            ctk.CTkLabel(
                row_frame, text=ext_label,
                font=ctk.CTkFont(size=11), width=48,
                text_color=("gray50", "gray60"), anchor="w",
            ).grid(row=0, column=1, padx=(8, 0), pady=7, sticky="w")

            ctk.CTkLabel(
                row_frame, text=modified,
                font=ctk.CTkFont(size=11), width=100,
                text_color=("gray50", "gray60"), anchor="w",
            ).grid(row=0, column=2, padx=(8, 0), pady=7, sticky="w")

            ctk.CTkLabel(
                row_frame, text=size,
                font=ctk.CTkFont(size=11), width=60,
                text_color=("gray50", "gray60"), anchor="e",
            ).grid(row=0, column=3, padx=(8, 8), pady=7, sticky="e")

    def _show_placeholder(self, text: str, parent=None):
        target = parent if parent else self._list
        ctk.CTkLabel(
            target,
            text=text,
            text_color=("gray55", "gray50"),
            font=ctk.CTkFont(size=13),
            justify="center",
        ).grid(row=0, column=0, padx=20, pady=70)

    def _open_in_explorer(self):
        if self.current_folder:
            os.startfile(str(self.current_folder))

    def _on_create_click(self):
        if self.current_folder and self.on_create:
            self.on_create(self.current_folder)
