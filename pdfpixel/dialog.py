"""Cross-platform Custom… prompt via tkinter (bundled with the frozen
runtime). Returns an ``AskResult(spec, fmt, dpi)``; spec is "" if
cancelled/empty (the caller treats an empty spec as a no-op)."""
from __future__ import annotations

from collections import namedtuple

from pdfpixel import core

AskResult = namedtuple("AskResult", "spec fmt dpi")

_PROMPT = "Pages to convert (e.g. 1  ·  5-8  ·  -4  ·  1,3-5,9  ·  10-):"

# Format dropdown labels -> fmt string passed to core.convert_pdf
_FORMATS = [("PNG", "png"), ("JPG", "jpg"), ("WEBP", "webp"), ("TIFF", "tiff")]

# Resolution dropdown labels -> dpi int
_RESOLUTIONS = [
    ("Screen (96)", 96),
    ("Default (200)", 200),
    ("Print (300)", 300),
    ("High (600)", 600),
]


def ask_pages(pdf_path) -> AskResult:
    import tkinter as tk
    from tkinter import ttk

    n = core.page_count(pdf_path)
    state = {"spec": "", "fmt": "png", "dpi": core.DEFAULT_DPI}

    root = tk.Tk()
    root.title("PDFPixel")
    root.resizable(False, False)

    frm = tk.Frame(root, padx=16, pady=12)
    frm.pack()
    if n:
        tk.Label(frm, text=f"Document has {n} page{'' if n == 1 else 's'}").pack(
            anchor="w")

    fmt_labels = [label for label, _ in _FORMATS]
    res_labels = [label for label, _ in _RESOLUTIONS]
    fmt_var = tk.StringVar(value=fmt_labels[0])          # PNG
    res_var = tk.StringVar(value=res_labels[1])          # Default (200)

    tk.Label(frm, text="Format:").pack(anchor="w")
    fmt_box = ttk.Combobox(frm, textvariable=fmt_var, values=fmt_labels,
                           state="readonly", width=36)
    fmt_box.pack(fill="x", pady=(2, 8))

    tk.Label(frm, text="Resolution:").pack(anchor="w")
    res_box = ttk.Combobox(frm, textvariable=res_var, values=res_labels,
                           state="readonly", width=36)
    res_box.pack(fill="x", pady=(2, 8))

    tk.Label(frm, text=_PROMPT).pack(anchor="w")

    entry = tk.Entry(frm, width=38)
    entry.pack(fill="x", pady=(4, 10))
    entry.focus_set()

    def convert(*_):
        state["spec"] = entry.get()
        state["fmt"] = dict(_FORMATS)[fmt_var.get()]
        state["dpi"] = dict(_RESOLUTIONS)[res_var.get()]
        root.destroy()

    def cancel(*_):
        state["spec"] = ""
        state["fmt"] = "png"
        state["dpi"] = core.DEFAULT_DPI
        root.destroy()

    btns = tk.Frame(frm)
    btns.pack(anchor="e")
    tk.Button(btns, text="Cancel", command=cancel).pack(side="left", padx=4)
    tk.Button(btns, text="Convert", command=convert, default="active").pack(side="left")

    entry.bind("<Return>", convert)
    root.bind("<Escape>", cancel)

    root.mainloop()
    return AskResult(state["spec"].strip(), state["fmt"], state["dpi"])
