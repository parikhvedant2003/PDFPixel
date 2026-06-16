"""pdfpixel pdfops — portable PDF operations (merge/split/compress) via pikepdf.

Pure file-level PDF manipulation with no GUI or notification code, so it is
fully unit-testable and identical across Linux, Windows and macOS. Reuses the
``FileResult`` dataclass from :mod:`pdfpixel.core` for the ``ok``/``error``
contract shared with the render engine.
"""
from __future__ import annotations

from pathlib import Path

import pikepdf

from pdfpixel.core import FileResult


def unique_output_path(directory: Path, stem: str, suffix: str = ".pdf") -> Path:
    """Return a non-existing path ``stem{suffix}`` in ``directory``.

    On collision, bump to ``stem-1``, ``stem-2``... so an existing file is never
    overwritten.
    """
    directory = Path(directory)
    candidate = directory / f"{stem}{suffix}"
    n = 1
    while candidate.exists():
        candidate = directory / f"{stem}-{n}{suffix}"
        n += 1
    return candidate


def merge(inputs: list[Path], out: Path | None = None) -> FileResult:
    """Concatenate all pages of ``inputs`` (in order) into one PDF.

    ``out`` defaults to a non-clobbering ``merged.pdf`` in ``inputs[0].parent``.
    On any unreadable/encrypted input, or zero inputs, returns
    ``FileResult(ok=False, ...)`` and writes nothing. ``pages`` is the total
    number of pages written.
    """
    inputs = [Path(p) for p in inputs]
    if not inputs:
        return FileResult(Path(), ok=False, error="no input files")

    merged = pikepdf.Pdf.new()
    try:
        total = 0
        for src in inputs:
            try:
                with pikepdf.Pdf.open(src) as doc:
                    merged.pages.extend(doc.pages)
                    total += len(doc.pages)
            except (pikepdf.PasswordError, pikepdf.PdfError):
                return FileResult(src, ok=False, error="encrypted or unreadable PDF")
            except OSError as e:
                return FileResult(src, ok=False, error=str(e))

        if out is None:
            out = unique_output_path(inputs[0].parent, "merged")
        else:
            out = Path(out)
        try:
            merged.save(out)
        except OSError as e:
            return FileResult(out, ok=False, error=str(e))
        return FileResult(out, ok=True, pages=total)
    finally:
        merged.close()


def split(pdf_path: Path) -> FileResult:
    """Write one single-page PDF per page beside the source.

    Files are named ``f"{stem}_p{n:0{width}d}.pdf"`` where ``width`` is the
    page-count width. Never overwrites the source. ``pages`` is the number of
    files written. Encrypted/unreadable input -> ``FileResult(ok=False, ...)``.
    """
    pdf_path = Path(pdf_path)
    try:
        doc = pikepdf.Pdf.open(pdf_path)
    except (pikepdf.PasswordError, pikepdf.PdfError):
        return FileResult(pdf_path, ok=False, error="encrypted or unreadable PDF")
    except OSError as e:
        return FileResult(pdf_path, ok=False, error=str(e))
    try:
        total = len(doc.pages)
        width = len(str(total))
        written = 0
        for n in range(1, total + 1):
            single = pikepdf.Pdf.new()
            try:
                single.pages.append(doc.pages[n - 1])
                out = pdf_path.parent / f"{pdf_path.stem}_p{n:0{width}d}.pdf"
                single.save(out)
            finally:
                single.close()
            written += 1
        return FileResult(pdf_path, ok=True, pages=written)
    finally:
        doc.close()


def compress(pdf_path: Path) -> FileResult:
    """Write ``f"{stem}_compressed.pdf"`` beside source via qpdf optimization.

    Uses object-stream generation + stream recompression. Never overwrites the
    source. ``pages`` is the page count. Encrypted/unreadable input ->
    ``FileResult(ok=False, ...)``.
    """
    pdf_path = Path(pdf_path)
    try:
        doc = pikepdf.Pdf.open(pdf_path)
    except (pikepdf.PasswordError, pikepdf.PdfError):
        return FileResult(pdf_path, ok=False, error="encrypted or unreadable PDF")
    except OSError as e:
        return FileResult(pdf_path, ok=False, error=str(e))
    try:
        out = pdf_path.parent / f"{pdf_path.stem}_compressed.pdf"
        try:
            doc.save(
                out,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )
        except OSError as e:
            return FileResult(pdf_path, ok=False, error=str(e))
        return FileResult(out, ok=True, pages=len(doc.pages))
    finally:
        doc.close()
