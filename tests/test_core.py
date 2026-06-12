import platform
from pathlib import Path

import pytest

from pdfpixel import core


# --- unique_output_dir ---------------------------------------------------

def test_unique_output_dir_no_collision(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.touch()
    assert core.unique_output_dir(pdf) == tmp_path / "report"


def test_unique_output_dir_suffixes_on_collision(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.touch()
    (tmp_path / "report").mkdir()
    (tmp_path / "report (1)").mkdir()
    assert core.unique_output_dir(pdf) == tmp_path / "report (2)"


# --- parse_pages ---------------------------------------------------------

def test_parse_pages_single():
    assert core.parse_pages("5") == [(5, 5)]


def test_parse_pages_closed_range():
    assert core.parse_pages("5-8") == [(5, 8)]


def test_parse_pages_open_end():
    assert core.parse_pages("5-") == [(5, None)]


def test_parse_pages_open_start():
    assert core.parse_pages("-8") == [(None, 8)]


def test_parse_pages_strips_whitespace():
    assert core.parse_pages("  5 - 8  ") == [(5, 8)]


def test_parse_pages_comma_list():
    assert core.parse_pages("1, 3-5, 6") == [(1, 1), (3, 5), (6, 6)]


def test_parse_pages_comma_with_open_end():
    assert core.parse_pages("1, 3-5, 6-") == [(1, 1), (3, 5), (6, None)]


def test_parse_pages_ignores_blank_segments():
    assert core.parse_pages("1,,2,") == [(1, 1), (2, 2)]


@pytest.mark.parametrize(
    "spec",
    ["abc", "5-2", "0", "-", "", "5-8-9", "-0", "0-3", "1,abc", ",", ", ,"],
)
def test_parse_pages_rejects_malformed(spec):
    with pytest.raises(ValueError):
        core.parse_pages(spec)


# --- build_summary -------------------------------------------------------

def test_build_summary_counts():
    results = [
        core.FileResult(Path("a.pdf"), ok=True, pages=3),
        core.FileResult(Path("b.pdf"), ok=False, error="boom"),
    ]
    summary, body = core.build_summary(results)
    assert "Converted 1 PDF" in summary
    assert "1 failed" in summary
    assert "boom" in body


# --- page_count ----------------------------------------------------------

def test_page_count_real(pdf12):
    assert core.page_count(pdf12) == 12


def test_page_count_encrypted_is_none(pdf_encrypted):
    assert core.page_count(pdf_encrypted) is None


# --- convert_pdf (real pypdfium2 rendering) ------------------------------

def test_convert_pdf_all_pages(pdf3):
    res = core.convert_pdf(pdf3)
    assert res.ok
    assert res.pages == 3
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*.png")) == ["1.png", "2.png", "3.png"]


def test_convert_pdf_closed_range(pdf12):
    res = core.convert_pdf(pdf12, segments=[(5, 8)])
    assert res.ok
    assert res.pages == 4
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


def test_convert_pdf_open_ended_range(pdf12):
    res = core.convert_pdf(pdf12, segments=[(10, None)])
    assert res.ok
    assert res.pages == 3
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == ["10.png", "11.png", "12.png"]


def test_convert_pdf_multi_segment(pdf12):
    res = core.convert_pdf(pdf12, segments=[(1, 2), (5, 5), (10, None)])
    assert res.ok
    assert res.pages == 6
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "01.png", "02.png", "05.png", "10.png", "11.png", "12.png"
    ]


def test_convert_pdf_out_of_range_in_mix_is_skipped(pdf12):
    # 1,50 on a 12-page PDF -> render page 1, silently skip 50
    res = core.convert_pdf(pdf12, segments=[(1, 1), (50, 50)])
    assert res.ok
    assert res.pages == 1
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == ["01.png"]


def test_convert_pdf_overshoot_clamps(pdf12):
    res = core.convert_pdf(pdf12, segments=[(11, 100)])
    assert res.ok
    assert res.pages == 2
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == ["11.png", "12.png"]


def test_convert_pdf_empty_pageset_fails_no_folder(pdf12):
    res = core.convert_pdf(pdf12, segments=[(50, None)])
    assert not res.ok
    assert res.error
    assert not (pdf12.parent / "doc12").exists()  # no litter folder


def test_convert_pdf_encrypted_fails(pdf_encrypted):
    res = core.convert_pdf(pdf_encrypted)
    assert not res.ok
    assert res.error
    assert not (pdf_encrypted.parent / "secret").exists()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="os.access(W_OK) on dirs is unreliable on Windows",
)
def test_convert_pdf_readonly_dir(readonly_pdf):
    res = core.convert_pdf(readonly_pdf)
    assert not res.ok
    assert "read-only" in res.error
