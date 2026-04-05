import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox

from modules.settings_manager import SettingsManager
from ui.sidebar import FolderTree
from ui.file_panel import FilePanel
from ui.create_file_dialog import CreateFileDialog
from ui.settings_dialog import SettingsDialog


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FileTrail")
        self.minsize(850, 520)
        self.after(0, lambda: self.state("zoomed"))  # open maximized on Windows

        # Persist settings in ~/.filetrail/
        config_dir = Path.home() / ".filetrail"
        self.settings = SettingsManager(config_dir)

        # Apply saved theme
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        self.current_folder: Path | None = None
        self.root_path: Path | None = None

        self._build_ui()
        self.update_idletasks()

        # Restore last root or ask on first run
        saved_root = self.settings.get("root_folder", "")
        if saved_root and Path(saved_root).is_dir():
            self._set_root(Path(saved_root))
        else:
            # Open folder picker after the window is fully visible
            self.after(200, self._prompt_root_folder)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=0)   # sidebar — fixed
        self.columnconfigure(1, weight=1)   # file panel — expands
        self.rowconfigure(0, weight=0)       # toolbar
        self.rowconfigure(1, weight=0)       # breadcrumb
        self.rowconfigure(2, weight=1)       # content

        # ---- Toolbar ------------------------------------------------
        toolbar = ctk.CTkFrame(self, height=58, corner_radius=0, fg_color=("gray94", "gray14"))
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(1, weight=1)
        toolbar.grid_propagate(False)

        ctk.CTkLabel(
            toolbar, text="FileTrail",
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=14, sticky="w")

        self._root_label = ctk.CTkLabel(
            toolbar,
            text="No folder selected",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray55"),
            anchor="w",
        )
        self._root_label.grid(row=0, column=1, padx=8, sticky="ew")

        toolbar_btns = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_btns.grid(row=0, column=2, padx=(0, 14), pady=10)

        ctk.CTkButton(
            toolbar_btns, text="Change Root",
            width=120, height=36,
            command=self._prompt_root_folder,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            hover_color=("gray84", "gray28"),
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            toolbar_btns, text="⚙  Settings",
            width=100, height=36,
            command=self._open_settings,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            hover_color=("gray84", "gray28"),
        ).grid(row=0, column=1)

        # ---- Breadcrumb ---------------------------------------------
        breadcrumb_bar = ctk.CTkFrame(self, height=34, corner_radius=0, fg_color=("gray88", "gray17"))
        breadcrumb_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        breadcrumb_bar.grid_propagate(False)
        breadcrumb_bar.columnconfigure(0, weight=1)

        self._breadcrumb_label = ctk.CTkLabel(
            breadcrumb_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
            anchor="w",
        )
        self._breadcrumb_label.grid(row=0, column=0, padx=14, pady=6, sticky="ew")

        # ---- Sidebar ------------------------------------------------
        sidebar_outer = ctk.CTkFrame(self, width=290, corner_radius=0, fg_color=("gray91", "gray12"))
        sidebar_outer.grid(row=2, column=0, sticky="nsew")
        sidebar_outer.grid_propagate(False)
        sidebar_outer.rowconfigure(1, weight=1)
        sidebar_outer.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar_outer,
            text="FOLDERS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray50"),
        ).grid(row=0, column=0, padx=14, pady=(10, 4), sticky="w")

        self._folder_tree = FolderTree(
            sidebar_outer,
            on_select=self._on_folder_select,
            fg_color=("gray91", "gray12"),
            corner_radius=0,
        )
        self._folder_tree.grid(row=1, column=0, sticky="nsew")

        # ---- File Panel ---------------------------------------------
        self._file_panel = FilePanel(
            self,
            on_create=self._on_create_file,
            on_new_folder=self._on_new_folder,
            corner_radius=0,
            fg_color=("white", "gray12"),
        )
        self._file_panel.grid(row=2, column=1, sticky="nsew")

    # ------------------------------------------------------------------
    # Root folder management
    # ------------------------------------------------------------------

    def _prompt_root_folder(self):
        folder = filedialog.askdirectory(
            title="Select Root Folder — FileTrail",
            initialdir=self.settings.get("root_folder") or str(Path.home()),
        )
        # Bring main window back to front on macOS after dialog closes
        self.lift()
        self.focus_force()
        if folder:
            self._set_root(Path(folder))

    def _set_root(self, path: Path):
        self.root_path = path
        self.settings.set("root_folder", str(path))
        display = str(path)
        if len(display) > 70:
            display = "…" + display[-68:]
        self._root_label.configure(text=f"Root:  {display}")
        self._folder_tree.set_root(path)
        # Reset file panel
        self.current_folder = None
        self._breadcrumb_label.configure(text="")
        self.update_idletasks()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_folder_select(self, path: Path):
        self.current_folder = path
        self._file_panel.set_folder(path)
        self._update_breadcrumb(path)
        self.settings.set("last_path", str(path))

    def _update_breadcrumb(self, path: Path):
        if self.root_path:
            try:
                rel = path.resolve().relative_to(self.root_path.resolve())
                parts = [self.root_path.name or str(self.root_path)] + list(rel.parts)
                self._breadcrumb_label.configure(text="  ›  ".join(parts))
                return
            except ValueError:
                pass
        self._breadcrumb_label.configure(text=str(path))

    def _on_create_file(self, folder: Path):
        if not self.root_path:
            messagebox.showerror("No Root Folder", "Please select a root folder first.")
            return
        CreateFileDialog(
            self,
            current_path=folder,
            root_path=self.root_path,
            doc_types=self.settings.doc_types,
            settings=self.settings,
            on_success=self._on_file_created,
        )

    def _on_new_folder(self, new_folder: Path):
        """Called after a subfolder is created — refresh tree, expand to it, select it."""
        # Re-expand all ancestors so the new folder is visible in the tree
        self._folder_tree.expanded.add(new_folder.parent)
        self._folder_tree.selected = new_folder
        self._folder_tree.refresh()
        self._on_folder_select(new_folder)

    def _on_file_created(self, file_path: Path):
        self._file_panel.refresh()
        # Brief status update in breadcrumb bar (non-blocking)
        original = self._breadcrumb_label.cget("text")
        self._breadcrumb_label.configure(
            text=f"✓  Created: {file_path.name}",
            text_color=("#1a7f37", "#3fb950"),
        )
        self.after(
            3500,
            lambda: self._breadcrumb_label.configure(
                text=original,
                text_color=("gray40", "gray65"),
            ),
        )

    def _open_settings(self):
        SettingsDialog(
            self,
            settings=self.settings,
            on_theme_change=None,   # theme applied inside dialog
            on_root_changed=self._set_root,
        )
