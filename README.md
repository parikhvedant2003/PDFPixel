# PDFPixel

Right-click a PDF → the **PDFPixel** menu → turn its pages into images, or
merge / split / compress it — straight from your file manager, fully local, no
app to open. Works on **Linux, Windows, and macOS**.

- **Convert** every page (or a range) to **PNG / JPG / WEBP / TIFF** at any DPI.
- **Merge** several PDFs into one, **split** a PDF into per-page files.
- **Compress** — real image downsampling that keeps text sharp and selectable.

📖 [USAGE.md](USAGE.md) — every action, in and out · 🛠 [ARCHITECTURE.md](ARCHITECTURE.md) · 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) · 📦 [DISTRIBUTING.md](packaging/linux/DISTRIBUTING.md)

## Supported platforms

| Platform | Status | How to run it |
|---|---|---|
| **Linux**, glibc ≥ 2.31 — Ubuntu 20.04+, Debian 11+, Mint 20+, Pop!_OS 20.04+, Fedora 32+, **RHEL/Rocky/Alma 9+**, openSUSE Leap 15.3+/Tumbleweed, Arch & derivatives | ✅ native | `.deb` / `.rpm` / AppImage / AUR |
| **Older or musl Linux** — RHEL/Rocky/Alma 8, Debian 10, Ubuntu 18.04, CentOS 7, Alpine (glibc < 2.31 or musl) | ✅ portable | **Flatpak** (own runtime, any distro) or `pipx install pdfpixel` |
| **CPU architectures** | ✅ | x86-64 (amd64) **and** ARM64 (aarch64) — both built in CI |
| **Windows** 10 / 11 | ✅ | `pdfpixel-setup.exe` (per-user, unsigned) |
| **macOS** 12+ (Intel & Apple Silicon) | ⚠️ experimental | `.dmg`, **unsigned** — Terminal install (below) |

> **Signing status — builds are unsigned.** We don't have an **Apple Developer
> ID**, so the macOS build can't be signed/notarized: expect a Gatekeeper prompt
> and use the Terminal install method below. Windows shows a one-time SmartScreen
> prompt. The native right-click menu ships only with the Linux `.deb`/`.rpm`/AUR
> packages — AppImage, Flatpak and pip are CLI/app-only (a sandbox/portability
> limit, not a choice).

## Install

Grab the artifact for your OS from the [Releases](../../releases) page.

### Linux

Native packages are built on glibc 2.31, so they run on **glibc ≥ 2.31**
(Ubuntu 20.04+, Debian 11+, Fedora 32+, RHEL/Rocky/Alma 9+, openSUSE Leap 15.3+),
amd64 **and** arm64, with no security prompt. On **older distros** (RHEL 8,
Debian 10, Ubuntu 18.04, CentOS 7) or **musl** (Alpine), use **Flatpak** or
`pipx install pdfpixel` instead.

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
4. **Right-click a PDF** → **PDFPixel** → **All Pages** / **First Page** /
   **Custom Range…** / **Split into Pages** / **Compress**
   (Windows 11: under **Show more options**, or press **Shift+F10**).
   *(Merge is command-line only on Windows — classic shell verbs run per file.)*

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
   **First Page** / **Custom Range…** / **Split into Pages** / **Compress** /
   **Merge PDFs** (select 2+ PDFs for Merge).
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
- **Unsigned** — hence the SmartScreen / Gatekeeper prompts above. macOS
  signing/notarization needs an Apple Developer ID we don't currently have, so the
  Terminal install is the supported macOS path; Windows signing may come later
  with a certificate.
- **Sandboxed builds** (Flatpak/Snap) and the AppImage/pip CLI can't install a
  host file-manager menu — that's a platform limit. The full right-click menu
  ships with the `.deb`/`.rpm`/AUR packages.
- **Windows/macOS menus** now expose the full action set (All Pages, First Page,
  Custom Range, Split, Compress; macOS also Merge). Windows Merge stays CLI-only
  (classic shell verbs run per selected file). Lands in the next release build.
