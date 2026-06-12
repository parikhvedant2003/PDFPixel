# PDFPixel

Right-click any PDF in Nautilus → **Convert to Images** → every page becomes a
PNG (200 DPI) inside a sibling folder named after the PDF. One click, no dialogs,
fully local.

📖 **New here? Read the [full user guide → USAGE.md](USAGE.md)** for a detailed
walkthrough, command-line usage, output layout, and troubleshooting.

## Install

```bash
./install.sh        # checks deps, installs to ~/.local, reloads Nautilus
```

## Uninstall

```bash
./uninstall.sh
```

## Usage

- Right-click one or more PDFs → **Convert to Images**.
- Each PDF → a sibling folder `<name>/` containing `1.png`, `2.png`, … one per page.
- Folder name collisions get a ` (n)` suffix — existing data is never overwritten.
- Mixed selection: non-PDFs are skipped. A desktop notification summarises the batch.

### Page ranges

Right-click a **single** PDF and the menu expands to a submenu:

- **All Pages** — convert everything (same as the batch behaviour above).
- **Custom Range…** — a small prompt asks which pages. Enter a single range
  (`5-8`), one page (`3`), open-ended (`5-` = page 5 to end, `-8` = start to 8),
  or a comma-separated mix (`1,3-5,9`). Output files keep their original page
  numbers (`05.png`, `06.png`, …).

You can also run the helper directly:

```bash
pdfpixel file1.pdf file2.pdf        # all pages
pdfpixel --pages 5-8 report.pdf     # just pages 5–8
pdfpixel --pages 1,3-5,9 report.pdf # pages 1, 3, 4, 5, 9
```

## Requirements

`poppler-utils` · `libnotify-bin` · `zenity` · `python3-nautilus`
(`install.sh` offers to `apt install` any that are missing.)

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

`pdfpixel/core.py` is the portable conversion engine (pypdfium2 + Pillow), fully
unit-tested with real rendering. `pdfpixel/cli.py` is the entry point;
`dialog.py`/`notify.py` are the tkinter prompt and per-OS notification.
`integrations/<os>/` holds the thin file-manager shims (verified by manual
click-test — the Nautilus/Finder/Explorer APIs can't be exercised under pytest).

> **Cross-platform packaging (Linux `.deb` / Windows `.exe` / macOS `.dmg`) is
> in progress** — see `docs/superpowers/plans/2026-06-12-cross-platform.md`.

## Notes / scope

- GNOME / Nautilus only (v1). Snap/Flatpak can't register a host file-manager
  extension, so distribution is `install.sh` now, `.deb` + PPA later.
- Format/DPI fixed at PNG / 200 in v1; configurable in a later release.
