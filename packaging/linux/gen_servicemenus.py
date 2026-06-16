#!/usr/bin/env python3
"""Generate the declarative right-click launchers from the shared menu source.

Single source of truth is integrations/linux/pdfpixel_menu.py (ACTIONS). This
script imports that list and emits the two *declarative* launch points so they
never drift from the python3-* shims:

  - integrations/linux/pdfpixel.desktop  — KDE Dolphin ServiceMenu (committed).
  - the XML block inside integrations/linux/thunar-actions.md — Thunar uca.xml.

Pure stdlib, no third-party imports. Run from the repo root:

    python packaging/linux/gen_servicemenus.py

It is idempotent: regenerating without an ACTIONS change rewrites identical
bytes.
"""
import os
import sys

HELPER = "/usr/bin/pdfpixel"   # the .deb / system install path the launchers call
ICON = "application-pdf"

# repo_root/packaging/linux/gen_servicemenus.py -> repo_root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INTEGRATIONS = os.path.join(REPO_ROOT, "integrations", "linux")
DESKTOP_PATH = os.path.join(INTEGRATIONS, "pdfpixel.desktop")
THUNAR_PATH = os.path.join(INTEGRATIONS, "thunar-actions.md")

# pdfpixel_menu.py is a pure-stdlib sibling of the shims; import it directly.
sys.path.insert(0, INTEGRATIONS)
import pdfpixel_menu as M  # noqa: E402

# Thunar/KDE field codes per arity: %f = one file, %F = many files.
FIELD_CODE = {"single": "%f", "multi": "%F"}


def _exec_args(action):
    """Expand an action's argv template to a KDE/Thunar Exec string."""
    code = FIELD_CODE["single" if "{f}" in action.args else "multi"]
    parts = [code if tok in ("{f}", "{ff}") else tok for tok in action.args]
    return " ".join(parts)


def render_desktop():
    actions = ";".join(f"PdfPixel{a.id.capitalize()}" for a in M.ACTIONS) + ";"
    lines = [
        "[Desktop Entry]",
        "Type=Service",
        "ServiceTypes=KonqPopupMenu/Plugin",
        "MimeType=application/pdf;",
        f"Actions={actions}",
        f'X-KDE-Submenu={M.PARENT_LABEL}',
        "X-KDE-Priority=TopLevel",
    ]
    for a in M.ACTIONS:
        lines += [
            "",
            f"[Desktop Action PdfPixel{a.id.capitalize()}]",
            f"Name={a.label}",
            f"Icon={ICON}",
            f"Exec={HELPER} {_exec_args(a)}",
        ]
    return "\n".join(lines) + "\n"


def render_thunar_xml():
    blocks = []
    for a in M.ACTIONS:
        blocks.append(
            "<action>\n"
            f"  <icon>{ICON}</icon>\n"
            f"  <name>{M.PARENT_LABEL}: {a.label}</name>\n"
            f"  <command>{HELPER} {_exec_args(a)}</command>\n"
            f"  <description>{M.PARENT_TIP} — {a.label}</description>\n"
            "  <patterns>*.pdf</patterns>\n"
            "  <other-files/>\n"
            "</action>"
        )
    return "\n".join(blocks)


def _splice_code_block(md, new_xml):
    """Replace the first ```xml ... ``` fenced block, keeping surrounding prose."""
    open_fence = "```xml"
    start = md.index(open_fence)
    body_start = md.index("\n", start) + 1
    end = md.index("```", body_start)
    return md[:body_start] + new_xml + "\n" + md[end:]


def main():
    with open(DESKTOP_PATH, "w", encoding="utf-8") as fh:
        fh.write(render_desktop())
    print(f"wrote {os.path.relpath(DESKTOP_PATH, REPO_ROOT)}")

    with open(THUNAR_PATH, "r", encoding="utf-8") as fh:
        md = fh.read()
    md = _splice_code_block(md, render_thunar_xml())
    with open(THUNAR_PATH, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"wrote {os.path.relpath(THUNAR_PATH, REPO_ROOT)}")


if __name__ == "__main__":
    main()
