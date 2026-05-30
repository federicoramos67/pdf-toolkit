$ErrorActionPreference = "Stop"

Write-Host "Preparing PDF Toolkit build..." -ForegroundColor Cyan

function Get-PythonCommand {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @("python")
        }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 --version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @("py", "-3")
        }
    }

    throw "Python was not found. Install Python 3.10+ or enable the Windows Python launcher."
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $FilePath $($Arguments -join ' ')"
    }
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    $PythonCommand = Get-PythonCommand
    $PythonExe = $PythonCommand[0]
    $PythonArgs = @()
    if ($PythonCommand.Count -gt 1) {
        $PythonArgs = $PythonCommand[1..($PythonCommand.Count - 1)]
    }

    Invoke-Checked $PythonExe @PythonArgs -m venv .venv
}

Invoke-Checked ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
Invoke-Checked ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

$PythonPrefix = (& ".\.venv\Scripts\python.exe" -c "import sys; print(sys.base_prefix)")
$TclRoot = Join-Path $PythonPrefix "tcl"
$TclLibrary = Join-Path $TclRoot "tcl8.6"
$TkLibrary = Join-Path $TclRoot "tk8.6"
$TclDll = Join-Path $PythonPrefix "DLLs\tcl86t.dll"
$TkDll = Join-Path $PythonPrefix "DLLs\tk86t.dll"

foreach ($PathToCheck in @($TclLibrary, $TkLibrary, $TclDll, $TkDll)) {
    if (-not (Test-Path $PathToCheck)) {
        throw "Required Tcl/Tk dependency was not found: $PathToCheck"
    }
}

$BuildPath = Join-Path $ProjectRoot "build"
$DistPath = Join-Path $ProjectRoot "dist"

if (Test-Path $BuildPath) {
    Remove-Item -LiteralPath $BuildPath -Recurse -Force
}

if (Test-Path $DistPath) {
    Remove-Item -LiteralPath $DistPath -Recurse -Force
}

Get-ChildItem -Path $ProjectRoot -Filter "*.spec" -File | Remove-Item -Force

New-Item -ItemType Directory -Path $BuildPath -Force | Out-Null
$HookPath = Join-Path $BuildPath "hooks"
$PreFindHookPath = Join-Path $HookPath "pre_find_module_path"
New-Item -ItemType Directory -Path $PreFindHookPath -Force | Out-Null

@'
def pre_find_module_path(hook_api):
    # The project explicitly bundles Tcl/Tk below, so do not let PyInstaller
    # exclude tkinter when its auto-detection cannot initialize Tcl in-place.
    return
'@ | Set-Content -LiteralPath (Join-Path $PreFindHookPath "hook-tkinter.py") -Encoding UTF8

$TkRuntimeHook = Join-Path $BuildPath "pyinstaller_tk_runtime_hook.py"
@'
import os
import sys

base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
tcl_library = os.path.join(base_path, "tcl", "tcl8.6")
tk_library = os.path.join(base_path, "tcl", "tk8.6")

if os.path.isdir(tcl_library):
    os.environ["TCL_LIBRARY"] = tcl_library
if os.path.isdir(tk_library):
    os.environ["TK_LIBRARY"] = tk_library
'@ | Set-Content -LiteralPath $TkRuntimeHook -Encoding UTF8

$CommonPyInstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.ttk",
    "--hidden-import=tkinter.filedialog",
    "--hidden-import=tkinter.messagebox",
    "--hidden-import=customtkinter",
    "--hidden-import=darkdetect",
    "--collect-data", "customtkinter",
    "--collect-submodules", "customtkinter",
    "--additional-hooks-dir", $HookPath,
    "--add-data", "$TclLibrary;tcl\tcl8.6",
    "--add-data", "$TkLibrary;tcl\tk8.6",
    "--add-binary", "$TclDll;.",
    "--add-binary", "$TkDll;.",
    "--runtime-hook", $TkRuntimeHook
)

Invoke-Checked ".\.venv\Scripts\python.exe" -m PyInstaller `
    @CommonPyInstallerArgs `
    --name "PDFToolkit_EN" `
    "main.py"

Invoke-Checked ".\.venv\Scripts\python.exe" -m PyInstaller `
    @CommonPyInstallerArgs `
    --name "KitPDF_ES" `
    "main_es.py"

Get-ChildItem -Path $ProjectRoot -Filter "*.spec" -File | Remove-Item -Force

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "English executable: dist\PDFToolkit_EN.exe"
Write-Host "Spanish executable: dist\KitPDF_ES.exe"
