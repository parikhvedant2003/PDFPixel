; Inno Setup script for PDFPixel (per-user, no admin).
; Build with: ISCC.exe packaging\windows\pdfpixel.iss
; Expects the PyInstaller onedir at build\dist\pdfpixel\ (see build_exe.ps1).

#define AppName "PDFPixel"
#define AppVersion "0.2.0"
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
; Top-level cascading entry on .pdf, with a sub-menu via ExtendedSubCommandsKey.
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\PdfPixel"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Convert to Images"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\PdfPixel"; \
  ValueType: string; ValueName: "ExtendedSubCommandsKey"; ValueData: "PdfPixel.SubCommands"

; Sub-command store (resolved relative to the class root).
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\01all"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "All Pages"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\01all\command"; \
  ValueType: string; ValueData: """{#Exe}"" ""%1"""

Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\02range"; \
  ValueType: string; ValueName: "MUIVerb"; ValueData: "Custom Range..."; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PdfPixel.SubCommands\shell\02range\command"; \
  ValueType: string; ValueData: """{#Exe}"" --ask ""%1"""
