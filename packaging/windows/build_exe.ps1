# Freeze pdfpixel (onedir, windowed) and build the Inno Setup installer.
# Requires: pip install -e ".[dev]"  and  Inno Setup 6 (choco install innosetup).
$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..\..").Path

python -m PyInstaller --onedir --windowed --name pdfpixel --noconfirm `
  --paths "$root" `
  --collect-all pypdfium2 --collect-all pypdfium2_raw `
  --distpath "$root\build\dist" --workpath "$root\build\work" --specpath "$root\build" `
  "$root\packaging\entry.py"

$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
& $iscc "$root\packaging\windows\pdfpixel.iss"
Write-Host "built: $root\build\dist\pdfpixel-setup.exe"
