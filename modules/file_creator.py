from pathlib import Path


def create_empty_file(dest_path: Path) -> None:
    """Create an empty placeholder file at dest_path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.touch()


def copy_to_clipboard(widget, text: str) -> None:
    """Copy text to the system clipboard via tkinter."""
    widget.clipboard_clear()
    widget.clipboard_append(text)
    widget.update()
