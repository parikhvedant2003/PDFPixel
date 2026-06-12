"""pdfpixel CLI — the single entry point every OS's context-menu shim invokes.

  pdfpixel FILE [FILE...]            all pages
  pdfpixel --pages SPEC FILE [...]   page range(s), same SPEC applied to each
  pdfpixel --ask FILE                prompt for a range (single file), then convert
  pdfpixel --version
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdfpixel import __version__, core
from pdfpixel.notify import notify as _notify


def _default_ask(path):
    from pdfpixel.dialog import ask_pages
    return ask_pages(path)


def main(argv, ask=None, notifier=None) -> int:
    ask = ask or _default_ask
    notifier = notifier or _notify

    parser = argparse.ArgumentParser(prog="pdfpixel")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--pages", help="page range, e.g. 5-8 or 1,3-5,9")
    parser.add_argument("--ask", action="store_true",
                        help="prompt for a page range (single file)")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    if args.version:
        print(f"pdfpixel {__version__}")
        return 0

    if args.ask:
        if len(args.files) != 1:
            print("usage: pdfpixel --ask FILE.pdf", file=sys.stderr)
            return 2
        spec = ask(args.files[0])
        if not spec.strip():
            return 0  # cancelled / empty -> no-op
        try:
            segments = core.parse_pages(spec)
        except ValueError:
            notifier(f"Invalid page range: {spec}", "")
            return 2
        results = [core.convert_pdf(Path(args.files[0]), segments)]
    else:
        if not args.files:
            print("usage: pdfpixel [--pages RANGE] FILE.pdf [FILE2.pdf ...]",
                  file=sys.stderr)
            return 2
        segments = None
        if args.pages is not None:
            try:
                segments = core.parse_pages(args.pages)
            except ValueError:
                notifier(f"Invalid page range: {args.pages}", "")
                return 2
        results = [core.convert_pdf(Path(p), segments) for p in args.files]

    summary, body = core.build_summary(results)
    notifier(summary, body)
    print(summary)
    return 0 if all(r.ok for r in results) else 1


def run():  # console-script / frozen entry point
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
