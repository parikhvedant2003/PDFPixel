# Contributing to PDFPixel

How to set up, test, build, and ship changes. For the design and module map read
[ARCHITECTURE.md](ARCHITECTURE.md) first.

## Dev setup

Requires Python 3.8+.

```bash
git clone https://github.com/parikhvedant2003/PDFPixel
cd PDFPixel
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"        # editable install + pytest, fpdf2, pyinstaller
```

Runtime deps (`pypdfium2`, `pillow`, `pikepdf`) install automatically. On Linux,
the file-manager shims additionally need the system bindings to *run* in a real
file manager — install whichever you use: `python3-nautilus` / `python3-nemo` /
`python3-caja`. Those bindings live in the **system** Python, so the shims are
exercised by manual click-testing, not pytest (see "Testing").

## Run the tests

```bash
pytest -q                      # whole suite
pytest tests/test_core_format.py -q       # one file
pytest -k compress -q          # by keyword
```

Tests build sample PDFs on the fly with `fpdf2`/`pikepdf` (`tests/conftest.py`),
so no fixtures live on disk. Everything in `pdfpixel/` is expected to stay green;
add tests with any behaviour change.

## Try it locally

```bash
python -m pdfpixel --version
python -m pdfpixel some.pdf                 # convert all pages
python -m pdfpixel --format jpg --dpi 96 some.pdf
python -m pdfpixel merge a.pdf b.pdf
python -m pdfpixel split a.pdf
python -m pdfpixel compress --quality medium a.pdf
```

To exercise the **right-click menu** on Linux from a checkout, `./install.sh`
copies the Nautilus shim *and* `pdfpixel_menu.py` into
`~/.local/share/nautilus-python/extensions/`, installs the CLI, and reloads
Nautilus. Re-run it after changing the shim or the menu spec; if the menu doesn't
appear, fully quit the file manager (`nautilus -q`) and reopen.

## Where to make changes

| Change | File(s) | Don't forget |
|---|---|---|
| New image format / DPI behaviour | `pdfpixel/core.py` | test in `tests/test_core_format.py` |
| New PDF operation | `pdfpixel/pdfops.py` + `cli.py` | safety: never overwrite the source |
| New CLI flag / verb | `pdfpixel/cli.py` | keep the default-verb back-compat |
| New right-click menu item | `integrations/linux/pdfpixel_menu.py` (`ACTIONS`) | run `python packaging/linux/gen_servicemenus.py` |
| The Custom… dialog | `pdfpixel/dialog.py` | return an `AskResult` |
| Packaging / a new channel | `packaging/…` + `DISTRIBUTING.md` | — |

After editing `ACTIONS`, regenerate the declarative launchers:

```bash
python packaging/linux/gen_servicemenus.py     # rewrites pdfpixel.desktop + thunar-actions.md
```

## Building artifacts

Linux artifacts are built **inside a glibc-2.31 container** so they run on older
distros — needs Docker:

```bash
bash packaging/linux/build_in_container.sh debian:11   # → build/dist/*.deb, *.rpm, *.AppImage
```

Windows (`packaging/windows/build_exe.ps1`, Inno Setup) and macOS
(`packaging/macos/build_dmg.sh`) build on their own OS. CI does all of this on
tag; you rarely need to build by hand. Channel-by-channel publishing
(Releases / PyPI / AUR / Flatpak) is documented in
[packaging/linux/DISTRIBUTING.md](packaging/linux/DISTRIBUTING.md).

## Commit & branch conventions

- Branch off `master` for any change; don't commit feature work directly to it.
- **Conventional Commits** for messages: `feat:`, `fix:`, `docs:`, `build:`,
  `ci:`, `refactor:`, `test:`. Subject in the imperative, ≤ ~72 chars; body
  explains *why* when it isn't obvious.
- Keep commits focused; run `pytest -q` before pushing.

## Releasing

The version is single-sourced — bump it in **one** place:

1. Edit `__version__` in `pdfpixel/__init__.py` (pyproject reads it dynamically).
2. Commit (`build: bump to X.Y.Z`), then tag: `git tag vX.Y.Z && git push --tags`.
3. CI runs the test matrix, builds every artifact (amd64 + arm64), publishes a
   GitHub Release, and (once the PyPI publisher is configured) uploads to PyPI.

PyPI uses Trusted Publishing — no token secret; the one-time setup is in
`DISTRIBUTING.md`. Never reuse a version number: PyPI rejects re-uploads.
