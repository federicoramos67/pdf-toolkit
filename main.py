from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # Drag and drop is optional at runtime.
    DND_FILES = None
    TkinterDnD = None

from pdf_tools import (
    PdfInfo,
    PdfToolkitError,
    extract_pages,
    get_pdf_info,
    merge_pdfs,
    parse_page_selection,
    rotate_pages,
    split_pdf_by_range,
)
from utils import choose_output_pdf, choose_pdf_file, choose_pdf_files, parse_dropped_files, readable_size


TEXT = {
    "app_title": "PDF Toolkit",
    "subtitle": "Merge, split, extract, and rotate PDF files",
    "files": "Selected PDFs",
    "file_count": "{count} file(s) selected",
    "add": "Add PDFs",
    "add_one": "Choose PDF",
    "remove": "Remove",
    "clear": "Clear",
    "move_up": "Move Up",
    "move_down": "Move Down",
    "drop": "Drop PDF files here",
    "drag_ready": "Drag PDF files onto the list",
    "drag_missing": "File picker ready. Install tkinterdnd2 for drag and drop.",
    "preview": "Preview",
    "no_files": "No files selected",
    "select_hint": "Select a row to remove or reorder it.",
    "name": "Name",
    "pages": "Pages",
    "size": "Size",
    "path": "Path",
    "merge": "Merge",
    "split": "Split by Range",
    "extract": "Extract Pages",
    "rotate": "Rotate",
    "page_range": "Pages",
    "page_hint": "Example: 1-3,5",
    "degrees": "Degrees",
    "all_pages": "All pages",
    "all_pages_if_blank": "All pages if blank",
    "process": "Process",
    "ready": "Ready",
    "working": "Processing...",
    "done": "Done",
    "success": "Created PDF:\n{path}",
    "error": "Error",
    "pick_files": "Choose PDF files",
    "pick_file": "Choose a PDF file",
    "save_as": "Save output PDF",
    "default_merge": "merged.pdf",
    "default_split": "split.pdf",
    "default_extract": "extracted_pages.pdf",
    "default_rotate": "rotated.pdf",
    "merge_help": "Combine selected PDFs in the order shown.",
    "single_help": "Choose one PDF, then enter the pages to process.",
    "rotate_help": "Leave pages blank to rotate the entire PDF.",
}


COLORS = {
    "bg": "#0d1117",
    "panel": "#151b23",
    "panel_alt": "#10161f",
    "border": "#273241",
    "text": "#f3f6fb",
    "muted": "#8b98a9",
    "accent": "#3b82f6",
    "accent_hover": "#60a5fa",
    "danger": "#ef4444",
    "danger_hover": "#f87171",
    "row_selected": "#1f3b63",
}


