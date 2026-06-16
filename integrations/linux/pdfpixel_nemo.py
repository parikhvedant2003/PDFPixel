"""Nemo shim — thin adapter over pdfpixel_menu (the shared menu source).
All UI (range dialog, notification) lives in the CLI process, so this never
blocks Nemo."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # find sibling
import pdfpixel_menu as M  # noqa: E402

import gi  # noqa: E402
try:
    gi.require_version("Nemo", "3.0")
except ValueError:
    gi.require_version("Nemo", "3.0")
from gi.repository import GObject, Nemo  # noqa: E402


class PdfPixelExtension(GObject.GObject, Nemo.MenuProvider):
    def get_file_items(self, *args):
        # Nemo 4.0 passes (files,); older nautilus-python passes (window, files).
        files = args[-1]
        pdfs = [f for f in files
                if M.is_pdf(f.get_uri_scheme(), f.get_mime_type())]
        if not pdfs:
            return []

        parent = Nemo.MenuItem(
            name="PdfPixel::parent", label=M.PARENT_LABEL, tip=M.PARENT_TIP)
        submenu = Nemo.Menu()
        for a in M.ACTIONS:
            # "single" actions only make sense for exactly one PDF.
            if a.arity == "single" and len(pdfs) != 1:
                continue
            item = Nemo.MenuItem(name=f"PdfPixel::{a.id}", label=a.label)
            item.connect("activate", self._run, a, pdfs)
            submenu.append_item(item)
        parent.set_submenu(submenu)
        return [parent]

    def _run(self, menu, action, pdfs):
        paths = [f.get_location().get_path() for f in pdfs]
        subprocess.Popen([M.helper_path(), *M.build_argv(action, paths)])
