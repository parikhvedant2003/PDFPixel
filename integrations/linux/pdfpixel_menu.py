"""Single source of truth for the branded PDFPixel right-click menu.

Pure stdlib — NO third-party imports (no gi, no pdfpixel). This module runs
under the *system* Python via python3-nautilus/nemo/caja, not the frozen
binary, so it must stay importable everywhere. The three file-manager shims
import it as a sibling; packaging/linux/gen_servicemenus.py imports ACTIONS to
emit the KDE/Thunar launchers. Change the menu here and it propagates to all 5
Linux launch points.
"""
import os
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    id: str            # stable id, e.g. "all"
    label: str         # submenu entry text
    args: list         # CLI argv template; "{f}" = single path, "{ff}" = many paths
    arity: str         # "single" (exactly 1 PDF) | "multi" (1+ PDFs)


PARENT_LABEL = "PDFPixel"           # branded top-level submenu label
PARENT_TIP = "PDF tools by PDFPixel"

ACTIONS = [
    Action("all",      "All Pages → PNG",     ["{ff}"],                 "multi"),
    Action("first",    "First Page → PNG",    ["--pages", "1", "{f}"],  "single"),
    Action("custom",   "Custom…",             ["--ask", "{f}"],         "single"),
    Action("merge",    "Merge selected PDFs", ["merge", "{ff}"],        "multi"),
    Action("split",    "Split into pages",    ["split", "{f}"],         "single"),
    Action("compress", "Compress",            ["compress", "{f}"],      "single"),
]


def helper_path():
    # .deb installs /usr/bin/pdfpixel; dev/pip install lands in ~/.local/bin.
    for p in ("/usr/bin/pdfpixel", os.path.expanduser("~/.local/bin/pdfpixel")):
        if os.path.exists(p):
            return p
    return shutil.which("pdfpixel") or os.path.expanduser("~/.local/bin/pdfpixel")


def is_pdf(uri_scheme, mime):
    # Only local files we can actually read; remote/trash URIs are skipped.
    return uri_scheme == "file" and mime == "application/pdf"


def build_argv(action, paths):
    """Expand an Action's args template into a real argv (sans helper binary).

    "{f}"  -> the single first path (paths[0]).
    "{ff}" -> spread to all selected paths, in place.
    """
    argv = []
    for tok in action.args:
        if tok == "{ff}":
            argv.extend(paths)
        elif tok == "{f}":
            argv.append(paths[0])
        else:
            argv.append(tok)
    return argv
