import tkinter as tk
import customtkinter as ctk
from pathlib import Path


class FolderTree(ctk.CTkFrame):
    """
    Expandable folder tree using a Canvas + inner CTkFrame for
    reliable scrolling on macOS and Windows.
    """

    def __init__(self, master, on_select, **kwargs):
        self._fc = kwargs.get("fg_color", ("gray91", "gray12"))
        super().__init__(master, **kwargs)
        self.on_select = on_select
        self.root_path: Path | None = None
        self.expanded: set = set()
        self.selected: Path | None = None
        self._buttons: list = []

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Resolve background colour for the canvas
        mode = ctk.get_appearance_mode()  # "Light" or "Dark"
        canvas_bg = "#1a1a1a" if mode == "Dark" else "#ebebeb"

        self._canvas = tk.Canvas(
            self, bg=canvas_bg, highlightthickness=0, bd=0
        )
        self._vscroll = ctk.CTkScrollbar(self, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vscroll.set)

        # Inner frame — all buttons live here
        self._inner = ctk.CTkFrame(
            self._canvas, fg_color=self._fc, corner_radius=0
        )
        self._inner.columnconfigure(0, weight=1)

        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._vscroll.grid(row=0, column=1, sticky="ns")

        # Keep canvas window width in sync with canvas width
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        # Update scroll region when inner frame size changes
        self._inner.bind("<Configure>", self._on_inner_resize)

        # Mouse-wheel scrolling (works on macOS + Windows + Linux)
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<Button-4>", self._on_wheel)
        self._canvas.bind("<Button-5>", self._on_wheel)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_root(self, root_path: Path):
        self.root_path = root_path
        self.expanded = {root_path}
        self.selected = None
        self._render()

    def refresh(self):
        self._render()

    # ------------------------------------------------------------------
    # Canvas helpers
    # ------------------------------------------------------------------

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._canvas_win, width=event.width)

    def _on_inner_resize(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_wheel(self, event):
        if event.num == 4:          # Linux scroll up
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:        # Linux scroll down
            self._canvas.yview_scroll(1, "units")
        else:
            delta = event.delta
            # Windows gives ±120; macOS gives ±1 (sometimes larger)
            if abs(delta) >= 120:
                delta = delta // 120
            self._canvas.yview_scroll(-delta, "units")

    # ------------------------------------------------------------------
    # Tree rendering
    # ------------------------------------------------------------------

    def _get_subdirs(self, path: Path) -> list:
        try:
            return sorted(
                [p for p in path.iterdir()
                 if p.is_dir() and not p.name.startswith(".")],
                key=lambda x: x.name.lower(),
            )
        except (PermissionError, OSError):
            return []

    def _clear(self):
        for w in self._buttons:
            w.destroy()
        self._buttons = []

    def _render(self):
        self._clear()

        if self.root_path is None:
            lbl = ctk.CTkLabel(
                self._inner,
                text="No folder selected.\nClick 'Change Root' above.",
                text_color=("gray55", "gray55"),
                font=ctk.CTkFont(size=12),
                justify="center",
            )
            lbl.grid(row=0, column=0, padx=12, pady=40, sticky="ew")
            self._buttons.append(lbl)
            return

        row_n = [0]
        self._render_node(self.root_path, depth=0, row=row_n)

        # Force geometry + scrollregion update
        self._inner.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _render_node(self, path: Path, depth: int, row: list):
        subdirs = self._get_subdirs(path)
        has_children = bool(subdirs)
        is_expanded = path in self.expanded
        is_selected = path == self.selected

        display = path.name if depth > 0 else (path.name or str(path))
        arrow = ("▼  " if is_expanded else "▶  ") if has_children else "     "

        if is_selected:
            fg = ("#2B7BE9", "#1F5BB5")
            tc = ("white", "white")
            hover = ("#2466c8", "#1a4d99")
        else:
            fg = "transparent"
            tc = ("gray15", "gray90")
            hover = ("gray85", "gray28")

        btn = ctk.CTkButton(
            self._inner,
            text=f"{arrow}{display}",
            anchor="w",
            fg_color=fg,
            text_color=tc,
            hover_color=hover,
            corner_radius=6,
            height=30,
            font=ctk.CTkFont(size=13),
            command=lambda p=path: self._on_click(p),
        )
        btn.grid(row=row[0], column=0, sticky="ew",
                 padx=(depth * 14 + 4, 4), pady=1)
        self._buttons.append(btn)
        row[0] += 1

        if is_expanded:
            for child in subdirs:
                self._render_node(child, depth + 1, row)

    def _on_click(self, path: Path):
        if path in self.expanded:
            self.expanded.discard(path)
        else:
            self.expanded.add(path)
        self.selected = path
        self._render()
        self.on_select(path)
