# PDFPixel

Right-click any PDF → **Convert to Images** → every page becomes a PNG (200 DPI)
in a sibling folder named after the PDF. One click, no dialogs for "all pages",
fully local. Works on **Linux, Windows, and macOS**.

📖 Detailed walkthrough: [USAGE.md](USAGE.md).

## Install

Grab the installer for your OS from the [Releases](../../releases) page.

> The installers are **unsigned** (v1), so Windows and macOS show a one-time
> security prompt on first run. Steps to get past it are below. Permanent
> signing/notarization is tracked in issue #2.

### Linux (Debian/Ubuntu, GNOME/Nautilus)

1. Install the package (pulls `python3-nautilus` + `libnotify-bin`; the PDF
   engine and dialog are bundled — no poppler needed):
   ```bash
   sudo apt install ./pdfpixel_*.deb
   ```
2. Open **Files** (Nautilus) and **right-click a PDF** → **Convert to Images**.
   - One PDF → submenu **All Pages** / **Custom Range…**
   - If the menu doesn't appear, fully quit Files (`killall nautilus`) and reopen.

No security prompt on Linux. *(From source instead of the `.deb`: `./install.sh`
— that path uses system Python and needs `python3-tk` for the dialog.)*

### Windows 10/11

1. Download **`pdfpixel-setup.exe`** and run it (**per-user, no admin**).
2. **SmartScreen prompt** — "Windows protected your PC":
   click **More info** → **Run anyway**.
3. Finish the installer (installs to `%LOCALAPPDATA%\Programs\PDFPixel`).
4. **Right-click a PDF** → **Convert to Images** → **All Pages** / **Custom Range…**.
   - **Windows 11:** it lives under **Show more options** (or press **Shift+F10**).

Uninstall via *Settings ▸ Apps* (removes the menu entry too).

### macOS  *(experimental — see Notes)*

The build is unsigned, and **recent macOS (Sequoia) no longer offers a
right-click "Open"** for downloaded scripts — it only shows *Move to Trash*. Use
the Terminal method, which bypasses Gatekeeper's launch gate cleanly:

1. Download **`pdfpixel-0.2.1.dmg`** and **double-click it** to mount it
   (a `PDFPixel` volume appears with the app, the Quick Actions, and an installer).
2. Open **Terminal** (⌘-Space → "Terminal") and run:
   ```bash
   bash "/Volumes/PDFPixel/Install PDFPixel.command"
   ```
   If it errors writing to `/Applications`, prefix with `sudo`:
   ```bash
   sudo bash "/Volumes/PDFPixel/Install PDFPixel.command"
   ```
   This copies the app to `/Applications/PDFPixel`, installs the two Quick
   Actions to `~/Library/Services`, and clears the quarantine flag.
3. **Right-click a PDF** in Finder → **Quick Actions** →
   **PDFPixel: All Pages** / **PDFPixel: Custom Range…**.
4. If the Quick Action isn't listed: **System Settings → Privacy & Security →
   Extensions → Finder** (or **Keyboard → Keyboard Shortcuts → Services**) and
   enable PDFPixel.

**Always-works fallback** (no Finder integration needed), any OS — run the bundled
CLI directly:

```bash
/Applications/PDFPixel/pdfpixel --pages 1,3-5 ~/file.pdf   # macOS
"%LOCALAPPDATA%\Programs\PDFPixel\pdfpixel.exe" file.pdf    # Windows
pdfpixel --pages 5-8 file.pdf                               # Linux
```

> **Want no prompt at all on macOS?** Either build it yourself on your Mac
> (locally-built files carry no download-quarantine, so they just open —
> `bash packaging/macos/build_dmg.sh`), or wait for a signed + notarized release
> (issue #2, needs an Apple Developer ID).

## Usage

- **All Pages** — converts every page to `1.png`, `2.png`, … (zero-padded to the
  page count: `01.png` for a 12-page PDF).
- **Custom Range…** — a prompt (showing the page count) asks which pages:

  | You type | You get |
  |---|---|
  | `5-8` | pages 5–8 |
  | `3` | page 3 |
  | `5-` | page 5 to the end |
  | `-8` | start through page 8 |
  | `1,3-5,9` | a comma-separated mix |

- Output folder collisions get a ` (n)` suffix — existing data is never overwritten.
- Mixed/multi selection: non-PDFs skipped; each PDF gets its own folder.

### Command line

The same engine is a CLI (`pdfpixel` on Linux/macOS, `pdfpixel.exe` on Windows):

```bash
pdfpixel file.pdf                  # all pages
pdfpixel --pages 5-8 file.pdf      # pages 5–8
pdfpixel --pages 1,3-5,9 file.pdf  # a mix
pdfpixel --ask file.pdf            # pop the range dialog
```

Exit codes: `0` ok · `1` ≥1 file failed · `2` no files / malformed `--pages`.

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

- `pdfpixel/core.py` — portable engine (pypdfium2 + Pillow), fully unit-tested.
- `pdfpixel/cli.py` · `dialog.py` (tkinter) · `notify.py` (per-OS).
- `integrations/<os>/` — thin file-manager shims (manual click-test).
- `packaging/<os>/` — `.deb` / `.exe` (Inno Setup) / `.dmg` builders.
- CI (`.github/workflows/build.yml`) runs tests on all 3 OSes and builds every
  installer; a `vX.Y.Z` tag publishes a Release.

## Notes / scope

- **Self-contained**: each installer bundles a frozen Python runtime, the PDF
  engine (PDFium via `pypdfium2`), and the tkinter dialog. No system Python or
  poppler required.
- **Unsigned (v1)** — hence the SmartScreen / Gatekeeper prompts above. Code
  signing + notarization are planned.
- **Linux**: Nautilus only (Nemo/Caja/Dolphin later).
- **Windows 11**: entry under "Show more options" (legacy verb).
- **macOS**: Quick Actions are experimental, pending on-device verification.
- Format/DPI fixed at PNG / 200 in v1; configurable later.
