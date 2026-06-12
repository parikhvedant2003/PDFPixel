import os
import shutil
import subprocess
import threading

import gi
_NAUT_VER = "4.0"
try:
    gi.require_version("Nautilus", "4.0")
except ValueError:
    gi.require_version("Nautilus", "3.0")
    _NAUT_VER = "3.0"
from gi.repository import GObject, Nautilus  # noqa: E402

# Prefer an in-process GTK3 dialog (instant: Nautilus 42 already has GTK3
# loaded, so there's no ~130-lib zenity process to cold-start). Only safe
# alongside the GTK3 Nautilus 3.0 API; under GTK4 we fall back to zenity.
HAVE_GTK3 = False
if _NAUT_VER == "3.0":
    try:
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk  # noqa: E402
        HAVE_GTK3 = hasattr(Gtk.Dialog, "run")
    except (ValueError, ImportError):
        HAVE_GTK3 = False

HELPER = os.path.expanduser("~/.local/bin/pdfpixel")
_PROMPT = "Pages to convert (e.g. 1  ·  5-8  ·  -4  ·  1,3-5,9  ·  10-):"


def _page_count(path):
    """Page count via pdfinfo, or None if it can't be determined (encrypted,
    corrupt, pdfinfo missing) -- callers just omit the count line then."""
    try:
        proc = subprocess.run(["pdfinfo", path], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def _count_label(n):
    return f"Document has {n} page{'' if n == 1 else 's'}"


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

        # Single PDF + a way to prompt -> submenu offering a page range.
        if len(pdfs) == 1 and (HAVE_GTK3 or shutil.which("zenity")):
            submenu = Nautilus.Menu()

            all_item = Nautilus.MenuItem(
                name="PdfPixel::all",
                label="All Pages",
                tip="Convert every page",
            )
            all_item.connect("activate", self._activate_all, pdfs)
            submenu.append_item(all_item)

            range_item = Nautilus.MenuItem(
                name="PdfPixel::range",
                label="Custom Range…",
                tip="Convert a page range you choose",
            )
            range_item.connect("activate", self._activate_range, pdfs[0])
            submenu.append_item(range_item)

            top.set_submenu(submenu)
        else:
            # Multiple PDFs, or no prompt available -> one flat all-pages action.
            top.connect("activate", self._activate_all, pdfs)

        return [top]

    def _activate_all(self, menu, files):
        paths = [f.get_location().get_path() for f in files]
        subprocess.Popen([HELPER, *paths])

    def _activate_range(self, menu, pdf):
        path = pdf.get_location().get_path()
        if HAVE_GTK3:
            # In-process dialog on the GTK main thread. Gtk.Dialog.run() spins a
            # nested main loop, so Nautilus stays responsive (no freeze) and the
            # dialog appears instantly (no external process to launch).
            spec = self._ask_pages_gtk(path)
            if spec:
                subprocess.Popen([HELPER, "--pages", spec, path])
            return
        # Fallback (GTK4 / no Gtk3): zenity off the main thread, since a blocking
        # subprocess on the main thread would freeze Nautilus.
        threading.Thread(
            target=self._zenity_and_convert, args=(path,), daemon=True
        ).start()

    def _ask_pages_gtk(self, path):
        dialog = Gtk.Dialog(title="PDFPixel")
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Convert", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box = dialog.get_content_area()
        box.set_spacing(8)
        box.set_border_width(10)
        n = _page_count(path)
        if n:
            box.add(Gtk.Label(label=_count_label(n)))
        box.add(Gtk.Label(label=_PROMPT))
        entry = Gtk.Entry()
        entry.set_activates_default(True)  # Enter triggers Convert
        box.add(entry)
        dialog.show_all()

        response = dialog.run()
        spec = entry.get_text().strip() if response == Gtk.ResponseType.OK else ""
        dialog.destroy()
        return spec

    def _zenity_and_convert(self, path):
        n = _page_count(path)
        text = f"{_count_label(n)}\n{_PROMPT}" if n else _PROMPT
        try:
            proc = subprocess.run(
                ["zenity", "--entry", "--title=PDFPixel", "--text=" + text],
                capture_output=True, text=True,
            )
        except FileNotFoundError:
            return  # zenity vanished between menu build and click
        if proc.returncode != 0:
            return  # cancelled / Esc
        spec = proc.stdout.strip()
        if not spec:
            return  # empty entry -> no-op
        subprocess.Popen([HELPER, "--pages", spec, path])
