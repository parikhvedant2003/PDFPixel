"""pdfpixel core — portable PDF-to-PNG engine (pypdfium2 + Pillow).

Pure conversion/naming/range logic with no GUI or notification code, so it is
fully unit-testable and identical across Linux, Windows and macOS.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium

DEFAULT_DPI = 200  # preserve current behaviour (pypdfium2 renders relative to 72 dpi)

# fmt -> output extension; "jpeg" is an alias of "jpg"
_FMT_EXT = {"png": "png", "jpg": "jpg", "jpeg": "jpg", "webp": "webp", "tiff": "tiff"}


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


# --- page-range parsing --------------------------------------------------

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
    open-ended. Blank segments (stray commas) are ignored. Raises ValueError on
    a malformed segment or if no segment remains.
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


def _expand(segments, total: int):
    """Segments -> sorted, deduped list of page numbers clamped to [1, total].

    Out-of-range pages are dropped (a mix like 1,50 on a 12-page doc yields [1])."""
    pages = set()
    for first, last in segments:
        lo = 1 if first is None else first
        hi = total if last is None else last
        for n in range(lo, hi + 1):
            if 1 <= n <= total:
                pages.add(n)
    return sorted(pages)


# --- conversion ----------------------------------------------------------

def page_count(pdf_path: Path):
    """Page count, or None if the PDF can't be read (encrypted/corrupt)."""
    try:
        doc = pdfium.PdfDocument(str(pdf_path))
    except pdfium.PdfiumError:
        return None
    try:
        return len(doc)
    finally:
        doc.close()


def convert_pdf(pdf_path: Path, segments=None, fmt: str = "png",
                dpi: int = DEFAULT_DPI) -> FileResult:
    """Render pages of one PDF to images in a sibling folder.

    ``segments`` is None (all pages) or a list of (first, last) tuples
    (None = open-ended). ``fmt`` is one of png/jpg/webp/tiff ("jpeg" aliases
    "jpg"). ``dpi`` sets the render scale (dpi / 72). Images are named by
    original page number, zero-padded to the document's page-count width, with
    the format's extension. JPG has no alpha so the image is flattened to RGB.
    """
    fmt = fmt.lower()
    ext = _FMT_EXT.get(fmt)
    if ext is None:
        return FileResult(pdf_path, ok=False, error=f"unsupported format: {fmt}")
    pdf_path = Path(pdf_path)
    if not os.access(pdf_path.parent, os.W_OK):
        return FileResult(pdf_path, ok=False, error="read-only directory")
    try:
        doc = pdfium.PdfDocument(str(pdf_path))
    except pdfium.PdfiumError:
        return FileResult(pdf_path, ok=False, error="encrypted or unreadable PDF")
    try:
        total = len(doc)
        pages = list(range(1, total + 1)) if segments is None else _expand(segments, total)
        if not pages:  # nothing in range -> don't create an empty folder
            return FileResult(pdf_path, ok=False, error="no pages produced")
        out_dir = unique_output_dir(pdf_path)
        try:
            out_dir.mkdir()
        except OSError as e:
            return FileResult(pdf_path, ok=False, error=str(e))
        width = len(str(total))
        scale = dpi / 72.0
        try:
            for n in pages:
                bitmap = doc[n - 1].render(scale=scale)
                img = bitmap.to_pil()
                if ext == "jpg":  # JPG has no alpha channel
                    img = img.convert("RGB")
                img.save(out_dir / f"{n:0{width}d}.{ext}")
        except Exception as e:  # render/save failure -> no half-written folder
            shutil.rmtree(out_dir, ignore_errors=True)
            return FileResult(pdf_path, ok=False, error=str(e))
        return FileResult(pdf_path, ok=True, pages=len(pages))
    finally:
        doc.close()


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
