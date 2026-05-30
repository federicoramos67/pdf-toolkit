from __future__ import annotations

import sys
from pathlib import Path
from tkinter import filedialog


def resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


def choose_pdf_files(title: str) -> tuple[str, ...]:
    return filedialog.askopenfilenames(
        title=title,
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
    )


def choose_pdf_file(title: str) -> str:
    return filedialog.askopenfilename(
        title=title,
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
    )


def choose_output_pdf(title: str, default_name: str = "output.pdf") -> str:
    return filedialog.asksaveasfilename(
        title=title,
        defaultextension=".pdf",
        initialfile=default_name,
        filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
    )


def readable_size(path: str | Path) -> str:
    size = Path(path).stat().st_size
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{size} B"


def parse_dropped_files(raw_data: str) -> list[str]:
    files: list[str] = []
    current = []
    in_braces = False

    for char in raw_data:
        if char == "{":
            in_braces = True
            current = []
        elif char == "}":
            in_braces = False
            files.append("".join(current))
            current = []
        elif char == " " and not in_braces:
            if current:
                files.append("".join(current))
                current = []
        else:
            current.append(char)

    if current:
        files.append("".join(current))

    return [file for file in files if Path(file).suffix.lower() == ".pdf"]
