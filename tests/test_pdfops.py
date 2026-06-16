from pathlib import Path

import pikepdf
import pytest
from fpdf import FPDF

from pdfpixel import pdfops


# --- helpers -------------------------------------------------------------

def _make_pdf(path, pages=3, text_size=48):
    pdf = FPDF()
    for i in range(1, pages + 1):
        pdf.add_page()
        pdf.set_font("Helvetica", size=text_size)
        # Lots of text so compression has something to chew on.
        for _ in range(20):
            pdf.cell(0, 8, f"Page {i} line of fairly repetitive sample content")
            pdf.ln(8)
    pdf.output(str(path))
    return Path(path)


def _page_count(path):
    with pikepdf.Pdf.open(path) as doc:
        return len(doc.pages)


# --- unique_output_path --------------------------------------------------

def test_unique_output_path_no_collision(tmp_path):
    assert pdfops.unique_output_path(tmp_path, "merged") == tmp_path / "merged.pdf"


def test_unique_output_path_bumps_on_collision(tmp_path):
    (tmp_path / "merged.pdf").touch()
    (tmp_path / "merged-1.pdf").touch()
    assert pdfops.unique_output_path(tmp_path, "merged") == tmp_path / "merged-2.pdf"


# --- merge ---------------------------------------------------------------

def test_merge_page_count_is_sum(tmp_path):
    a = _make_pdf(tmp_path / "a.pdf", pages=3)
    b = _make_pdf(tmp_path / "b.pdf", pages=2)
    res = pdfops.merge([a, b])
    assert res.ok
    assert res.pages == 5
    assert res.path.exists()
    assert res.path == tmp_path / "merged.pdf"
    assert _page_count(res.path) == 5


def test_merge_default_output_does_not_clobber(tmp_path):
    a = _make_pdf(tmp_path / "a.pdf", pages=1)
    b = _make_pdf(tmp_path / "b.pdf", pages=1)
    (tmp_path / "merged.pdf").write_bytes(b"not a real pdf")
    res = pdfops.merge([a, b])
    assert res.ok
    assert res.path == tmp_path / "merged-1.pdf"
    assert (tmp_path / "merged.pdf").read_bytes() == b"not a real pdf"  # untouched


def test_merge_explicit_output(tmp_path):
    a = _make_pdf(tmp_path / "a.pdf", pages=2)
    out = tmp_path / "combined.pdf"
    res = pdfops.merge([a], out=out)
    assert res.ok
    assert res.path == out
    assert _page_count(out) == 2


def test_merge_no_inputs_fails(tmp_path):
    res = pdfops.merge([])
    assert not res.ok
    assert res.error


def test_merge_bad_input_writes_nothing(tmp_path):
    good = _make_pdf(tmp_path / "good.pdf", pages=2)
    missing = tmp_path / "nope.pdf"
    res = pdfops.merge([good, missing])
    assert not res.ok
    assert res.error
    assert not (tmp_path / "merged.pdf").exists()


def test_merge_encrypted_input_fails(pdf_encrypted, tmp_path):
    good = _make_pdf(tmp_path / "good.pdf", pages=1)
    res = pdfops.merge([good, pdf_encrypted])
    assert not res.ok
    assert res.error


# --- split ---------------------------------------------------------------

def test_split_produces_one_file_per_page(tmp_path):
    src = _make_pdf(tmp_path / "doc.pdf", pages=12)
    res = pdfops.split(src)
    assert res.ok
    assert res.pages == 12
    outs = sorted(p.name for p in tmp_path.glob("doc_p*.pdf"))
    assert outs == [f"doc_p{n:02d}.pdf" for n in range(1, 13)]
    for p in tmp_path.glob("doc_p*.pdf"):
        assert _page_count(p) == 1


def test_split_leaves_source_intact(tmp_path):
    src = _make_pdf(tmp_path / "doc.pdf", pages=3)
    before = src.read_bytes()
    res = pdfops.split(src)
    assert res.ok
    assert src.exists()
    assert src.read_bytes() == before


def test_split_single_page_no_padding(tmp_path):
    src = _make_pdf(tmp_path / "one.pdf", pages=1)
    res = pdfops.split(src)
    assert res.ok
    assert res.pages == 1
    assert (tmp_path / "one_p1.pdf").exists()


def test_split_encrypted_fails(pdf_encrypted):
    res = pdfops.split(pdf_encrypted)
    assert not res.ok
    assert res.error


def test_split_nonexistent_fails(tmp_path):
    res = pdfops.split(tmp_path / "ghost.pdf")
    assert not res.ok
    assert res.error


# --- compress ------------------------------------------------------------

def test_compress_output_opens_and_not_larger(tmp_path):
    src = _make_pdf(tmp_path / "doc.pdf", pages=8)
    res = pdfops.compress(src)
    assert res.ok
    assert res.pages == 8
    out = tmp_path / "doc_compressed.pdf"
    assert res.path == out
    assert out.exists()
    assert _page_count(out) == 8  # openable
    assert out.stat().st_size <= src.stat().st_size


def test_compress_leaves_source_intact(tmp_path):
    src = _make_pdf(tmp_path / "doc.pdf", pages=3)
    before = src.read_bytes()
    res = pdfops.compress(src)
    assert res.ok
    assert src.exists()
    assert src.read_bytes() == before


def test_compress_encrypted_fails(pdf_encrypted):
    res = pdfops.compress(pdf_encrypted)
    assert not res.ok
    assert res.error


def test_compress_nonexistent_fails(tmp_path):
    res = pdfops.compress(tmp_path / "ghost.pdf")
    assert not res.ok
    assert res.error
