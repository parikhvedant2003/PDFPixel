; Inno Setup script for PDFPixel (per-user, no admin).
; Build with: ISCC.exe packaging\windows\pdfpixel.iss
; Expects the PyInstaller onedir at build\dist\pdfpixel\ (see build_exe.ps1).

#define AppName "PDFPixel"
; build_exe.ps1 passes the real version via /DAppVersion=X.Y.Z; this is the fallback.
#ifndef AppVersion
  #define AppVersion "0.3.0"
#endif
#define Exe "{app}\pdfpixel.exe"

[Setup]
AppId={{8F2C9A41-3B7D-4E16-9C2A-PDFPIXEL0001}}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\PDFPixel
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\build\dist
OutputBaseFilename=pdfpixel-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Files]
Source: "..\..\build\dist\pdfpixel\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Registry]
; Top-level cascading "PDFPixel" entry on .pdf, with a sub-menu via ExtendedSubCommandsKey.
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\PdfPixel"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "PDFPixel"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\PdfPixel"; \
  ValueType: string; ValueName: "ExtendedSubCommandsKey"; ValueData: "PdfPixel.SubCommands"

; Sub-command store (resolved relative to the class root). Numbered for ordering.
; NOTE: classic shell verbs are invoked once PER selected file (%1), so "Merge"
; (needs all selected files at once) is intentionally CLI-only on Windows.
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\01all"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "All Pages"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\01all\command"; \
  ValueType: string; ValueData: """{#Exe}"" ""%1"""

Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\02first"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "First Page"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\02first\command"; \
  ValueType: string; ValueData: """{#Exe}"" --pages 1 ""%1"""

Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\03range"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Custom Range..."; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\03range\command"; \
  ValueType: string; ValueData: """{#Exe}"" --ask ""%1"""

Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\04split"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Split into Pages"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\04split\command"; \
  ValueType: string; ValueData: """{#Exe}"" split ""%1"""

Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\05compress"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Compress"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\05compress\command"; \
  ValueType: string; ValueData: """{#Exe}"" compress ""%1"""
