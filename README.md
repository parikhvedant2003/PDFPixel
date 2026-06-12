# PDFPixel

Right-click any PDF → **Convert to Images** → every page becomes a PNG (200 DPI)
in a sibling folder named after the PDF. One click, no dialogs for "all pages",
fully local. Works on **Linux, Windows, and macOS**.

📖 Detailed walkthrough: [USAGE.md](USAGE.md).

## Install

Grab the installer for your OS from the [Releases](../../releases) page.

### Linux (Debian/Ubuntu, GNOME/Nautilus)

```bash
sudo apt install ./pdfpixel_*.deb
```

Depends on `python3-nautilus` (hosts the menu) and `libnotify-bin` (notifications);
`apt` pulls them in. The PDF engine and dialog are bundled — no poppler needed.
Then open **Files** and right-click a PDF.

*(From source: `./install.sh` — needs `python3-tk` for the dialog.)*

### Windows 10/11

Run **`pdfpixel-setup.exe`** (per-user, no admin). On first run Windows SmartScreen
may warn — click **More info ▸ Run anyway**. Right-click a PDF → **Convert to
Images**. On Windows 11 it sits under **Show more options**.

### macOS

Open **`pdfpixel-*.dmg`**, then double-click **Install PDFPixel.command**.
The build is unsigned, so the first launch is blocked by Gatekeeper — **right-click
the command ▸ Open** (or run `xattr -dr com.apple.quarantine` on the mounted
volume). Then right-click a PDF in Finder → **Quick Actions ▸ PDFPixel**.
*(Experimental — see Notes.)*

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

Full plan: `docs/superpowers/plans/2026-06-12-cross-platform.md`.
