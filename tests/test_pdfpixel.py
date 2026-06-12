from pathlib import Path

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
