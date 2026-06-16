# PDFPixel

Right-click a PDF → the **PDFPixel** menu → turn its pages into images, or
merge / split / compress it — straight from your file manager, fully local, no
app to open. Works on **Linux, Windows, and macOS**.

- **Convert** every page (or a range) to **PNG / JPG / WEBP / TIFF** at any DPI.
- **Merge** several PDFs into one, **split** a PDF into per-page files.
- **Compress** — real image downsampling that keeps text sharp and selectable.

📖 [USAGE.md](USAGE.md) — every action, in and out · 🛠 [ARCHITECTURE.md](ARCHITECTURE.md) · 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) · 📦 [DISTRIBUTING.md](packaging/linux/DISTRIBUTING.md)

## Install

Grab the artifact for your OS from the [Releases](../../releases) page.

> The installers are **unsigned** (v1), so Windows and macOS show a one-time
> security prompt on first run — steps below. Permanent signing/notarization is
> planned.

### Linux (any distro)

Artifacts are built on glibc 2.31, so they run on Ubuntu 20.04+, Debian 11+,
Fedora, RHEL 8+, openSUSE, etc. — amd64 **and** arm64. No security prompt.

| Distro family | Install |
|---|---|
| Debian/Ubuntu/Mint/Pop!_OS | `sudo apt install ./pdfpixel_*.deb` |
| Fedora/RHEL/openSUSE | `sudo dnf install ./pdfpixel-*.rpm` |
| Arch/CachyOS/EndeavourOS | `yay -S pdfpixel` *(AUR)* |
| **Any** (no install) | `chmod +x PDFPixel-*.AppImage` then run it |
| Any (Python) | `pipx install pdfpixel` *(CLI only)* |

The PDF engine and dialog are bundled — no poppler, no system Python. The
`.deb`/`.rpm` install the **right-click menu** for GNOME Files (Nautilus),
Cinnamon (Nemo), MATE (Caja) and KDE Dolphin (install the matching binding —
`nautilus-python` / `nemo-python` / `python3-caja` — for the GTK ones); XFCE
Thunar takes a one-time manual step (`integrations/linux/thunar-actions.md`).
After installing, reload the file manager (`nautilus -q`) or log out/in.

The **AppImage** and **pip/Flatpak** builds are the app/CLI only (no host
right-click menu — a sandbox/portability limit), but run anywhere:
`./PDFPixel-*.AppImage --pages 1,3-5 file.pdf`.

*(From a checkout: `./install.sh` — uses system Python, needs `python3-tk`.)*

### Windows 10/11

1. Download **`pdfpixel-setup.exe`** and run it (**per-user, no admin**).
2. **SmartScreen** — "Windows protected your PC": **More info** → **Run anyway**.
3. Finish the installer (installs to `%LOCALAPPDATA%\Programs\PDFPixel`).
4. **Right-click a PDF** → **PDFPixel** → **All Pages** / **Custom Range…**
   (Windows 11: under **Show more options**, or press **Shift+F10**).

Uninstall via *Settings ▸ Apps* (removes the menu entry too).

### macOS  *(experimental)*

The build is unsigned, and recent macOS no longer offers a right-click "Open" for
downloaded scripts, so use Terminal (it bypasses Gatekeeper's launch gate
cleanly):

1. Download **`pdfpixel-*.dmg`** and double-click to mount it.
2. In **Terminal**, run (prefix with `sudo` if it can't write to `/Applications`):
   ```bash
   bash "/Volumes/PDFPixel/Install PDFPixel.command"
   ```
   This copies the app to `/Applications/PDFPixel`, installs the Quick Actions to
   `~/Library/Services`, and clears the quarantine flag.
3. **Right-click a PDF** in Finder → **Quick Actions** → **PDFPixel: All Pages** /
   **PDFPixel: Custom Range…**.
4. Not listed? Enable it under **System Settings → Privacy & Security →
   Extensions → Finder** (or **Keyboard → Keyboard Shortcuts → Services**).

> No prompt at all: build it yourself on your Mac (locally-built files carry no
> quarantine) — `bash packaging/macos/build_dmg.sh`.

**Always-works fallback** (any OS) — run the bundled CLI directly:

```bash
/Applications/PDFPixel/pdfpixel --pages 1,3-5 ~/file.pdf    # macOS
"%LOCALAPPDATA%\Programs\PDFPixel\pdfpixel.exe" file.pdf     # Windows
pdfpixel --pages 5-8 file.pdf                                # Linux
```

## Usage at a glance

```bash
pdfpixel file.pdf                          # all pages → PNG @ 200 DPI
pdfpixel --pages 1,3-5,9 file.pdf          # a page-range mix
pdfpixel --format jpg --dpi 300 file.pdf   # JPG at print resolution
pdfpixel --ask file.pdf                    # pop the Custom… dialog
pdfpixel merge a.pdf b.pdf                 # → merged.pdf
pdfpixel split report.pdf                  # → report_p1.pdf, report_p2.pdf, …
pdfpixel compress --quality low scan.pdf   # shrink images
```

Outputs land beside the source and never overwrite it. Exit codes: `0` ok ·
`1` ≥1 file failed · `2` no files / malformed `--pages`. Full reference and the
right-click flow are in **[USAGE.md](USAGE.md)**.

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

The codebase is a thin file-manager shim that launches a self-contained CLI
(`pdfpixel/`: `core` rendering, `pdfops` merge/split/compress, `cli`, `dialog`,
`notify`); the menu is generated from one `ACTIONS` list. See
**[ARCHITECTURE.md](ARCHITECTURE.md)** for the design and
**[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, build, and release steps.

## Notes / scope

- **Self-contained**: each installer bundles a frozen Python runtime, the PDF
  engine (PDFium via `pypdfium2`, `pikepdf`), and the tkinter dialog. No system
  Python or poppler required.
- **Unsigned (v1)** — hence the SmartScreen / Gatekeeper prompts above; signing +
  notarization are planned.
- **Sandboxed builds** (Flatpak/Snap) and the AppImage/pip CLI can't install a
  host file-manager menu — that's a platform limit. The full right-click menu
  ships with the `.deb`/`.rpm`/AUR packages.
- **Windows/macOS native menus** currently expose All Pages + Custom Range; the
  newer actions are available there via the CLI (parity is in progress).
