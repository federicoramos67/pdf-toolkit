# PDF Toolkit

PDF Toolkit is a Windows desktop app built with Python and Tkinter. It includes English and Spanish launchers, a dark modern interface, file picking, optional drag and drop, and PDF preview metadata before processing.

## Features

- Merge multiple PDF files into one
- Split a PDF by page range
- Extract selected pages
- Rotate all pages or selected pages
- File picker for PDF input and output
- Drag and drop support through `tkinterdnd2`
- Preview selected files with name, page count, size, and full path

## Project Structure

```text
main.py          English desktop app
main_es.py       Spanish desktop app
pdf_tools.py     PDF operation layer
utils.py         Shared UI and path helpers
requirements.txt Python dependencies
build_exe.ps1    Windows executable build script
README.md        Project documentation
.gitignore       Ignored local/build files
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

English:

```powershell
python main.py
```

Spanish:

```powershell
python main_es.py
```

## Page Ranges

Use comma-separated pages and ranges:

```text
1-3,5,8-10
```

For rotation, leave the page field empty to rotate every page.

## Build Executables

Run:

```powershell
.\build_exe.ps1
```

The executables will be created in `dist`:

- `PDFToolkit_EN.exe`
- `KitPDF_ES.exe`

## Notes

- Password-protected encrypted PDFs are not supported.
- Drag and drop is enabled when `tkinterdnd2` is installed. The app still works without it through the file picker.
