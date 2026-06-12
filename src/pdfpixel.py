#!/usr/bin/env python3
"""pdfpixel — render each page of one or more PDFs to PNG images.

Usage: pdfpixel FILE.pdf [FILE2.pdf ...]
For each PDF: create a sibling folder named after the PDF (suffixed " (n)" on
collision) and write one PNG per page named by zero-padded page number, then
send one summary desktop notification.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DPI = 200
PAGE_PREFIX = "p"  # temp prefix handed to pdftoppm, stripped afterwards


@dataclass
class FileResult:
    path: Path
    ok: bool
    pages: int = 0
    error: str | None = None


def unique_output_dir(pdf_path: Path) -> Path:
    """Return a non-existing output dir beside the PDF, suffixed (n) on collision."""
    pdf_path = Path(pdf_path)
    candidate = pdf_path.parent / pdf_path.stem
    n = 1
    while candidate.exists():
        candidate = pdf_path.parent / f"{pdf_path.stem} ({n})"
        n += 1
    return candidate


def rename_pages(out_dir: Path, prefix: str = PAGE_PREFIX) -> None:
    """Strip the pdftoppm prefix so files are bare page numbers: p-07.png -> 07.png."""
    out_dir = Path(out_dir)
    pat = re.compile(rf"^{re.escape(prefix)}-(\d+)\.png$")
    for f in out_dir.iterdir():
        m = pat.match(f.name)
        if m:
            f.rename(out_dir / f"{m.group(1)}.png")


def _pos_int(s: str) -> int:
    if not s.isdigit():
        raise ValueError(f"not a positive integer: {s!r}")
    v = int(s)
    if v < 1:
        raise ValueError(f"page numbers start at 1: {s!r}")
    return v


def _parse_segment(s: str):
    """Parse one contiguous segment into (first, last); None means open-ended."""
    if "-" in s:
        left, _, right = s.partition("-")
        if "-" in right:
            raise ValueError(f"too many dashes: {s!r}")
        left, right = left.strip(), right.strip()
        first = _pos_int(left) if left else None
        last = _pos_int(right) if right else None
        if first is None and last is None:
            raise ValueError(f"empty range: {s!r}")
        if first is not None and last is not None and first > last:
            raise ValueError(f"reversed range: {s!r}")
        return (first, last)
    n = _pos_int(s)
    return (n, n)


def parse_pages(spec: str):
    """Parse a page spec into a list of (first, last) segments.

    Comma-separated segments, each ``N`` -> (N, N), ``N-M`` -> (N, M),
    ``N-`` -> (N, None), ``-M`` -> (None, M). Pages are 1-based; None means
    open-ended. Blank segments (stray commas/whitespace) are ignored. Raises
    ValueError on a malformed segment or if no segment remains.
    """
    segments = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        segments.append(_parse_segment(part))
    if not segments:
        raise ValueError(f"no pages: {spec!r}")
    return segments


def notify(summary: str, body: str = "") -> None:
    """Best-effort desktop notification; silent if notify-send is absent."""
    if shutil.which("notify-send") is None:
        return
    subprocess.run(["notify-send", summary, body], check=False)


def build_summary(results):
    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    total_pages = sum(r.pages for r in ok)
    summary = f"Converted {len(ok)} PDF{'s' if len(ok) != 1 else ''}"
    if failed:
        summary += f" · {len(failed)} failed"
    lines = [f"{total_pages} pages total"]
    for r in failed:
        lines.append(f"✗ {r.path.name}: {r.error}")
    return summary, "\n".join(lines)


def convert_pdf(pdf_path: Path, segments=None) -> FileResult:
    """Render pages of one PDF to PNGs. ``segments`` is None (all pages) or a
    list of (first, last) tuples (None = open-ended), one pdftoppm pass each."""
    pdf_path = Path(pdf_path)
    parent = pdf_path.parent
    if not os.access(parent, os.W_OK):
        return FileResult(pdf_path, ok=False, error="read-only directory")
    out_dir = unique_output_dir(pdf_path)
    try:
        out_dir.mkdir()
    except OSError as e:
        return FileResult(pdf_path, ok=False, error=str(e))
    for first, last in (segments or [(None, None)]):
        cmd = ["pdftoppm", "-png", "-r", str(DPI)]
        if first is not None:
            cmd += ["-f", str(first)]
        if last is not None:
            cmd += ["-l", str(last)]
        cmd += ["--", str(pdf_path), str(out_dir / PAGE_PREFIX)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            shutil.rmtree(out_dir, ignore_errors=True)  # don't leave a folder
            err = proc.stderr.strip().splitlines()
            return FileResult(pdf_path, ok=False,
                              error=err[-1] if err else "pdftoppm failed")
    rename_pages(out_dir)
    pages = len(list(out_dir.glob("*.png")))
    if pages == 0:  # produced nothing — don't leave an empty folder
        shutil.rmtree(out_dir, ignore_errors=True)
        return FileResult(pdf_path, ok=False, error="no pages produced")
    return FileResult(pdf_path, ok=True, pages=pages)


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="pdfpixel")
    parser.add_argument("--pages", help="contiguous page range, e.g. 5-8, 3, 5-, -8")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)
    if not args.files:
        print("usage: pdfpixel [--pages RANGE] FILE.pdf [FILE2.pdf ...]",
              file=sys.stderr)
        return 2
    segments = None
    if args.pages is not None:
        try:
            segments = parse_pages(args.pages)
        except ValueError:
            notify(f"Invalid page range: {args.pages}")
            return 2
    results = [convert_pdf(Path(p), segments) for p in args.files]
    summary, body = build_summary(results)
    notify(summary, body)
    print(summary)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
