import customtkinter as ctk
from pathlib import Path
from datetime import date
from tkinter import messagebox

from modules.file_engine import preview_filename, generate_filename
from modules.file_creator import create_empty_file, copy_to_clipboard

EXTENSIONS = ["PDF", "DOCX", "XLSX", "JPG"]


class CreateFileDialog(ctk.CTkToplevel):
    """
    Modal dialog for creating a new file with an auto-generated name
    that encodes the full folder path from root.
    """

    def __init__(self, master, current_path: Path, root_path: Path, doc_types: list, on_success=None):
        super().__init__(master)
        self.current_path = current_path
        self.root_path = root_path
        self.doc_types = doc_types
        self.on_success = on_success

        self.title("Create New File")
        self.geometry("540x560")
        self.resizable(False, False)
        self.transient(master)

        # macOS: lift above parent after a short delay
        self.after(50, self.lift)
        self.after(100, self.grab_set)

        self._center_on(master)

        # StringVars
        self._doc_type_var = ctk.StringVar(value=doc_types[0] if doc_types else "")
        self._custom_var = ctk.StringVar()
        self._date_var = ctk.StringVar(value=date.today().strftime("%Y%m%d"))
        self._ext_var = ctk.StringVar(value="PDF")
        self._showing_custom = False

        self._build_ui()
        self._update_preview()

        # Live preview — trace all inputs
        self._doc_type_var.trace_add("write", lambda *_: self._update_preview())
        self._custom_var.trace_add("write", lambda *_: self._update_preview())
        self._date_var.trace_add("write", lambda *_: self._update_preview())
        self._ext_var.trace_add("write", lambda *_: self._update_preview())

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            self, text="Create New File",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(22, 2), sticky="w")

        # Path context
        try:
            rel = self.current_path.resolve().relative_to(self.root_path.resolve())
            parts = list(rel.parts)
        except ValueError:
            parts = [self.current_path.name]

        path_display = " › ".join(parts) if parts else str(self.current_path)
        ctk.CTkLabel(
            self, text=f"📁  {path_display}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
            wraplength=492,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=("gray82", "gray28")).grid(
            row=2, column=0, sticky="ew", padx=16
        )

        # --- Document Type ---
        ctk.CTkLabel(
            self, text="Document Type",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=3, column=0, padx=24, pady=(14, 4), sticky="w")

        dropdown_values = self.doc_types + ["— Custom —"]
        self._doc_dropdown = ctk.CTkOptionMenu(
            self,
            values=dropdown_values,
            variable=self._doc_type_var,
            command=self._on_doc_type_change,
            width=492,
            height=38,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13),
        )
        self._doc_dropdown.grid(row=4, column=0, padx=24, pady=(0, 4), sticky="w")

        # Custom entry — hidden by default
        self._custom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._custom_frame.grid(row=5, column=0, padx=24, sticky="ew")
        self._custom_frame.columnconfigure(0, weight=1)

        self._custom_entry = ctk.CTkEntry(
            self._custom_frame,
            textvariable=self._custom_var,
            placeholder_text="Type your custom document type (e.g. Legal_Notice_Reply)…",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        # Start hidden
        self._custom_entry_visible = False

        # --- Date + Extension (same row) ---
        row6 = ctk.CTkFrame(self, fg_color="transparent")
        row6.grid(row=6, column=0, padx=24, pady=(12, 0), sticky="ew")

        ctk.CTkLabel(row6, text="Date", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(row6, text="File Type", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=1, padx=(40, 0), sticky="w"
        )

        self._date_entry = ctk.CTkEntry(
            row6,
            textvariable=self._date_var,
            width=160,
            height=38,
            font=ctk.CTkFont(size=13),
            placeholder_text="YYYYMMDD",
        )
        self._date_entry.grid(row=1, column=0, pady=(4, 0), sticky="w")

        self._ext_seg = ctk.CTkSegmentedButton(
            row6,
            values=EXTENSIONS,
            variable=self._ext_var,
            font=ctk.CTkFont(size=13),
        )
        self._ext_seg.grid(row=1, column=1, padx=(40, 0), pady=(4, 0), sticky="w")

        # --- Preview ---
        ctk.CTkFrame(self, height=1, fg_color=("gray82", "gray28")).grid(
            row=7, column=0, sticky="ew", padx=16, pady=(16, 0)
        )

        ctk.CTkLabel(
            self, text="Generated Filename Preview",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=8, column=0, padx=24, pady=(12, 4), sticky="w")

        preview_box = ctk.CTkFrame(self, fg_color=("gray91", "gray18"), corner_radius=8)
        preview_box.grid(row=9, column=0, padx=24, sticky="ew")
        preview_box.columnconfigure(0, weight=1)

        self._preview_label = ctk.CTkLabel(
            preview_box,
            text="",
            font=ctk.CTkFont(family="Courier New", size=12),
            wraplength=460,
            justify="left",
            anchor="w",
        )
        self._preview_label.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

        # --- Action buttons ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=10, column=0, padx=24, pady=(16, 22), sticky="ew")
        btn_row.columnconfigure(0, weight=1)

        ctk.CTkButton(
            btn_row, text="Cancel",
            width=90, height=40,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            hover_color=("gray88", "gray30"),
            command=self.destroy,
        ).grid(row=0, column=2, padx=(8, 0))

        self._copy_btn = ctk.CTkButton(
            btn_row, text="Copy Name",
            width=110, height=40,
            fg_color=("gray75", "gray40"),
            hover_color=("gray65", "gray50"),
            command=self._copy_name,
        )
        self._copy_btn.grid(row=0, column=1, padx=(8, 0))

        self._create_btn = ctk.CTkButton(
            btn_row, text="＋  Create File",
            height=40,
            command=self._create_file,
        )
        self._create_btn.grid(row=0, column=0, sticky="ew")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_doc_type_change(self, value):
        if value == "— Custom —":
            if not self._custom_entry_visible:
                self._custom_entry.grid(row=0, column=0, sticky="ew", pady=(4, 0))
                self._custom_entry_visible = True
            self.after(50, self._custom_entry.focus)
        else:
            if self._custom_entry_visible:
                self._custom_entry.grid_remove()
                self._custom_entry_visible = False
        self._update_preview()

    def _get_doc_type(self) -> str:
        val = self._doc_type_var.get()
        if val == "— Custom —":
            return self._custom_var.get().strip()
        return val

    def _update_preview(self):
        doc_type = self._get_doc_type()
        date_str = self._date_var.get().strip()
        ext = self._ext_var.get().lower()

        preview = preview_filename(self.current_path, self.root_path, doc_type, date_str, ext)
        self._preview_label.configure(text=preview)

        is_valid = (
            preview
            and not preview.startswith("⚠")
            and not preview.startswith("Select")
            and not preview.startswith("Enter")
            and not preview.startswith("Please")
        )
        state = "normal" if is_valid else "disabled"
        self._create_btn.configure(state=state)
        self._copy_btn.configure(state=state)

    def _copy_name(self):
        doc_type = self._get_doc_type()
        date_str = self._date_var.get().strip()
        ext = self._ext_var.get().lower()
        try:
            filename, _ = generate_filename(
                self.current_path, self.root_path, doc_type, date_str, ext
            )
            copy_to_clipboard(self, filename)
            self._copy_btn.configure(text="✓  Copied!")
            self.after(2000, lambda: self._copy_btn.configure(text="Copy Name"))
        except ValueError:
            pass

    def _create_file(self):
        doc_type = self._get_doc_type()
        date_str = self._date_var.get().strip()
        ext = self._ext_var.get().lower()
        try:
            filename, dest = generate_filename(
                self.current_path, self.root_path, doc_type, date_str, ext
            )
            create_empty_file(dest)
            if self.on_success:
                self.on_success(dest)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Cannot Create File", str(e), parent=self)
        except OSError as e:
            messagebox.showerror("File System Error", str(e), parent=self)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _center_on(self, master):
        self.update_idletasks()
        w, h = 540, 560
        mx = master.winfo_rootx() + master.winfo_width() // 2 - w // 2
        my = master.winfo_rooty() + master.winfo_height() // 2 - h // 2
        self.geometry(f"{w}x{h}+{mx}+{my}")
