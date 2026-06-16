# Freeze pdfpixel (onedir, windowed) and build the Inno Setup installer.
# Requires: pip install -e ".[dev]"  and  Inno Setup 6 (choco install innosetup).
$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..\..").Path

python -m PyInstaller --onedir --windowed --name pdfpixel --noconfirm `
  --paths "$root" `
  --collect-all pypdfium2 --collect-all pypdfium2_raw --collect-all pikepdf `
  --distpath "$root\build\dist" --workpath "$root\build\work" --specpath "$root\build" `
  "$root\packaging\entry.py"

# Single-source the version from the package, inject into the installer.
$ver = (python -c "import pdfpixel; print(pdfpixel.__version__)").Trim()
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
& $iscc "/DAppVersion=$ver" "$root\packaging\windows\pdfpixel.iss"
Write-Host "built: $root\build\dist\pdfpixel-setup.exe ($ver)"
