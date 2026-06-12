"""Cross-platform page-range prompt via tkinter (bundled with the frozen
runtime). Returns the entered spec string, or "" if cancelled/empty."""
from __future__ import annotations

from pdfpixel import core

_PROMPT = "Pages to convert (e.g. 1  ·  5-8  ·  -4  ·  1,3-5,9  ·  10-):"


def ask_pages(pdf_path) -> str:
    import tkinter as tk

    n = core.page_count(pdf_path)
    state = {"spec": ""}

    root = tk.Tk()
    root.title("PDFPixel")
    root.resizable(False, False)

    frm = tk.Frame(root, padx=16, pady=12)
    frm.pack()
    if n:
        tk.Label(frm, text=f"Document has {n} page{'' if n == 1 else 's'}").pack(
            anchor="w")
    tk.Label(frm, text=_PROMPT).pack(anchor="w")

    entry = tk.Entry(frm, width=38)
    entry.pack(fill="x", pady=(4, 10))
    entry.focus_set()

    def convert(*_):
        state["spec"] = entry.get()
        root.destroy()

    def cancel(*_):
        state["spec"] = ""
        root.destroy()

    btns = tk.Frame(frm)
    btns.pack(anchor="e")
    tk.Button(btns, text="Cancel", command=cancel).pack(side="left", padx=4)
    tk.Button(btns, text="Convert", command=convert, default="active").pack(side="left")

    entry.bind("<Return>", convert)
    root.bind("<Escape>", cancel)

    root.mainloop()
    return state["spec"].strip()