class PdfToolkitApp:
    def __init__(self, root: ctk.CTk, text: dict[str, str] | None = None) -> None:
        self.root = root
        self.text = {**TEXT, **(text or {})}
        self.pdfs: list[PdfInfo] = []
        self.selected_index: int | None = None
        self.processing = False
        self.row_frames: list[ctk.CTkFrame] = []

        self.operation_var = tk.StringVar(value=self.t("merge"))
        self.status_var = tk.StringVar(value=self.t("ready"))
        self.file_count_var = tk.StringVar(value=self.t("file_count").format(count=0))

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root.title(self.t("app_title"))
        self.root.geometry("1180x740")
        self.root.minsize(1100, 700)
        self.root.configure(fg_color=COLORS["bg"])

        self._build_layout()
        self._setup_drag_drop()
        self.refresh_files()

    def t(self, key: str) -> str:
        return self.text.get(key, key)

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=self.text["app_title"],
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=self.text["subtitle"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        content.grid_columnconfigure(0, weight=3, uniform="main")
        content.grid_columnconfigure(1, weight=2, uniform="main")
        content.grid_rowconfigure(0, weight=1)

        self._build_file_panel(content)
        self._build_operation_panel(content)

        footer = ctk.CTkFrame(self.root, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, textvariable=self.status_var, text_color=COLORS["muted"]).grid(row=0, column=0, sticky="w")

    def _build_file_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent, fg_color=COLORS["panel"], corner_radius=14, border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text=self.text["files"],
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top, textvariable=self.file_count_var, text_color=COLORS["muted"]).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.drop_label = ctk.CTkLabel(
            panel,
            text=self.text["drop"],
            fg_color=COLORS["panel_alt"],
            corner_radius=10,
            height=46,
            text_color=COLORS["muted"],
        )
        self.drop_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))
        for column in range(5):
            controls.grid_columnconfigure(column, weight=1)

        self._button(controls, self.text["add"], self.add_files, column=0, accent=True)
        self._button(controls, self.text["remove"], self.remove_selected, column=1, danger=True)
        self._button(controls, self.text["clear"], self.clear_files, column=2)
        self._button(controls, self.text["move_up"], lambda: self.move_selected(-1), column=3)
        self._button(controls, self.text["move_down"], lambda: self.move_selected(1), column=4)

        list_shell = ctk.CTkFrame(panel, fg_color=COLORS["panel_alt"], corner_radius=12)
        list_shell.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 18))
        list_shell.grid_columnconfigure(0, weight=1)
        list_shell.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(list_shell, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        header.grid_columnconfigure(0, weight=5)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)

        for col, label, anchor in ((0, "name", "w"), (1, "pages", "center"), (2, "size", "center")):
            ctk.CTkLabel(
                header,
                text=self.text[label],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["muted"],
                anchor=anchor,
            ).grid(row=0, column=col, sticky="ew", padx=6)

        self.files_frame = ctk.CTkScrollableFrame(list_shell, fg_color="transparent", corner_radius=0)
        self.files_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.files_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text=self.text["select_hint"], text_color=COLORS["muted"], font=ctk.CTkFont(size=12)).grid(
            row=4, column=0, sticky="w", padx=18, pady=(0, 16)
        )

    def _build_operation_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent, fg_color=COLORS["panel"], corner_radius=14, border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            panel,
            text=self.text["preview"],
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        self.preview_text = ctk.CTkTextbox(
            panel,
            height=165,
            fg_color=COLORS["panel_alt"],
            border_width=0,
            corner_radius=12,
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            wrap="word",
        )
        self.preview_text.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.preview_text.configure(state="disabled")

        ctk.CTkSegmentedButton(
            panel,
            variable=self.operation_var,
            values=[self.text["merge"], self.text["split"], self.text["extract"], self.text["rotate"]],
            command=self._render_operation_controls,
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["panel_alt"],
            unselected_hover_color="#1c2633",
            text_color=COLORS["text"],
            height=40,
        ).grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

        self.operation_content = ctk.CTkFrame(panel, fg_color=COLORS["panel_alt"], corner_radius=12)
        self.operation_content.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.operation_content.grid_columnconfigure(0, weight=1)

        spacer = ctk.CTkFrame(panel, fg_color="transparent")
        spacer.grid(row=4, column=0, sticky="nsew")

        self._render_operation_controls(self.operation_var.get())

    def _button(
        self,
        parent: ctk.CTkFrame,
        text: str,
        command: Callable[[], None],
        *,
        column: int,
        accent: bool = False,
        danger: bool = False,
    ) -> None:
        fg = COLORS["accent"] if accent else COLORS["danger"] if danger else "#263142"
        hover = COLORS["accent_hover"] if accent else COLORS["danger_hover"] if danger else "#334155"
        ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=38,
            corner_radius=9,
            fg_color=fg,
            hover_color=hover,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        ).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0 if column == 4 else 6))

    def _render_operation_controls(self, selected: str) -> None:
        for child in self.operation_content.winfo_children():
            child.destroy()

        if selected == self.text["merge"]:
            self._operation_header(self.text["merge"], self.text["merge_help"])
            ctk.CTkButton(
                self.operation_content,
                text=self.text["process"],
                command=self.process_merge,
                height=42,
                corner_radius=10,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 16))
            return

        if selected == self.text["split"]:
            self.split_entry = self._range_controls(self.text["split"], self.text["single_help"], self.process_split)
            return

        if selected == self.text["extract"]:
            self.extract_entry = self._range_controls(self.text["extract"], self.text["single_help"], self.process_extract)
            return

        self._operation_header(self.text["rotate"], self.text["rotate_help"])
        self.rotate_entry = self._entry(self.operation_content, row=2, placeholder=self.text["page_hint"])
        ctk.CTkLabel(
            self.operation_content,
            text=f"{self.text['page_hint']} - {self.text['all_pages_if_blank']}",
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=3, column=0, sticky="ew", padx=16, pady=(6, 12))

        self.degrees_var = tk.StringVar(value="90")
        ctk.CTkOptionMenu(
            self.operation_content,
            variable=self.degrees_var,
            values=("90", "180", "270"),
            height=38,
            fg_color="#263142",
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
        ).grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 12))
        self._single_file_and_process(row=5, command=self.process_rotate)

    def _range_controls(self, title: str, help_text: str, command: Callable[[], None]) -> ctk.CTkEntry:
        self._operation_header(title, help_text)
        entry = self._entry(self.operation_content, row=2, placeholder=self.text["page_hint"])
        ctk.CTkLabel(self.operation_content, text=self.text["page_hint"], text_color=COLORS["muted"], anchor="w").grid(
            row=3, column=0, sticky="ew", padx=16, pady=(6, 12)
        )
        self._single_file_and_process(row=4, command=command)
        return entry

    def _operation_header(self, title: str, help_text: str) -> None:
        ctk.CTkLabel(
            self.operation_content,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            self.operation_content,
            text=help_text,
            text_color=COLORS["muted"],
            anchor="w",
            wraplength=390,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

    def _entry(self, parent: ctk.CTkFrame, *, row: int, placeholder: str) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            corner_radius=9,
            fg_color="#0f1722",
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        entry.grid(row=row, column=0, sticky="ew", padx=16)
        return entry

    def _single_file_and_process(self, *, row: int, command: Callable[[], None]) -> None:
        buttons = ctk.CTkFrame(self.operation_content, fg_color="transparent")
        buttons.grid(row=row, column=0, sticky="ew", padx=16, pady=(4, 16))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            buttons,
            text=self.text["add_one"],
            command=self.add_single_file,
            height=40,
            corner_radius=9,
            fg_color="#263142",
            hover_color="#334155",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(
            buttons,
            text=self.text["process"],
            command=command,
            height=40,
            corner_radius=9,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _setup_drag_drop(self) -> None:
        if TkinterDnD is None or DND_FILES is None or not hasattr(self.root, "drop_target_register"):
            self.drop_label.configure(text=self.text["drag_missing"])
            return

        for widget in (self.root, self.drop_label, self.files_frame):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._handle_drop)
        self.drop_label.configure(text=self.text["drag_ready"])

    def _handle_drop(self, event) -> None:
        self.add_paths(parse_dropped_files(event.data))

    def add_files(self) -> None:
        self.add_paths(choose_pdf_files(self.text["pick_files"]))

    def add_single_file(self) -> None:
        file_path = choose_pdf_file(self.text["pick_file"])
        if file_path:
            self.add_paths([file_path], replace=True)

    def add_paths(self, paths: list[str] | tuple[str, ...], replace: bool = False) -> None:
        if not paths:
            return
        if replace:
            self.pdfs.clear()
            self.selected_index = None

        known = {info.path for info in self.pdfs}
        errors: list[str] = []
        for path in paths:
            try:
                info = get_pdf_info(path)
                if info.path not in known:
                    self.pdfs.append(info)
                    known.add(info.path)
            except PdfToolkitError as exc:
                errors.append(str(exc))

        self.refresh_files()
        if errors:
            messagebox.showwarning(self.text["error"], "\n".join(errors))

    def remove_selected(self) -> None:
        if self.selected_index is None:
            return
        del self.pdfs[self.selected_index]
        self.selected_index = None
        self.refresh_files()

    def clear_files(self) -> None:
        self.pdfs.clear()
        self.selected_index = None
        self.refresh_files()

    def move_selected(self, direction: int) -> None:
        if self.selected_index is None:
            return
        target = self.selected_index + direction
        if target < 0 or target >= len(self.pdfs):
            return
        self.pdfs[self.selected_index], self.pdfs[target] = self.pdfs[target], self.pdfs[self.selected_index]
        self.selected_index = target
        self.refresh_files()

    def refresh_files(self) -> None:
        for child in self.files_frame.winfo_children():
            child.destroy()
        self.row_frames.clear()

        self.file_count_var.set(self.text["file_count"].format(count=len(self.pdfs)))

        if not self.pdfs:
            ctk.CTkLabel(
                self.files_frame,
                text=self.text["no_files"],
                text_color=COLORS["muted"],
                height=80,
            ).grid(row=0, column=0, sticky="ew", pady=24)
        else:
            for index, info in enumerate(self.pdfs):
                self._add_file_row(index, info)

        self._update_preview()

    def _add_file_row(self, index: int, info: PdfInfo) -> None:
        selected = index == self.selected_index
        row = ctk.CTkFrame(
            self.files_frame,
            fg_color=COLORS["row_selected"] if selected else "#111a25",
            corner_radius=9,
            border_width=1,
            border_color=COLORS["accent"] if selected else "#1f2937",
        )
        row.grid(row=index, column=0, sticky="ew", padx=2, pady=4)
        row.grid_columnconfigure(0, weight=5)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)
        self.row_frames.append(row)

        encrypted = " (encrypted)" if info.encrypted else ""
        name = info.path.name + encrypted
        labels = (
            (0, name, "w"),
            (1, str(info.pages), "center"),
            (2, readable_size(info.path), "center"),
        )
        for column, value, anchor in labels:
            label = ctk.CTkLabel(
                row,
                text=value,
                anchor=anchor,
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=13),
            )
            label.grid(row=0, column=column, sticky="ew", padx=10, pady=9)
            label.bind("<Button-1>", lambda _event, idx=index: self._select_row(idx))
        row.bind("<Button-1>", lambda _event, idx=index: self._select_row(idx))

    def _select_row(self, index: int) -> None:
        self.selected_index = index
        self.refresh_files()

    def _update_preview(self) -> None:
        if not self.pdfs:
            content = self.text["no_files"]
        else:
            total_pages = sum(info.pages for info in self.pdfs)
            lines = [f"{len(self.pdfs)} PDF(s), {total_pages} page(s)", ""]
            for index, info in enumerate(self.pdfs, start=1):
                lines.append(f"{index}. {info.path.name}")
                lines.append(f"   {info.pages} page(s) - {readable_size(info.path)}")
                lines.append(f"   {info.path}")
            content = "\n".join(lines)

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", content)
        self.preview_text.configure(state="disabled")

    def process_merge(self) -> None:
        output = choose_output_pdf(self.text["save_as"], self.text["default_merge"])
        if output:
            self._run_operation(lambda: merge_pdfs([info.path for info in self.pdfs], output))

    def process_split(self) -> None:
        if not self._ensure_one_pdf():
            return
        page_range = self.split_entry.get()
        output = choose_output_pdf(self.text["save_as"], self.text["default_split"])
        if output:
            self._run_operation(lambda: split_pdf_by_range(self.pdfs[0].path, page_range, output))

    def process_extract(self) -> None:
        if not self._ensure_one_pdf():
            return
        page_range = self.extract_entry.get()
        output = choose_output_pdf(self.text["save_as"], self.text["default_extract"])
        if output:
            self._run_operation(lambda: extract_pages(self.pdfs[0].path, parse_page_selection(page_range, max_pages=self.pdfs[0].pages), output))

    def process_rotate(self) -> None:
        if not self._ensure_one_pdf():
            return
        page_range = self.rotate_entry.get().strip()
        try:
            pages = parse_page_selection(page_range, max_pages=self.pdfs[0].pages) if page_range else []
        except PdfToolkitError as exc:
            messagebox.showerror(self.text["error"], str(exc))
            return
        output = choose_output_pdf(self.text["save_as"], self.text["default_rotate"])
        if output:
            self._run_operation(lambda: rotate_pages(self.pdfs[0].path, pages, int(self.degrees_var.get()), output))

    def _ensure_one_pdf(self) -> bool:
        if len(self.pdfs) != 1:
            messagebox.showwarning(self.text["error"], self.text["pick_file"])
            return False
        return True

    def _run_operation(self, operation: Callable[[], Path]) -> None:
        if self.processing:
            return
        self.processing = True
        self.status_var.set(self.text["working"])

        def worker() -> None:
            try:
                result = operation()
            except Exception as exc:
                self.root.after(0, self._operation_failed, exc)
            else:
                self.root.after(0, self._operation_done, result)

        threading.Thread(target=worker, daemon=True).start()

    def _operation_done(self, result: Path) -> None:
        self.processing = False
        self.status_var.set(self.text["done"])
        messagebox.showinfo(self.text["done"], self.text["success"].format(path=result))

    def _operation_failed(self, exc: Exception) -> None:
        self.processing = False
        self.status_var.set(self.text["ready"])
        messagebox.showerror(self.text["error"], str(exc))


def create_root() -> ctk.CTk:
    if TkinterDnD is not None:
        class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.TkdndVersion = TkinterDnD._require(self)

        return CTkDnD()
    return ctk.CTk()


def main() -> None:
    root = create_root()
    PdfToolkitApp(root, TEXT)
    root.mainloop()


if __name__ == "__main__":
    main()
