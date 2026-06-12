"""Nautilus shim — dumb Popen of the pdfpixel CLI. All UI (range dialog,
notification) lives in the CLI process, so this never blocks Nautilus."""
import os
import shutil
import subprocess

import gi
try:
    gi.require_version("Nautilus", "4.0")
except ValueError:
    gi.require_version("Nautilus", "3.0")
from gi.repository import GObject, Nautilus  # noqa: E402


def _helper():
    # .deb installs /usr/bin/pdfpixel; dev/pip install lands in ~/.local/bin.
    for p in ("/usr/bin/pdfpixel", os.path.expanduser("~/.local/bin/pdfpixel")):
        if os.path.exists(p):
            return p
    return shutil.which("pdfpixel") or os.path.expanduser("~/.local/bin/pdfpixel")


class PdfPixelExtension(GObject.GObject, Nautilus.MenuProvider):
    def _pdfs(self, files):
        out = []
        for f in files:
            if f.get_uri_scheme() != "file":
                continue
            if f.get_mime_type() == "application/pdf":
                out.append(f)
        return out

    def get_file_items(self, *args):
        # Nautilus 4.0 passes (files,); older nautilus-python passes (window, files).
        files = args[-1]
        pdfs = self._pdfs(files)
        if not pdfs:
            return []

        top = Nautilus.MenuItem(
            name="PdfPixel::convert",
            label="Convert to Images",
            tip="Render PDF pages to PNG images",
        )

        if len(pdfs) == 1:
            submenu = Nautilus.Menu()
            all_item = Nautilus.MenuItem(
                name="PdfPixel::all", label="All Pages", tip="Convert every page")
            all_item.connect("activate", self._activate_all, pdfs)
            submenu.append_item(all_item)
            range_item = Nautilus.MenuItem(
                name="PdfPixel::range", label="Custom Range…",
                tip="Convert a page range you choose")
            range_item.connect("activate", self._activate_range, pdfs[0])
            submenu.append_item(range_item)
            top.set_submenu(submenu)
        else:
            top.connect("activate", self._activate_all, pdfs)

        return [top]

    def _activate_all(self, menu, files):
        paths = [f.get_location().get_path() for f in files]
        subprocess.Popen([_helper(), *paths])

    def _activate_range(self, menu, pdf):
        path = pdf.get_location().get_path()
        subprocess.Popen([_helper(), "--ask", path])
