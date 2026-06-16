# PDFPixel — Architecture

Onboarding for developers. What the pieces are, how a click becomes images, and
where to change things. For day-to-day *usage* see [USAGE.md](USAGE.md); for dev
setup and conventions see [CONTRIBUTING.md](CONTRIBUTING.md).

## The one-sentence model

A file-manager right-click runs a **thin shim** that does nothing but
`Popen` the **`pdfpixel` CLI** in the background; the CLI holds *all* the real
logic (rendering, PDF ops, the dialog, notifications). The shim never blocks the
file manager, and the same CLI is what you run in a terminal.

```
right-click ─▶ FM shim (system python) ─▶  pdfpixel CLI (frozen binary)
 (Nautilus/…)   builds menu from a            │
                shared ACTIONS list           ├─ core.py    render pages → images
                                              ├─ pdfops.py  merge / split / compress
                                              ├─ dialog.py  tkinter "Custom…" prompt
                                              └─ notify.py  desktop notification
```

Two processes, one contract: the shim knows only *which argv* to launch; the CLI
owns behaviour. This keeps the GTK/Qt-bound shim trivial and the logic fully
unit-testable in plain Python.

## Repository layout

```
pdfpixel/                 the Python package (the engine + CLI)
  __init__.py             __version__  ← single source of truth for the version
  __main__.py             enables `python -m pdfpixel`
  cli.py                  arg parsing + verb routing (the entry point)
  core.py                 render engine: PDF pages → PNG/JPG/WEBP/TIFF
  pdfops.py               merge / split / compress (pikepdf)
  dialog.py               tkinter "Custom…" dialog (format + DPI + range)
  notify.py               per-OS desktop notification

integrations/             file-manager bindings (NOT shipped in the wheel)
  linux/
    pdfpixel_menu.py      ★ ACTIONS — the single menu source of truth
    pdfpixel_nautilus.py  thin GNOME Files shim   ┐ ~identical adapters;
    pdfpixel_nemo.py      thin Cinnamon shim      │ only the GI module differs
    pdfpixel_caja.py      thin MATE shim          ┘
    pdfpixel.desktop      KDE Dolphin ServiceMenu (generated)
    thunar-actions.md     XFCE Thunar uca snippet (generated; manual install)
  windows/pdfpixel.reg.tmpl   registry cascade on .pdf
  macos/*.workflow            Finder Quick Actions

packaging/                how each artifact is built
  entry.py                PyInstaller entry point (shared by all OSes)
  linux/build_linux.sh    PyInstaller → .deb + .rpm + AppImage (in a glibc-2.31 container)
  linux/gen_servicemenus.py   regenerate the KDE/Thunar files from ACTIONS
  windows/build_exe.ps1 + pdfpixel.iss   Inno Setup installer
  macos/build_dmg.sh      .dmg with the Quick Actions
  DISTRIBUTING.md         every channel (Releases/PyPI/AUR/Flatpak) + publish steps

tests/                    pytest suite (conftest.py builds sample PDFs with fpdf2)
```

## The package (`pdfpixel/`)

### `core.py` — render engine
Pure conversion/naming/range logic, no GUI or notification code, so it is
identical and unit-tested across OSes. Key surface:

- `convert_pdf(pdf_path, segments=None, fmt="png", dpi=DEFAULT_DPI) -> FileResult`
  renders pages to a **sibling folder** named after the PDF, files
  `f"{n:0{width}d}.{ext}"`. `DEFAULT_DPI = 200`; scale = `dpi/72`. `jpg`/`jpeg`
  flatten RGBA→RGB; png/webp/tiff keep alpha. Unknown `fmt` → failed result.
- `parse_pages(spec)` → list of `(first, last)` segments (`5-8`, `3`, `5-`,
  `-8`, `1,3-5,9`). `_expand` clamps to `[1, total]` and drops out-of-range pages.
- `FileResult(path, ok, pages=0, error=None)` — the shared result contract,
  reused by `pdfops`.
- `unique_output_dir` / `build_summary` — non-clobbering output dir; one-line
  summary + per-failure detail.

### `pdfops.py` — PDF operations (pikepdf)
- `merge(inputs, out=None)` — concatenate; `out` defaults to a non-clobbering
  `merged.pdf` beside the first input.
- `split(pdf_path)` — one `{stem}_p{n}.pdf` per page beside the source.
- `compress(pdf_path, quality="medium")` — **real image compression**: walks
  image XObjects (`_iter_image_xobjects`, recursing into Form XObjects),
  re-encodes *safe* images (RGB/grayscale, 8-bit, no transparency mask) to
  downscaled JPEG per `QUALITY_PRESETS`, then a qpdf structural pass. Skips
  masked/alpha/CMYK/indexed/stencil images and text/vectors → no corruption,
  selectable text preserved. Only replaces an image if the result is smaller.
