"""pdfpixel CLI — the single entry point every OS's context-menu shim invokes.

  pdfpixel FILE [FILE...]                 convert all pages (default verb)
  pdfpixel [--pages SPEC] [--ask] \
           [--format {png,jpg,webp,tiff}] [--dpi N] FILE [...]
  pdfpixel merge    FILE.pdf FILE2.pdf...   concatenate into one PDF
  pdfpixel split    FILE.pdf                one single-page PDF per page
  pdfpixel compress FILE.pdf                qpdf-optimized copy
  pdfpixel --version

The default verb is ``convert``: unless the first token is one of
{merge, split, compress}, the whole argv is routed to the convert path, so
every historical invocation (bare file, ``--pages``, ``--ask``) still works.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdfpixel import __version__, core, pdfops
from pdfpixel.dialog import AskResult
from pdfpixel.notify import notify as _notify

_OPS = ("merge", "split", "compress")
_FORMATS = ("png", "jpg", "webp", "tiff")


def _default_ask(path) -> AskResult:
    from pdfpixel.dialog import ask_pages
    return ask_pages(path)


# --- convert (default verb) ----------------------------------------------

def _build_convert_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pdfpixel")
    parser.add_argument("--pages", help="page range, e.g. 5-8 or 1,3-5,9")
    parser.add_argument("--ask", action="store_true",
                        help="prompt for a page range (single file)")
    parser.add_argument("--format", choices=_FORMATS, default="png",
                        help="output image format (default: png)")
    parser.add_argument("--dpi", type=int, default=core.DEFAULT_DPI,
                        help=f"render resolution (default: {core.DEFAULT_DPI})")
    parser.add_argument("files", nargs="*")
    return parser


def _normalize_ask(result, fmt: str, dpi: int):
    """Coerce whatever ``ask`` returned into ``(spec, fmt, dpi)``.

    Accepts an ``AskResult`` (whose fmt/dpi OVERRIDE the CLI ones) or a plain
    string spec (which keeps the CLI's fmt/dpi). This keeps the injected-ask
    seam working for both shapes.
    """
    if isinstance(result, str):
        return result, fmt, dpi
    spec = getattr(result, "spec", "")
    return spec, getattr(result, "fmt", fmt), getattr(result, "dpi", dpi)


def _convert(argv, ask, notifier) -> int:
    args = _build_convert_parser().parse_args(argv)
    fmt, dpi = args.format, args.dpi

    if args.ask:
        if len(args.files) != 1:
            print("usage: pdfpixel --ask FILE.pdf", file=sys.stderr)
            return 2
        spec, fmt, dpi = _normalize_ask(ask(args.files[0]), fmt, dpi)
        if not spec.strip():
            return 0  # cancelled / empty -> no-op
        try:
            segments = core.parse_pages(spec)
        except ValueError:
            notifier(f"Invalid page range: {spec}", "")
            return 2
        results = [core.convert_pdf(Path(args.files[0]), segments,
                                    fmt=fmt, dpi=dpi)]
    else:
        if not args.files:
            print("usage: pdfpixel [--pages RANGE] [--format FMT] [--dpi N] "
                  "FILE.pdf [FILE2.pdf ...]", file=sys.stderr)
            return 2
        segments = None
        if args.pages is not None:
            try:
                segments = core.parse_pages(args.pages)
            except ValueError:
                notifier(f"Invalid page range: {args.pages}", "")
                return 2
        results = [core.convert_pdf(Path(p), segments, fmt=fmt, dpi=dpi)
                   for p in args.files]

    summary, body = core.build_summary(results)
    notifier(summary, body)
    print(summary)
    return 0 if all(r.ok for r in results) else 1


# --- merge / split / compress --------------------------------------------

def _merge(argv, notifier) -> int:
    parser = argparse.ArgumentParser(prog="pdfpixel merge")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)
    if not args.files:
        print("usage: pdfpixel merge FILE.pdf [FILE2.pdf ...]", file=sys.stderr)
        return 2
    r = pdfops.merge([Path(p) for p in args.files])
    if not r.ok:
        notifier(r.error, "")
        return 1
    summary = f"Merged {len(args.files)} PDFs"
    notifier(summary, str(r.path))
    print(summary)
    return 0


def _split(argv, notifier) -> int:
    parser = argparse.ArgumentParser(prog="pdfpixel split")
    parser.add_argument("file")
    args = parser.parse_args(argv)
    r = pdfops.split(Path(args.file))
    if not r.ok:
        notifier(r.error, "")
        return 1
    summary = f"Split into {r.pages} pages"
    notifier(summary, "")
    print(summary)
    return 0


def _compress(argv, notifier) -> int:
    parser = argparse.ArgumentParser(prog="pdfpixel compress")
    parser.add_argument("file")
    args = parser.parse_args(argv)
    r = pdfops.compress(Path(args.file))
    if not r.ok:
        notifier(r.error, "")
        return 1
    summary = "Compressed"
    notifier(summary, r.path.name)
    print(summary)
    return 0


# --- entry point ----------------------------------------------------------

def main(argv, ask=None, notifier=None) -> int:
    ask = ask or _default_ask
    notifier = notifier or _notify

    if argv and argv[0] == "--version":
        print(f"pdfpixel {__version__}")
        return 0

    if argv and argv[0] in _OPS:
        verb, rest = argv[0], argv[1:]
        if verb == "merge":
            return _merge(rest, notifier)
        if verb == "split":
            return _split(rest, notifier)
        return _compress(rest, notifier)

    # default verb = convert: bare files, --pages/--ask/--format/--dpi, or empty
    return _convert(argv, ask, notifier)


def run():  # console-script / frozen entry point
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
