import re
import customtkinter as ctk
from pathlib import Path
from datetime import date, datetime
from tkinter import messagebox

from modules.file_engine import preview_filename, generate_filename
from modules.file_creator import create_empty_file, copy_to_clipboard

EXTENSIONS = [
    "DOCX", "XLSX", "PDF", "CSV", "XML", "ZIP",
    "JPG", "PNG", "PPTX", "TXT",
]

_PLACEHOLDER = "Add more context: client name, note etc (optional)"


class CreateFileDialog(ctk.CTkToplevel):
    """
    Modal dialog for creating a new file with an auto-generated name.
    The extra text field is always visible:
      - When '— Custom —' is selected  → it IS the document type
      - When a preset is selected       → its text is appended after the preset
    The filename preview is fully editable.
    """

    def __init__(self, master, current_path: Path, root_path: Path,
                 doc_types: list, settings=None, on_success=None):
        super().__init__(master)
        self.current_path = current_path
        self.root_path = root_path
        self.doc_types = doc_types
        self.settings = settings
        self.on_success = on_success

        self.title("Create New File")
        self.resizable(False, False)
        self.transient(master)
        self.geometry("560x580")
        self.after(50, self.lift)
        self.after(100, self.grab_set)

        include_date_default = settings.get("include_date", True) if settings else True

        self._doc_type_var     = ctk.StringVar(value="— Custom —")
        self._date_var         = ctk.StringVar(value=date.today().strftime("%d-%m-%Y"))
        self._ext_var          = ctk.StringVar(value="DOCX")
        self._include_date_var = ctk.BooleanVar(value=include_date_default)

        self._build_ui()
        self._toggle_date_fields()
        self._update_preview()

        self.after(150, self._center_on_screen)

        self._doc_type_var.trace_add("write",     lambda *_: self._on_doc_type_change())
        self._date_var.trace_add("write",         lambda *_: self._update_preview())
        self._ext_var.trace_add("write",          lambda *_: self._update_preview())
        self._include_date_var.trace_add("write", lambda *_: self._on_include_date_toggle())

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            self, text="Create New File",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(22, 4), sticky="w")

        # Path breadcrumb
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
            wraplength=512, justify="left", anchor="w",
        ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

        ctk.CTkFrame(self, height=1, fg_color=("gray82", "gray28")).grid(
            row=2, column=0, sticky="ew", padx=16
        )

        # --- Document Type label ---
        ctk.CTkLabel(
            self, text="Document Type (Optional)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=3, column=0, padx=24, pady=(16, 6), sticky="w")

        # --- Dropdown + extra text on same row ---
        doc_row = ctk.CTkFrame(self, fg_color="transparent")
        doc_row.grid(row=4, column=0, padx=24, pady=(0, 4), sticky="ew")
        doc_row.columnconfigure(1, weight=1)

        self._doc_dropdown = ctk.CTkOptionMenu(
            doc_row,
            values=self.doc_types + ["— Custom —"],
            variable=self._doc_type_var,
            command=lambda _: self._on_doc_type_change(),
            width=160, height=36,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13),
        )
        self._doc_dropdown.grid(row=0, column=0, sticky="w")

        self._extra_entry = ctk.CTkEntry(
            doc_row,
            placeholder_text=_PLACEHOLDER,
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self._extra_entry.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        self._extra_entry.bind("<KeyRelease>", lambda _: self._update_preview())

        # --- Date + File Type row ---
        date_row = ctk.CTkFrame(self, fg_color="transparent")
        date_row.grid(row=6, column=0, padx=24, pady=(14, 0), sticky="ew")

        self._include_date_cb = ctk.CTkCheckBox(
            date_row, text="Include date in filename",
            variable=self._include_date_var,
            font=ctk.CTkFont(size=13),
        )
        self._include_date_cb.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ctk.CTkLabel(date_row, text="Date",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(date_row, text="File Type",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=1, column=2, padx=(24, 0), sticky="w")

        date_input = ctk.CTkFrame(date_row, fg_color="transparent")
        date_input.grid(row=2, column=0, pady=(6, 0), sticky="w")

        self._date_entry = ctk.CTkEntry(
            date_input, textvariable=self._date_var,
            width=140, height=36, font=ctk.CTkFont(size=13),
            placeholder_text="DD-MM-YYYY",
        )
        self._date_entry.grid(row=0, column=0)
        self._date_entry.bind("<KeyRelease>", lambda _: self._update_preview())

        self._today_btn = ctk.CTkButton(
            date_input, text="Today", width=64, height=36,
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "gray35"), hover_color=("gray70", "gray45"),
            text_color=("gray10", "gray90"), command=self._set_today,
        )
        self._today_btn.grid(row=0, column=1, padx=(6, 0))

        self._ext_menu = ctk.CTkOptionMenu(
            date_row, values=EXTENSIONS, variable=self._ext_var,
            width=110, height=36,
            font=ctk.CTkFont(size=13), dropdown_font=ctk.CTkFont(size=13),
        )
        self._ext_menu.grid(row=2, column=2, padx=(24, 0), pady=(4, 0), sticky="w")

        # --- Preview (editable) ---
        ctk.CTkFrame(self, height=1, fg_color=("gray82", "gray28")).grid(
            row=7, column=0, sticky="ew", padx=16, pady=(18, 0)
        )

        preview_hdr = ctk.CTkFrame(self, fg_color="transparent")
        preview_hdr.grid(row=8, column=0, padx=24, pady=(12, 6), sticky="ew")
        preview_hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_hdr, text="Filename  (editable)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            preview_hdr, text="↺ Reset", width=70, height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            text_color=("gray40", "gray65"), hover_color=("gray84", "gray28"),
            command=self._update_preview,
        ).grid(row=0, column=1, sticky="e")

        self._preview_entry = ctk.CTkEntry(
            self, height=38,
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color=("gray91", "gray18"), border_color=("gray75", "gray35"),
        )
        self._preview_entry.grid(row=9, column=0, padx=24, sticky="ew")
        self._preview_entry.bind("<KeyRelease>", lambda _: self._refresh_btn_states())

        # --- Buttons ---
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=10, column=0, padx=24, pady=(14, 18), sticky="ew")
        btn_row.columnconfigure(0, weight=1)

        ctk.CTkButton(
            btn_row, text="Cancel", width=90, height=40,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"), hover_color=("gray88", "gray30"),
            command=self.destroy,
        ).grid(row=0, column=2, padx=(8, 0))

        self._copy_btn = ctk.CTkButton(
            btn_row, text="Copy Name", width=110, height=40,
            fg_color=("gray75", "gray40"), hover_color=("gray65", "gray50"),
            command=self._copy_name,
        )
        self._copy_btn.grid(row=0, column=1, padx=(8, 0))

        self._create_btn = ctk.CTkButton(
            btn_row, text="＋  Create File", height=40,
            command=self._create_file,
        )
        self._create_btn.grid(row=0, column=0, sticky="ew")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_doc_type_change(self):
        self._update_preview()

    def _on_include_date_toggle(self):
        self._toggle_date_fields()
        self._update_preview()
        if self.settings:
            self.settings.set("include_date", self._include_date_var.get())

    def _toggle_date_fields(self):
        state = "normal" if self._include_date_var.get() else "disabled"
        self._date_entry.configure(state=state)
        self._today_btn.configure(state=state)

    def _set_today(self):
        self._date_var.set(date.today().strftime("%d-%m-%Y"))

    def _get_doc_type(self) -> str:
        val   = self._doc_type_var.get()
        extra = self._extra_entry.get().strip()

        if val == "— Custom —":
            # extra text IS the doc type
            return extra
        else:
            # preset + optional append text
            if extra:
                extra_clean = re.sub(r"[^A-Za-z0-9_\-]", "_", extra).strip("_")
                extra_clean = re.sub(r"_+", "_", extra_clean)
                return f"{val}_{extra_clean}"
            return val

    def _get_date_str(self) -> str:
        if not self._include_date_var.get():
            return ""
        return self._date_var.get().strip()

    def _update_preview(self):
        doc_type = self._get_doc_type()
        date_str = self._get_date_str()
        ext      = self._ext_var.get().lower()

        generated = preview_filename(self.current_path, self.root_path, doc_type, date_str, ext)

        self._preview_entry.configure(state="normal")
        self._preview_entry.delete(0, "end")
        self._preview_entry.insert(0, generated)
        self._refresh_btn_states()

    def _refresh_btn_states(self):
        text = self._preview_entry.get().strip()
        ok   = bool(text) and not text.startswith("⚠") and not text.startswith("Select")
        state = "normal" if ok else "disabled"
        self._create_btn.configure(state=state)
        self._copy_btn.configure(state=state)

    def _copy_name(self):
        filename = self._preview_entry.get().strip()
        if filename:
            copy_to_clipboard(self, filename)
            self._copy_btn.configure(text="✓  Copied!")
            self.after(2000, lambda: self._copy_btn.configure(text="Copy Name"))

    def _create_file(self):
        filename = self._preview_entry.get().strip()
        if not filename:
            return
        dest = self.current_path / filename
        if dest.exists():
            messagebox.showerror("File Already Exists",
                                 f'"{filename}" already exists in this folder.', parent=self)
            return
        try:
            create_empty_file(dest)
            if self.settings and self._doc_type_var.get() != "— Custom —":
                self.settings.set("last_doc_type", self._doc_type_var.get())
            if self.on_success:
                self.on_success(dest)
            self.destroy()
        except OSError as e:
            messagebox.showerror("File System Error", str(e), parent=self)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _center_on_screen(self):
        self.update_idletasks()
        w  = 560
        h  = 580
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)*3//4}+{(sh-h)//2}")
