import customtkinter as ctk
from pathlib import Path
from datetime import datetime


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


class FilePanel(ctk.CTkFrame):
    """
    Right panel showing files in the currently selected folder
    and a prominent 'Create File Here' button.
    """

    def __init__(self, master, on_create, **kwargs):
        super().__init__(master, **kwargs)
        self.on_create = on_create
        self.current_folder: Path | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- Header ---
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

        # --- Scrollable file list ---
        self._list = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color=("white", "gray12"))
        self._list.grid(row=1, column=0, sticky="nsew")
        self._list.columnconfigure(0, weight=1)

        # --- Bottom bar ---
        bottom = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=("gray96", "gray14"))
        bottom.grid(row=2, column=0, sticky="ew")
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
        folder_name = folder.name or str(folder)
        self._header_label.configure(
            text=f"📁  {folder_name}",
            text_color=("gray15", "gray90"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._load_files()

    def refresh(self):
        if self.current_folder:
            self._load_files()

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
        ctk.CTkLabel(hdr, text="Modified", font=ctk.CTkFont(size=12, weight="bold"), anchor="w", width=115).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        ctk.CTkLabel(hdr, text="Size", font=ctk.CTkFont(size=12, weight="bold"), anchor="e", width=65).grid(
            row=0, column=2, sticky="e", padx=(8, 4)
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

            # Truncate very long filenames for display
            name = f.name
            display = name if len(name) <= 55 else name[:52] + "…"

            ctk.CTkLabel(
                row_frame, text=display,
                font=ctk.CTkFont(size=12), anchor="w",
            ).grid(row=0, column=0, padx=8, pady=7, sticky="w")

            ctk.CTkLabel(
                row_frame, text=modified,
                font=ctk.CTkFont(size=11), width=115,
                text_color=("gray50", "gray60"), anchor="w",
            ).grid(row=0, column=1, padx=(8, 0), pady=7, sticky="w")

            ctk.CTkLabel(
                row_frame, text=size,
                font=ctk.CTkFont(size=11), width=65,
                text_color=("gray50", "gray60"), anchor="e",
            ).grid(row=0, column=2, padx=(8, 8), pady=7, sticky="e")

    def _show_placeholder(self, text: str, parent=None):
        target = parent if parent else self._list
        ctk.CTkLabel(
            target,
            text=text,
            text_color=("gray55", "gray50"),
            font=ctk.CTkFont(size=13),
            justify="center",
        ).grid(row=0, column=0, padx=20, pady=70)

    def _on_create_click(self):
        if self.current_folder and self.on_create:
            self.on_create(self.current_folder)
