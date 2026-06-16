"""pdfpixel pdfops — portable PDF operations (merge/split/compress) via pikepdf.

Pure file-level PDF manipulation with no GUI or notification code, so it is
fully unit-testable and identical across Linux, Windows and macOS. Reuses the
``FileResult`` dataclass from :mod:`pdfpixel.core` for the ``ok``/``error``
contract shared with the render engine.
"""
from __future__ import annotations

import io
from pathlib import Path

import pikepdf
from PIL import Image  # noqa: F401  (kept for parity with the render engine)

from pdfpixel.core import FileResult

# Image-compression quality presets: (max_pixel_dimension | None, jpeg_quality).
QUALITY_PRESETS = {
    "low": (1200, 60),
    "medium": (2000, 75),
    "high": (None, 85),
}


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


def _iter_image_xobjects(doc):
    """Yield each unique image XObject stream reachable from any page.

    Walks page Resources and recurses into Form XObjects' Resources. Dedups by
    object id so a shared image is visited (and recompressed) once.
    """
    seen = set()
    stack = []
    for page in doc.pages:
        res = page.get("/Resources")
        if res is not None:
            stack.append(res)
    while stack:
        res = stack.pop()
        xobjs = res.get("/XObject")
        if xobjs is None:
            continue
        for _name, xobj in xobjs.items():
            try:
                key = xobj.objgen
            except Exception:
                key = id(xobj)
            if key in seen:
                continue
            seen.add(key)
            subtype = str(xobj.get("/Subtype"))
            if subtype == "/Image":
                yield xobj
            elif subtype == "/Form":
                fres = xobj.get("/Resources")
                if fres is not None:
                    stack.append(fres)


def _recompress_image(xobj, max_dim, jpeg_quality):
    """Re-encode one image XObject to JPEG, downscaled to ``max_dim``.

    Returns ``(jpeg_bytes, (w, h), mode)`` if the image is safe to recompress
    AND the result is smaller than the current stream; otherwise ``None`` (leave
    the original untouched). Safe = plain RGB/grayscale, 8-bit, no transparency
    mask, not a stencil — so text, vectors, CMYK, indexed, and masked/alpha
    images are never corrupted.
    """
    if bool(xobj.get("/ImageMask", False)):
        return None
    if "/SMask" in xobj or "/Mask" in xobj:
        return None
    try:
        pil = pikepdf.PdfImage(xobj).as_pil_image()
    except Exception:
        return None  # undecodable colorspace/filter -> leave as-is
    if pil.mode not in ("RGB", "L"):
        return None  # indexed/CMYK/etc -> leave as-is

    w, h = pil.size
    if max_dim and max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        pil = pil.resize((max(1, round(w * scale)), max(1, round(h * scale))))

    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
    data = buf.getvalue()
    try:
        old = len(xobj.read_raw_bytes())
    except Exception:
        old = None
    if old is not None and len(data) >= old:
        return None  # would not shrink -> keep original
    return data, pil.size, pil.mode


def compress(pdf_path: Path, quality: str = "medium") -> FileResult:
    """Write ``f"{stem}_compressed.pdf"`` beside source, shrinking images.

    Walks the PDF's image XObjects and re-encodes the safe ones (RGB/grayscale,
    no transparency) to downscaled JPEG per the ``quality`` preset, then applies
    a qpdf structural pass (object streams + stream recompression). Text and
    vectors are preserved; CMYK/indexed/masked images are left untouched. Never
    overwrites the source. ``pages`` is the page count. Encrypted/unreadable
    input or an unknown ``quality`` -> ``FileResult(ok=False, ...)``.
    """
    pdf_path = Path(pdf_path)
    if quality not in QUALITY_PRESETS:
        return FileResult(pdf_path, ok=False, error=f"unknown quality: {quality}")
    max_dim, jpeg_quality = QUALITY_PRESETS[quality]
    try:
        doc = pikepdf.Pdf.open(pdf_path)
    except (pikepdf.PasswordError, pikepdf.PdfError):
        return FileResult(pdf_path, ok=False, error="encrypted or unreadable PDF")
    except OSError as e:
        return FileResult(pdf_path, ok=False, error=str(e))
    try:
        for xobj in _iter_image_xobjects(doc):
            res = _recompress_image(xobj, max_dim, jpeg_quality)
            if res is None:
                continue
            data, (w, h), mode = res
            xobj.write(data, filter=pikepdf.Name("/DCTDecode"))
            xobj.ColorSpace = (
                pikepdf.Name("/DeviceRGB") if mode == "RGB"
                else pikepdf.Name("/DeviceGray")
            )
            xobj.Width, xobj.Height = w, h
            xobj.BitsPerComponent = 8
            for k in ("/Decode", "/DecodeParms"):
                if k in xobj:
                    del xobj[k]

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
