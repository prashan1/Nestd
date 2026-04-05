import re
from pathlib import Path
from datetime import datetime


def sanitize_segment(segment: str) -> str:
    """Sanitize a path segment for use as part of a filename."""
    s = segment.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def generate_filename(
    current_path: Path,
    root_path: Path,
    document_type: str,
    date_str: str,
    extension: str = "pdf",
) -> tuple:
    """
    Generate a filename that encodes the full folder path from root.
    Returns (filename, full_destination_path).
    Raises ValueError with a user-friendly message on invalid input.
    """
    # Validate date
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        raise ValueError("Invalid date — please use YYYYMMDD format (e.g. 20250401).")

    # Compute relative path
    try:
        relative = current_path.resolve().relative_to(root_path.resolve())
    except ValueError:
        raise ValueError("The selected folder is not inside the root folder.")

    parts = relative.parts
    if not parts:
        raise ValueError("Please navigate into a subfolder — don't use the root folder itself.")

    sanitized = [sanitize_segment(p) for p in parts]
    sanitized = [p for p in sanitized if p]

    if not sanitized:
        raise ValueError("Folder names are not usable after sanitization (too many special characters).")

    path_component = "_".join(sanitized)
    doc_type_clean = sanitize_segment(document_type)

    if not doc_type_clean:
        raise ValueError("Please enter a document type.")

    ext = extension.lstrip(".")
    base = f"{path_component}_{doc_type_clean}_{date_str}"

    # Warn + truncate if filename would exceed 200 chars
    if len(base) > 195:
        max_path = 195 - len(f"_{doc_type_clean}_{date_str}")
        path_component = path_component[:max_path]
        base = f"{path_component}_{doc_type_clean}_{date_str}"

    filename = f"{base}.{ext}"

    # Collision detection — append _v2, _v3, etc.
    dest = current_path / filename
    if dest.exists():
        v = 2
        while True:
            filename = f"{base}_v{v}.{ext}"
            dest = current_path / filename
            if not dest.exists():
                break
            v += 1

    return filename, dest


def preview_filename(
    current_path,
    root_path,
    document_type: str,
    date_str: str,
    extension: str = "pdf",
) -> str:
    """
    Return a preview string of the generated filename.
    Returns a helpful hint if inputs are incomplete or invalid.
    """
    if not current_path or not root_path:
        return "Select a folder from the left panel"
    if not document_type:
        return "Select a document type above"
    if not date_str:
        return "Enter a date above"
    try:
        filename, _ = generate_filename(
            Path(current_path), Path(root_path), document_type, date_str, extension
        )
        return filename
    except ValueError as e:
        return f"⚠  {e}"


# ---------------------------------------------------------------------------
# Quick self-test — run with: python modules/file_engine.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from pathlib import Path
    import tempfile, os

    root = Path("/Root/Clients")
    current = root / "ABC Pvt Ltd" / "FY2025-26" / "GST & Tax"

    cases = [
        ("Normal path", current, root, "GST_Return", "20250401", "pdf"),
        ("Spaces in path", root / "XYZ Corp" / "FY2024", root, "Balance_Sheet", "20241231", "xlsx"),
        ("Special chars", root / "A@B#Ltd" / "Q1", root, "ITR_4", "20250401", "pdf"),
        ("Custom type", current, root, "Custom Notice Reply", "20250401", "pdf"),
    ]

    print("=== File Engine Tests ===\n")
    for name, cp, rp, dt, ds, ext in cases:
        result = preview_filename(cp, rp, dt, ds, ext)
        print(f"[{name}]\n  → {result}\n")

    # Test validation
    print("[Invalid date]")
    print(f"  → {preview_filename(current, root, 'GST_Return', 'April2025', 'pdf')}\n")

    print("[Root path used directly]")
    print(f"  → {preview_filename(root, root, 'GST_Return', '20250401', 'pdf')}\n")

    print("All tests complete.")
