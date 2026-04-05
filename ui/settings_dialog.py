import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog

from modules.settings_manager import SettingsManager


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog — root folder + appearance theme. Non-modal (no grab_set)."""

    def __init__(self, master, settings: SettingsManager, on_theme_change=None, on_root_changed=None):
        super().__init__(master)
        self.settings = settings
        self.on_theme_change = on_theme_change
        self.on_root_changed = on_root_changed

        self.title("Settings")
        self.resizable(False, False)
        self.transient(master)   # stays above main window — no grab needed
        self.after(50, self.lift)

        self._build_ui()
        self.after(10, self._center_on_screen)

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(22, 16), sticky="w")

        # --- Root folder ---
        ctk.CTkLabel(
            self, text="Root Folder",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=1, column=0, padx=24, pady=(0, 4), sticky="w")

        root_row = ctk.CTkFrame(self, fg_color="transparent")
        root_row.grid(row=2, column=0, padx=24, sticky="ew")
        root_row.columnconfigure(0, weight=1)

        current_root = self.settings.get("root_folder") or "Not set"
        self._root_label = ctk.CTkLabel(
            root_row,
            text=current_root,
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray60"),
            anchor="w",
            wraplength=290,
            justify="left",
        )
        self._root_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            root_row, text="Change…",
            width=90, height=32,
            command=self._change_root,
        ).grid(row=0, column=1, padx=(10, 0))

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=("gray82", "gray28")).grid(
            row=3, column=0, sticky="ew", padx=16, pady=16
        )

        # --- Appearance ---
        ctk.CTkLabel(
            self, text="Appearance",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=4, column=0, padx=24, pady=(0, 8), sticky="w")

        theme_row = ctk.CTkFrame(self, fg_color="transparent")
        theme_row.grid(row=5, column=0, padx=24, sticky="w")

        ctk.CTkLabel(theme_row, text="Theme:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(0, 12)
        )

        current_theme = self.settings.get("theme", "dark").capitalize()
        self._theme_seg = ctk.CTkSegmentedButton(
            theme_row,
            values=["Light", "Dark", "System"],
            command=self._on_theme,
        )
        self._theme_seg.set(current_theme)
        self._theme_seg.grid(row=0, column=1)

        # Close button
        ctk.CTkButton(
            self, text="Close",
            height=38, width=90,
            command=self.destroy,
        ).grid(row=6, column=0, padx=24, pady=(20, 22), sticky="e")

    def _change_root(self):
        folder = filedialog.askdirectory(
            title="Select Root Folder",
            initialdir=self.settings.get("root_folder") or str(Path.home()),
        )
        if folder:
            self.settings.set("root_folder", folder)
            self._root_label.configure(text=folder)
            if self.on_root_changed:
                self.on_root_changed(Path(folder))
            self.destroy()

    def _on_theme(self, value: str):
        theme = value.lower()
        ctk.set_appearance_mode(theme)
        self.settings.set("theme", theme)
        if self.on_theme_change:
            self.on_theme_change(theme)

    def _center_on_screen(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
