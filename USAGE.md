# PDFPixel — User Guide

> **Cross-platform install** (Linux `.deb` / Windows `.exe` / macOS `.dmg`) is in
> the [README](README.md). This guide goes deep on the **Linux/Nautilus** flow
> and the page-range behaviour, which is identical on every OS. Some Linux
> internals below (zenity, dependency list) describe the from-source `install.sh`
> path; the shipped `.deb` bundles its engine and a tkinter dialog instead.

PDFPixel turns any PDF into a folder of page images straight from your file
manager. Right-click a PDF in **Nautilus** (the GNOME Files app) → **Convert to
Images** → every page is written out as a PNG inside a new folder next to the
original. No app to open, no dialogs, no upload — it all runs locally on your
machine.

This guide covers everything: requirements, install, day-to-day use (both the
right-click menu and the command line), how the output is named, what happens
when things go wrong, and how to troubleshoot.

---

## Table of contents

1. [What it does](#1-what-it-does)
2. [Requirements](#2-requirements)
3. [Install](#3-install)
4. [Using it from Nautilus (the main way)](#4-using-it-from-nautilus-the-main-way)
5. [Using it from the command line](#5-using-it-from-the-command-line)
6. [Understanding the output](#6-understanding-the-output)
7. [Batches, mixed selections, and collisions](#7-batches-mixed-selections-and-collisions)
8. [When something fails](#8-when-something-fails)
9. [Notifications](#9-notifications)
10. [Uninstall](#10-uninstall)
11. [Troubleshooting](#11-troubleshooting)
12. [Scope and limitations](#12-scope-and-limitations)
13. [For developers](#13-for-developers)

---

## 1. What it does

- Adds a **"Convert to Images"** entry to the Nautilus right-click menu.
- The entry appears **only when your selection contains at least one PDF**
  (detected by file type, not just the `.pdf` extension).
- Clicking it renders **every page of every selected PDF** to a PNG image at
  **200 DPI**.
- For each PDF, the images go into a **new sibling folder** named after the PDF.
- It is **100% local** — nothing is uploaded anywhere.
- It runs **in the background**, so the Files window never freezes, even on a
  large PDF.

Example: right-click `invoice.pdf` → click **Convert to Images** → a folder
`invoice/` appears beside it containing `1.png`, `2.png`, `3.png` … one image
per page. A desktop notification confirms when it's done.

---

## 2. Requirements

PDFPixel is for **GNOME / Nautilus on Ubuntu or Debian** (and close relatives).

It depends on four system packages:

| Package | Provides | Why it's needed |
|---|---|---|
| `poppler-utils` | the `pdftoppm` command | does the actual PDF → PNG rendering |
| `libnotify-bin` | the `notify-send` command | shows the "done" desktop notification |
| `zenity` | the `zenity` dialog | the **Custom Range** page-range prompt |
| `python3-nautilus` | Nautilus Python bindings | lets the extension hook into the right-click menu |

> If `zenity` is missing, everything else still works — the menu just omits
> **Custom Range…** and offers all-pages conversion only.

You do **not** need to install these by hand — `install.sh` checks for them and
offers to install any that are missing (see below).

> **No sudo to run the tool.** It installs entirely into your user home
> (`~/.local`). `sudo` is only used once, and only if you let `install.sh`
> `apt install` missing system packages for you.

---

## 3. Install

From the project directory:

```bash
./install.sh
```

What the installer does, step by step:

1. **Checks dependencies.** Looks for `pdftoppm`, `notify-send`, `zenity`, and
   the `python3-nautilus` package. If any are missing it prints the exact
   `apt install` command and asks:

   ```
   Missing: poppler-utils libnotify-bin
   Install with:  sudo apt install poppler-utils libnotify-bin
   Run that now with sudo? [y/N]
   ```

   Answer `y` to let it run the install for you, or `N` to install them
   yourself and re-run `./install.sh` afterwards.

2. **Installs the helper** to `~/.local/bin/pdfpixel` (executable). This is the
   command-line program that does the conversion.

3. **Installs the extension** to
   `~/.local/share/nautilus-python/extensions/pdfpixel.py`. This is the thin
   piece that adds the right-click menu item. (This is the directory
   nautilus-python actually scans — the user-level mirror of the system
   `/usr/share/nautilus-python/extensions/`.)

4. **Reloads Nautilus** (`nautilus -q`) so the new menu item is picked up.

When it finishes you'll see:

```
Done. Right-click a PDF and choose 'Convert to Images'.
```

> **Tip:** if the menu item doesn't show up right away, fully close all Nautilus
> windows (or log out and back in) so Nautilus reloads its extensions. See
> [Troubleshooting](#11-troubleshooting).

---

## 4. Using it from Nautilus (the main way)

1. Open **Files** (Nautilus) and navigate to a PDF.
2. **Right-click** the PDF.
3. Choose **Convert to Images** from the menu.
4. Wait a moment. When it's done, a desktop notification appears, e.g.
   *"Converted 1 PDF — 3 pages total"*.
5. A new folder named after the PDF now sits next to it, full of PNGs.

That's the whole flow.

You can also **select several PDFs at once** (Ctrl-click or Shift-click), then
right-click and **Convert to Images** — each PDF gets its own output folder, and
you get a single summary notification at the end.

### Converting only some pages (single PDF)

When you right-click **one** PDF, **Convert to Images** opens a submenu:

- **All Pages** — convert every page (same as above).
- **Custom Range…** — a small prompt (showing the document's page count, e.g.
  *"Document has 12 pages"*) asks which pages. Enter:

  | You type | You get |
  |---|---|
  | `5-8` | pages 5, 6, 7, 8 |
  | `3` | page 3 only |
  | `5-` | page 5 to the end |
  | `-8` | the start through page 8 |
  | `1,3-5,9` | a comma-separated mix — pages 1, 3, 4, 5, 9 |

  Output files keep their **original page numbers** (`05.png`, `06.png`, …), so
  you always know which page is which. Cancel the prompt (or leave it blank) and
  nothing happens.

The submenu appears for a single PDF only. With **2+ PDFs selected**, the menu
is the single flat **Convert to Images** (all pages of each) — a custom range
can't sensibly mean the same thing across files of different lengths.

> If a range starts past the end of the document (e.g. `50-` on a 12-page PDF),
> that conversion fails gracefully — you get a notification and no empty folder.
> A range whose end overshoots (e.g. `5-100`) simply stops at the last page.

---

## 5. Using it from the command line

The same conversion engine is available as a standalone command, installed at
`~/.local/bin/pdfpixel`. If `~/.local/bin` is on your `PATH` (it usually is on
modern Ubuntu/Debian), you can run:

```bash
pdfpixel file1.pdf
pdfpixel report.pdf invoice.pdf scan.pdf      # batch — any number of files
pdfpixel --pages 5-8 report.pdf               # only pages 5–8
pdfpixel --pages 10- report.pdf               # page 10 to the end
pdfpixel --pages 1,3-5,9 report.pdf           # a comma-separated mix
```

`--pages` accepts the same forms as the dialog: single ranges (`N`, `N-M`,
`N-`, `-M`) and comma-separated mixes of them (`1,3-5,9`). Unlike the menu, on
the CLI it may be combined with multiple files — the same spec applies to each.

If `pdfpixel` isn't found, either add `~/.local/bin` to your `PATH` or call it
by full path:

```bash
~/.local/bin/pdfpixel file1.pdf
```

It prints a one-line summary and also sends the desktop notification:

```
$ pdfpixel report.pdf
Converted 1 PDF
```

### Exit codes

Useful if you're scripting around it:

| Exit code | Meaning |
|---|---|
| `0` | all files converted successfully |
| `1` | at least one file failed (the rest still converted) |
| `2` | no files given, or a malformed `--pages` value |

Example with no arguments:

```bash
$ pdfpixel
usage: pdfpixel [--pages RANGE] FILE.pdf [FILE2.pdf ...]
```

File paths are passed safely as arguments, so names with spaces or unicode work
without any quoting tricks beyond your normal shell quoting.

---

## 6. Understanding the output

For each PDF, PDFPixel creates a **sibling folder** (same directory as the PDF)
named after the PDF, minus the `.pdf` extension. Inside, there's **one PNG per
page**, named by page number.

```
~/Documents/
├── invoice.pdf
└── invoice/            ← created by PDFPixel
    ├── 1.png
    ├── 2.png
    └── 3.png
```

**Page-number padding.** File names are zero-padded to the width of the highest
page number, so they sort correctly in any file manager:

| PDF length | File names |
|---|---|
| up to 9 pages | `1.png`, `2.png`, … `9.png` |
| 10–99 pages | `01.png`, `02.png`, … `42.png` |
| 100+ pages | `001.png`, `002.png`, … `123.png` |

**Image format / quality.** Every image is a **PNG at 200 DPI** in v1. This is
fixed for now (configurable in a later release — see
[Scope and limitations](#12-scope-and-limitations)).

---

## 7. Batches, mixed selections, and collisions

**Batches.** Select multiple PDFs and convert them in one click. Each gets its
own folder; all conversions run in a single background pass (no CPU thrash from
spawning a process per file), and you get one summary notification at the end.

**Mixed selections.** If your selection contains non-PDF files (images, text,
folders…), those are **silently skipped**. Only the PDFs are converted. The
menu item itself only appears when there's at least one PDF in the selection.

**Folder-name collisions — your data is never overwritten.** If a folder with
the target name already exists, PDFPixel appends ` (n)`:

```
invoice/          ← already there from a previous run
invoice (1)/      ← this run
invoice (2)/      ← next run
```

So you can safely convert the same PDF repeatedly — each run lands in a fresh
folder and nothing existing is touched.

---

## 8. When something fails

A failure on one file **never aborts the rest of the batch.** Common cases:

- **Encrypted / password-protected PDF** — can't be rendered without the
  password, so it's reported as failed. No empty leftover folder is created.
- **Corrupt or unreadable PDF** — reported as failed with the underlying error.
- **Read-only directory** — if the folder holding the PDF isn't writable,
  PDFPixel can't create the output folder there, so that file is reported as a
  *"read-only directory"* failure.

In every case, the other files in the batch still convert, and the final
notification names what failed, e.g.:

```
Converted 2 PDFs · 1 failed
5 pages total
✗ secret.pdf: <reason>
```

---

## 9. Notifications

When conversion finishes, PDFPixel sends **one summary desktop notification**
via `notify-send`:

- Title: `Converted N PDFs` (plus `· M failed` if any failed).
- Body: total page count, followed by a line per failed file.

If `notify-send` isn't installed, PDFPixel **degrades silently** — the
conversion still happens, you just don't get the popup. (The command line also
prints the summary line either way.)

---

## 10. Uninstall

```bash
./uninstall.sh
```

This removes the helper (`~/.local/bin/pdfpixel`) and the extension
(`~/.local/share/nautilus-python/extensions/pdfpixel.py`), then reloads
Nautilus. It does **not** touch any image folders you've already created, and it
leaves the system packages (`poppler-utils` etc.) installed.

---

## 11. Troubleshooting

**The "Convert to Images" menu item doesn't appear.**

1. Make sure you re-launched Nautilus after installing. Close every Files
   window, then run `nautilus -q` in a terminal (or log out and back in).
2. Confirm `python3-nautilus` is installed:
   `dpkg -l python3-nautilus`.
3. Run Nautilus from a terminal in the foreground:

   ```bash
   nautilus -q     # quit any running instance first
   nautilus        # then start it here
   ```

   Python extension import errors are printed to this terminal — that output is
   the source of truth for why the extension failed to load. The most common
   cause is a Nautilus GI version mismatch, which the extension already tries to
   handle (it requests Nautilus 4.0 and falls back to 3.0).

**The menu item is there but nothing happens / no images appear.**

- Check the helper exists and is executable:
  `ls -l ~/.local/bin/pdfpixel`.
- Try running it directly on the same file to see the real error:
  `~/.local/bin/pdfpixel /path/to/your.pdf`.
- Make sure `pdftoppm` is installed: `command -v pdftoppm`.

**No notification appears, but the images are created.**

- `notify-send` is probably missing: install `libnotify-bin`. The conversion
  works regardless; only the popup is affected.

**`pdfpixel: command not found` on the command line.**

- `~/.local/bin` isn't on your `PATH`. Either add it, or call the helper by its
  full path: `~/.local/bin/pdfpixel`.

---

## 12. Scope and limitations

This is **v1**, intentionally minimal:

- **GNOME / Nautilus only.** Nemo, Caja, and Dolphin are not supported in v1.
- **PNG @ 200 DPI is fixed.** Output format and resolution aren't configurable
  yet.
- **Snap / Flatpak builds can't work** as a host file-manager extension — that's
  a hard sandbox limitation, not a choice. Distribution is via `install.sh` for
  now; a `.deb` + PPA may come later.

Planned for later releases: configurable format/DPI/prefix, JPEG/TIFF output, a
per-page progress bar, `.deb` packaging, and other file managers.

---

## 13. For developers

The codebase is two decoupled pieces against a frozen contract:

- **`src/pdfpixel.py`** — the conversion CLI. Pure Python, standard library only
  at runtime, fully unit-tested (including real `pdftoppm` runs against
  PDFs generated on the fly with `fpdf2`).
- **`src/pdfpixel_nautilus.py`** — a thin Nautilus `MenuProvider` that detects
  PDFs and `Popen`s the helper in the background. It loads under the system's
  `python3-nautilus`, not a virtualenv, so it's verified by manual click-testing
  (the Nautilus API can't be exercised under pytest).
- **`install.sh` / `uninstall.sh`** — place/remove both files at fixed
  user-level paths.

Run the test suite:

```bash
pip install -r requirements-dev.txt
pytest -v
```

The product spec and implementation plan live under
`docs/superpowers/plans/`.
