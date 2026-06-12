import os
import subprocess

import gi
try:
    gi.require_version("Nautilus", "4.0")
except ValueError:
    gi.require_version("Nautilus", "3.0")
from gi.repository import GObject, Nautilus  # noqa: E402

HELPER = os.path.expanduser("~/.local/bin/pdfpixel")


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
        item = Nautilus.MenuItem(
            name="PdfPixel::convert",
            label="Convert to Images",
            tip="Render each PDF page to a PNG image",
        )
        item.connect("activate", self._activate, pdfs)
        return [item]

    def _activate(self, menu, files):
        paths = [f.get_location().get_path() for f in files]
        subprocess.Popen([HELPER, *paths])