- **Invariant:** ops never overwrite the source; they write new sibling files.

### `cli.py` — entry point & verb router
The single program every shim and the terminal invoke.

- **Default verb = convert.** If `argv[0]` is not one of `merge/split/compress`
  (and not `--version`), the whole argv goes to the convert path — so historical
  calls (`pdfpixel x.pdf`, `--pages`, `--ask`) still work.
- Convert flags: `--pages`, `--ask`, `--format {png,jpg,webp,tiff}`, `--dpi`.
- `merge` / `split` / `compress` subcommands; `compress` adds `--quality`.
- `main(argv, ask=None, notifier=None)` — the **injection seam**: tests pass a
  fake `ask`/`notifier`. `ask` may return an `AskResult` (its fmt/dpi override
  the flags) or a plain string spec.
- Exit codes: `0` ok · `1` ≥1 failure · `2` usage / bad `--pages`.

### `dialog.py` / `notify.py`
`ask_pages(pdf_path) -> AskResult(spec, fmt, dpi)` — tkinter window with Format
and Resolution dropdowns above the range field; cancel/empty →
`AskResult("", "png", 200)`. tkinter is imported lazily so importing the module
is headless-safe. `notify.py` sends one summary notification per OS and degrades
silently if the notifier is absent.

## The menu: one source, five launch points

`integrations/linux/pdfpixel_menu.py` is the **single source of truth**:

```python
@dataclass(frozen=True)
class Action: id; label; args; arity   # arity: "single" (1 PDF) | "multi" (1+ PDFs)
ACTIONS = [all, first, custom, merge, split, compress]   # see the file
PARENT_LABEL = "PDFPixel"
helper_path(); is_pdf(scheme, mime); build_argv(action, paths)
```

- The 3 **GTK shims** (`pdfpixel_nautilus/nemo/caja.py`) are ~30-line adapters:
  `sys.path.insert(0, dirname(__file__))` → `import pdfpixel_menu` → loop
  `ACTIONS`, skip `arity=="single"` when >1 PDF is selected, and on activate
  `Popen([helper_path(), *build_argv(action, paths)])`. Only the GI module name
  (`Nautilus`/`Nemo`/`Caja`) differs. They run under the **system** Python
  (`python3-nautilus`), *not* the frozen binary — hence the sibling-import dance
  and why `pdfpixel_menu.py` is installed next to each shim.
- **KDE Dolphin** (`.desktop`) and **Thunar** (`uca.xml`) are declarative and
  can't import Python, so `packaging/linux/gen_servicemenus.py` *generates* them
  from `ACTIONS`. Run it after editing `ACTIONS`.

**To add or change a menu action:** edit `ACTIONS` once, run
`python packaging/linux/gen_servicemenus.py`, done — GTK shims pick it up at
runtime, KDE/Thunar are regenerated. (Add the matching CLI behaviour in
`cli.py`/`core.py`/`pdfops.py` if it's a new verb.)

### Cross-OS reality
- **Linux** — 5 file managers, full action set, all from `ACTIONS`.
- **Windows** — registry cascade (`pdfpixel.reg.tmpl`, installed by Inno Setup).
- **macOS** — Finder Quick Actions (`.workflow` bundles in `~/Library/Services`).
- Windows/macOS menus currently expose only **All Pages** + **Custom Range**;
  the newer verbs (merge/split/compress, formats) are available there via the
  **CLI** but not yet wired into their native menus (parity is pending). The
  Linux menu and the CLI are the complete surface today.

## Build & distribution (short version)
Linux artifacts are built by PyInstaller **inside a Debian 11 (glibc 2.31)
container** so the frozen binary runs on Ubuntu 20.04+/RHEL 8+/etc., producing
`.deb` + `.rpm` + AppImage for amd64 **and** arm64 (CI matrix). Windows uses Inno
Setup, macOS a `.dmg`. The version is single-sourced from
`pdfpixel/__init__.py:__version__` (pyproject reads it dynamically). Full channel
matrix and publish steps live in
[packaging/linux/DISTRIBUTING.md](packaging/linux/DISTRIBUTING.md).

## Testing model
`core` and `pdfops` are exercised directly against PDFs built on the fly with
`fpdf2`/`pikepdf` (see `tests/conftest.py`). `cli` is tested through its
injection seam with fake `ask`/`notifier`. The **shims are not unit-tested** —
the file-manager GI API can't run under pytest — so they're kept trivial and
verified by manual click-testing. Run `pytest -q`.
