from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from pypdf import PdfReader, PdfWriter


@dataclass(frozen=True)
class PdfInfo:
    path: Path
    pages: int
    encrypted: bool


class PdfToolkitError(Exception):
    """Raised when a PDF operation cannot be completed safely."""


def get_pdf_info(path: str | Path) -> PdfInfo:
    pdf_path = _validate_pdf_path(path)
    try:
        reader = PdfReader(str(pdf_path))
        encrypted = reader.is_encrypted
        if encrypted:
            try:
                reader.decrypt("")
            except Exception:
                pass
        return PdfInfo(path=pdf_path, pages=len(reader.pages), encrypted=encrypted)
    except Exception as exc:  # pypdf raises several parser-specific exceptions.
        raise PdfToolkitError(f"Could not read PDF: {pdf_path}") from exc


def merge_pdfs(input_paths: Sequence[str | Path], output_path: str | Path) -> Path:
    paths = [_validate_pdf_path(path) for path in input_paths]
    if len(paths) < 2:
        raise PdfToolkitError("Select at least two PDF files to merge.")

    writer = PdfWriter()
    for path in paths:
        reader = _reader_for(path)
        for page in reader.pages:
            writer.add_page(page)

    return _write_pdf(writer, output_path)


def split_pdf_by_range(input_path: str | Path, page_range: str, output_path: str | Path) -> Path:
    pages = parse_page_selection(page_range)
    return extract_pages(input_path, pages, output_path)


def extract_pages(input_path: str | Path, pages: Sequence[int], output_path: str | Path) -> Path:
    source = _validate_pdf_path(input_path)
    if not pages:
        raise PdfToolkitError("Enter at least one page.")

    reader = _reader_for(source)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    for page_number in pages:
        if page_number < 1 or page_number > total_pages:
            raise PdfToolkitError(f"Page {page_number} is outside the document range 1-{total_pages}.")
        writer.add_page(reader.pages[page_number - 1])

    return _write_pdf(writer, output_path)


def rotate_pages(
    input_path: str | Path,
    pages: Sequence[int],
    degrees: int,
    output_path: str | Path,
) -> Path:
    source = _validate_pdf_path(input_path)
    if degrees not in {90, 180, 270}:
        raise PdfToolkitError("Rotation must be 90, 180, or 270 degrees.")

    reader = _reader_for(source)
    writer = PdfWriter()
    total_pages = len(reader.pages)
    selected = set(pages)

    if selected:
        invalid = [page for page in selected if page < 1 or page > total_pages]
        if invalid:
            raise PdfToolkitError(f"Page {invalid[0]} is outside the document range 1-{total_pages}.")

    for index, page in enumerate(reader.pages, start=1):
        if not selected or index in selected:
            page.rotate(degrees)
        writer.add_page(page)

    return _write_pdf(writer, output_path)


def parse_page_selection(value: str, *, max_pages: int | None = None) -> list[int]:
    text = value.strip()
    if not text:
        raise PdfToolkitError("Enter a page selection, for example 1-3,5.")

    selected: list[int] = []
    seen: set[int] = set()

    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            if not start_text.isdigit() or not end_text.isdigit():
                raise PdfToolkitError(f"Invalid page range: {part}")
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise PdfToolkitError(f"Invalid page range: {part}")
            numbers: Iterable[int] = range(start, end + 1)
        else:
            if not part.isdigit():
                raise PdfToolkitError(f"Invalid page number: {part}")
            numbers = (int(part),)

        for page_number in numbers:
            if page_number < 1:
                raise PdfToolkitError("Page numbers start at 1.")
            if max_pages is not None and page_number > max_pages:
                raise PdfToolkitError(f"Page {page_number} is outside the document range 1-{max_pages}.")
            if page_number not in seen:
                selected.append(page_number)
                seen.add(page_number)

    if not selected:
        raise PdfToolkitError("Enter at least one page.")

    return selected


def _reader_for(path: Path) -> PdfReader:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            result = reader.decrypt("")
            if result == 0:
                raise PdfToolkitError(f"Encrypted PDFs with passwords are not supported: {path.name}")
        return reader
    except PdfToolkitError:
        raise
    except Exception as exc:
        raise PdfToolkitError(f"Could not open PDF: {path}") from exc


def _validate_pdf_path(path: str | Path) -> Path:
    pdf_path = Path(path).expanduser().resolve()
    if not pdf_path.exists():
        raise PdfToolkitError(f"File does not exist: {pdf_path}")
    if not pdf_path.is_file():
        raise PdfToolkitError(f"Path is not a file: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise PdfToolkitError(f"File is not a PDF: {pdf_path.name}")
    return pdf_path


def _write_pdf(writer: PdfWriter, output_path: str | Path) -> Path:
    target = Path(output_path).expanduser().resolve()
    if target.suffix.lower() != ".pdf":
        target = target.with_suffix(".pdf")
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        with target.open("wb") as output_file:
            writer.write(output_file)
    except Exception as exc:
        raise PdfToolkitError(f"Could not write output PDF: {target}") from exc

    return target
