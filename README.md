# PDFPixel

Right-click any PDF in Nautilus → **Convert to Images** → every page becomes a
PNG (200 DPI) inside a sibling folder named after the PDF. One click, no dialogs,
fully local.

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

You can also run the helper directly:

```bash
pdfpixel file1.pdf file2.pdf
```

## Requirements

`poppler-utils` · `libnotify-bin` · `python3-nautilus`
(`install.sh` offers to `apt install` any that are missing.)

## Development

```bash
pip install -r requirements-dev.txt
pytest -v
```

`src/pdfpixel.py` is the conversion CLI (fully unit-tested, including real
`pdftoppm` runs). `src/pdfpixel_nautilus.py` is the thin Nautilus `MenuProvider`
that shells out to it in the background, verified by manual click-test (the
Nautilus API can't be exercised under pytest).

## Notes / scope

- GNOME / Nautilus only (v1). Snap/Flatpak can't register a host file-manager
  extension, so distribution is `install.sh` now, `.deb` + PPA later.
- Format/DPI fixed at PNG / 200 in v1; configurable in a later release.
