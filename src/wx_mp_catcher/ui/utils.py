"""UI 辅助函数."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def open_output_directory(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    path = str(out.resolve())
    if sys.platform == "win32":
        subprocess.Popen(["explorer", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_file_or_folder(path: Path) -> None:
    target = str(path.resolve())
    if sys.platform == "win32":
        if path.is_file():
            subprocess.Popen(["explorer", "/select,", target])
        else:
            subprocess.Popen(["explorer", target])
    else:
        subprocess.Popen(["xdg-open", target])
