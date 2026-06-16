# PDFPixel — User Guide

What every menu item and command does, what you put in, and what you get out.
No internals here — for those see [ARCHITECTURE.md](ARCHITECTURE.md). To install,
see the [README](README.md).

PDFPixel works two ways, with the **same engine** behind both:

1. **Right-click a file in your file manager** → the **PDFPixel** menu.
2. **The `pdfpixel` command** in a terminal.

Everything runs locally. Nothing is uploaded.

---

## Table of contents

1. [The right-click menu](#1-the-right-click-menu)
2. [The "Custom…" dialog](#2-the-custom-dialog)
3. [Command line](#3-command-line)
4. [What each action outputs](#4-what-each-action-outputs)
5. [Page ranges](#5-page-ranges)
6. [Formats & resolution](#6-formats--resolution)
7. [Compression quality](#7-compression-quality)
8. [Batches, selections & collisions](#8-batches-selections--collisions)
9. [When something fails](#9-when-something-fails)
10. [Exit codes & notifications](#10-exit-codes--notifications)
11. [Uninstall](#11-uninstall)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. The right-click menu

Select one or more PDFs in your file manager and right-click. The menu entry
only appears when the selection contains at least one PDF (detected by file
type, not just the `.pdf` name). On **Linux** you get the full **PDFPixel ▸**
submenu:

| Item | What it does | Shown when |
|---|---|---|
| **All Pages → PNG** | every page → PNG, one folder per PDF | any PDF(s) selected |
| **First Page → PNG** | just page 1 → PNG | exactly one PDF |
| **Custom…** | opens the dialog (format + resolution + page range) | exactly one PDF |
| **Merge selected PDFs** | combine the selection into one PDF | 2+ PDFs selected |
| **Split into pages** | one single-page PDF per page | exactly one PDF |
| **Compress** | shrink the PDF's images | exactly one PDF |

Each action runs in the background — your file manager never freezes — and a
desktop notification confirms when it's done.

> **Linux file managers:** GNOME Files (Nautilus), Cinnamon (Nemo), MATE (Caja),
> KDE Dolphin, and XFCE Thunar are all supported (Thunar needs a one-time manual
> step — see `integrations/linux/thunar-actions.md`).
>
> **Windows & macOS:** the native menu now exposes **All Pages**, **First Page**,
> **Custom Range**, **Split** and **Compress** (macOS Quick Actions also include
> **Merge**). On Windows, **Merge** is command-line only (classic shell verbs run
> per file). Format/DPI are chosen in the Custom… dialog on every OS.

---

## 2. The "Custom…" dialog

Right-click **one** PDF → **Custom…**. A small window shows the page count and
lets you choose, in one place:

- **Format** — PNG · JPG · WEBP · TIFF
- **Resolution** — Screen (96) · Default (200) · Print (300) · High (600) DPI
- **Pages** — a range spec (see [Page ranges](#5-page-ranges))

Click **Convert**, or **Cancel** / leave it blank to do nothing.

---

## 3. Command line

The same engine is the `pdfpixel` command (`pdfpixel.exe` on Windows). The first
word picks the action; with no action word it converts.

```bash
# convert (the default action)
pdfpixel file.pdf                          # all pages → PNG @ 200 DPI
pdfpixel a.pdf b.pdf c.pdf                 # batch — each gets its own folder
pdfpixel --pages 5-8 file.pdf              # only pages 5–8
pdfpixel --pages 1,3-5,9 file.pdf          # a mix
pdfpixel --format jpg --dpi 300 file.pdf   # JPG at print resolution
pdfpixel --ask file.pdf                    # pop the Custom… dialog

# PDF operations
pdfpixel merge a.pdf b.pdf c.pdf           # → merged.pdf (beside the first)
pdfpixel split report.pdf                  # → report_p1.pdf, report_p2.pdf, …
pdfpixel compress scan.pdf                 # shrink images (medium)
pdfpixel compress --quality low scan.pdf   # shrink harder

pdfpixel --version
```

`--pages`, `--format`, and `--dpi` apply to the convert action and, unlike the
menu, the same `--pages` spec can be applied across several files at once.

---

## 4. What each action outputs

Outputs always land **beside the source**, and the **source file is never
overwritten or modified**.

**Convert** → a folder named after the PDF, one image per page:

```
~/Documents/
├── invoice.pdf
└── invoice/            ← created
    ├── 1.png
    ├── 2.png
    └── 3.png
```

File names are zero-padded to the page count so they sort correctly: `1.png…9.png`,
`01.png…42.png`, `001.png…123.png`. With a custom range, files keep their
**original page numbers** (`05.png`, `06.png`, …).

**Merge** → `merged.pdf` in the first file's folder (bumped to `merged-1.pdf`,
`merged-2.pdf`… if one already exists).

**Split** → one `name_pN.pdf` per page (`report_p1.pdf`, `report_p2.pdf`, …).

**Compress** → `name_compressed.pdf`.

If a convert output folder already exists, PDFPixel appends ` (n)` —
`invoice (1)/`, `invoice (2)/` — so repeated runs never clobber earlier output.

---

## 5. Page ranges

Both the dialog and `--pages` accept the same spec:

| You type | You get |
|---|---|
| `5-8` | pages 5, 6, 7, 8 |
| `3` | page 3 only |
| `5-` | page 5 to the end |
| `-8` | the start through page 8 |
| `1,3-5,9` | a comma-separated mix — pages 1, 3, 4, 5, 9 |

A range that overshoots the end (e.g. `5-100` on a 12-page PDF) simply stops at
the last page. A range entirely past the end (e.g. `50-` on 12 pages) produces
nothing and is reported as a failure — no empty folder is left behind.

---

## 6. Formats & resolution

- **Formats:** `png` (default), `jpg`, `webp`, `tiff`. JPG is flattened to
  opaque RGB (no transparency); PNG/WEBP/TIFF keep an alpha channel.
- **Resolution (DPI):** default **200**. Higher DPI = sharper and larger files
  (Screen 96 / Print 300 / High 600 are handy presets in the dialog; on the CLI
  pass any `--dpi N`).

---

## 7. Compression quality

`compress` performs **real image compression** — it downsamples and re-encodes
the photos inside the PDF, then tidies the file structure. **Text and vector
graphics stay sharp and selectable**; images with transparency, or CMYK/indexed
images, are left untouched so nothing is corrupted.

| `--quality` | Max image dimension | JPEG quality | Use for |
|---|---|---|---|
| `low` | 1200 px | 60 | smallest file (email, web) |
| `medium` *(default)* | 2000 px | 75 | balanced |
| `high` | unchanged | 85 | light squeeze, keep resolution |

The result notification reports the actual reduction, e.g.
`Compressed 7.1 MB → 758 KB (-90%)`. A PDF that is mostly text won't shrink much —
there are no large images to reduce.

---

## 8. Batches, selections & collisions

- **Batches** — select several PDFs and convert in one click; each gets its own
  folder, with a single summary notification at the end.
- **Mixed selections** — non-PDF files are silently skipped.
- **Merge** uses the selection order. **Split/Compress/First Page/Custom…** act
  on a single PDF, so they're hidden when several are selected.
- **Collisions** — outputs are auto-suffixed; existing files/folders are never
  overwritten.

---

## 9. When something fails

A failure on one file never aborts the rest of a batch. Common cases:

- **Encrypted / password-protected PDF** — can't be read without the password →
  reported as failed, no partial output.
- **Corrupt / unreadable PDF** — reported with the underlying error.
- **Read-only directory** — output can't be written there → that file is
  reported as a "read-only directory" failure.

The final notification names what failed, e.g.:

```
Converted 2 PDFs · 1 failed
5 pages total
✗ secret.pdf: encrypted or unreadable PDF
```

---

## 10. Exit codes & notifications

When run from a terminal, `pdfpixel` prints a one-line summary and returns:

| Exit code | Meaning |
|---|---|
| `0` | success |
| `1` | at least one file failed (the rest still ran) |
| `2` | no files given, or a malformed `--pages` value |

It also sends one desktop notification (via the OS notifier). If the notifier
isn't available, the work still happens — you just don't get the popup; the
terminal summary is printed either way.

---

## 11. Uninstall

- **Linux (from source):** `./uninstall.sh` removes the CLI and the file-manager
  extension, then reloads the file manager. Packaged installs:
  `sudo apt remove pdfpixel` / `sudo dnf remove pdfpixel`, or just delete the
  AppImage.
- **Windows:** *Settings ▸ Apps ▸ PDFPixel ▸ Uninstall* (removes the menu entry).
- **macOS:** delete `/Applications/PDFPixel` and the
  `~/Library/Services/PDFPixel-*.workflow` Quick Actions.

Image folders and PDFs you've already produced are never touched by uninstalling.

---

## 12. Troubleshooting

**The PDFPixel menu doesn't appear (Linux).**
1. Reload the file manager after installing: `nautilus -q` (or `nemo -q` /
   `caja -q`), then reopen it — or log out and back in.
2. Confirm the binding is installed: `dpkg -l python3-nautilus`.
3. Run the file manager from a terminal (`nautilus -q; nautilus`) and watch for
   Python import errors — that output is the source of truth for a load failure.

**The menu is there but nothing happens.**
- Run the CLI directly on the same file to see the real error:
  `pdfpixel /path/to/your.pdf`.
- Confirm the command resolves: `command -v pdfpixel`.

**`pdfpixel: command not found`.**
- `~/.local/bin` isn't on your `PATH`; add it, or call the full path
  `~/.local/bin/pdfpixel`.

**Compression barely changed the size.**
- The PDF is probably text/vector-heavy (no large images to shrink), or its
  images are already small. Try `--quality low` for the most aggressive setting.
