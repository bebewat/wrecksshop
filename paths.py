import sys
from pathlib import Path

def resource_path(rel: str) -> Path:
    """Resolve path for dev & PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / rel
    return Path(rel)
