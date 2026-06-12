from pathlib import Path

import pytest

import pdfpixel


def test_unique_output_dir_no_collision(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.touch()
    assert pdfpixel.unique_output_dir(pdf) == tmp_path / "report"


def test_unique_output_dir_suffixes_on_collision(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.touch()
    (tmp_path / "report").mkdir()
    (tmp_path / "report (1)").mkdir()
    assert pdfpixel.unique_output_dir(pdf) == tmp_path / "report (2)"


def test_rename_pages_strips_prefix(tmp_path):
    for name in ["p-01.png", "p-02.png", "p-10.png"]:
        (tmp_path / name).touch()
    pdfpixel.rename_pages(tmp_path)
    got = sorted(f.name for f in tmp_path.glob("*.png"))
    assert got == ["01.png", "02.png", "10.png"]


def test_notify_silent_without_binary(monkeypatch):
    monkeypatch.setattr(pdfpixel.shutil, "which", lambda _: None)
    pdfpixel.notify("hello", "world")  # must not raise


def test_build_summary_counts():
    results = [
        pdfpixel.FileResult(Path("a.pdf"), ok=True, pages=3),
        pdfpixel.FileResult(Path("b.pdf"), ok=False, error="boom"),
    ]
    summary, body = pdfpixel.build_summary(results)
    assert "Converted 1 PDF" in summary
    assert "1 failed" in summary
    assert "boom" in body


def test_convert_pdf_real(pdf3):
    res = pdfpixel.convert_pdf(pdf3)
    assert res.ok
    assert res.pages == 3
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*.png")) == ["1.png", "2.png", "3.png"]


def test_convert_pdf_encrypted_fails(pdf_encrypted):
    res = pdfpixel.convert_pdf(pdf_encrypted)
    assert not res.ok
    assert res.error
    assert not (pdf_encrypted.parent / "secret").exists()  # no litter folder


def test_convert_pdf_readonly_dir(readonly_pdf):
    res = pdfpixel.convert_pdf(readonly_pdf)
    assert not res.ok
    assert "read-only" in res.error


def test_main_cli_end_to_end(pdf3, pdf_encrypted, monkeypatch):
    monkeypatch.setattr(pdfpixel, "notify", lambda *a, **k: None)  # silence
    rc = pdfpixel.main([str(pdf3), str(pdf_encrypted)])
    assert rc == 1  # one of two failed
    assert (pdf3.parent / "doc" / "1.png").exists()


def test_main_no_args_returns_2():
    assert pdfpixel.main([]) == 2


def test_parse_pages_single():
    assert pdfpixel.parse_pages("5") == [(5, 5)]


def test_parse_pages_closed_range():
    assert pdfpixel.parse_pages("5-8") == [(5, 8)]


def test_parse_pages_open_end():
    assert pdfpixel.parse_pages("5-") == [(5, None)]


def test_parse_pages_open_start():
    assert pdfpixel.parse_pages("-8") == [(None, 8)]


def test_parse_pages_strips_whitespace():
    assert pdfpixel.parse_pages("  5 - 8  ") == [(5, 8)]


def test_parse_pages_comma_list():
    assert pdfpixel.parse_pages("1, 3-5, 6") == [(1, 1), (3, 5), (6, 6)]


def test_parse_pages_comma_with_open_end():
    assert pdfpixel.parse_pages("1, 3-5, 6-") == [(1, 1), (3, 5), (6, None)]


def test_parse_pages_ignores_blank_segments():
    assert pdfpixel.parse_pages("1,,2,") == [(1, 1), (2, 2)]


@pytest.mark.parametrize(
    "spec",
    ["abc", "5-2", "0", "-", "", "5-8-9", "-0", "0-3", "1,abc", ",", ", ,"],
)
def test_parse_pages_rejects_malformed(spec):
    with pytest.raises(ValueError):
        pdfpixel.parse_pages(spec)


def test_convert_pdf_closed_range(pdf12):
    res = pdfpixel.convert_pdf(pdf12, segments=[(5, 8)])
    assert res.ok
    assert res.pages == 4
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


def test_convert_pdf_open_ended_range(pdf12):
    res = pdfpixel.convert_pdf(pdf12, segments=[(10, None)])
    assert res.ok
    assert res.pages == 3
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == ["10.png", "11.png", "12.png"]


def test_convert_pdf_multi_segment(pdf12):
    res = pdfpixel.convert_pdf(pdf12, segments=[(1, 2), (5, 5), (10, None)])
    assert res.ok
    assert res.pages == 6
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "01.png", "02.png", "05.png", "10.png", "11.png", "12.png"
    ]


def test_convert_pdf_first_past_end_fails(pdf12):
    res = pdfpixel.convert_pdf(pdf12, segments=[(50, None)])
    assert not res.ok
    assert res.error
    assert not (pdf12.parent / "doc12").exists()  # no litter folder


def test_convert_pdf_zero_pages_produced_is_failure(pdf3, monkeypatch):
    class FakeProc:
        returncode = 0
        stderr = ""

    monkeypatch.setattr(pdfpixel.subprocess, "run", lambda *a, **k: FakeProc())
    res = pdfpixel.convert_pdf(pdf3)
    assert not res.ok
    assert not (pdf3.parent / "doc").exists()


def test_main_pages_flag_end_to_end(pdf12, monkeypatch):
    monkeypatch.setattr(pdfpixel, "notify", lambda *a, **k: None)
    rc = pdfpixel.main(["--pages", "5-8", str(pdf12)])
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


def test_main_pages_comma_list_end_to_end(pdf12, monkeypatch):
    monkeypatch.setattr(pdfpixel, "notify", lambda *a, **k: None)
    rc = pdfpixel.main(["--pages", "1,3-5", str(pdf12)])
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "01.png", "03.png", "04.png", "05.png"
    ]


def test_main_malformed_pages_returns_2_without_converting(pdf3, monkeypatch):
    monkeypatch.setattr(pdfpixel, "notify", lambda *a, **k: None)
    rc = pdfpixel.main(["--pages", "abc", str(pdf3)])
    assert rc == 2
    assert not (pdf3.parent / "doc").exists()  # never attempted conversion
