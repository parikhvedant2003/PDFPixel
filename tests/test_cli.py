from pdfpixel import cli, core, pdfops
from pdfpixel.dialog import AskResult


def _silent(*a, **k):
    pass


def test_main_no_args_returns_2():
    assert cli.main([], notifier=_silent) == 2


def test_main_version(capsys):
    assert cli.main(["--version"], notifier=_silent) == 0
    out = capsys.readouterr().out
    assert any(ch.isdigit() for ch in out)  # prints a version number


def test_main_all_pages_end_to_end(pdf3, pdf_encrypted):
    rc = cli.main([str(pdf3), str(pdf_encrypted)], notifier=_silent)
    assert rc == 1  # one of two failed
    assert (pdf3.parent / "doc" / "1.png").exists()


def test_main_pages_flag(pdf12):
    rc = cli.main(["--pages", "5-8", str(pdf12)], notifier=_silent)
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


def test_main_pages_comma_list(pdf12):
    rc = cli.main(["--pages", "1,3-5", str(pdf12)], notifier=_silent)
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "01.png", "03.png", "04.png", "05.png"
    ]


def test_main_malformed_pages_returns_2(pdf3):
    rc = cli.main(["--pages", "abc", str(pdf3)], notifier=_silent)
    assert rc == 2
    assert not (pdf3.parent / "doc").exists()


def test_main_ask_converts_with_injected_spec(pdf12):
    rc = cli.main(["--ask", str(pdf12)], ask=lambda path: "5-8", notifier=_silent)
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


def test_main_ask_cancelled_is_noop(pdf12):
    rc = cli.main(["--ask", str(pdf12)], ask=lambda path: "", notifier=_silent)
    assert rc == 0
    assert not (pdf12.parent / "doc12").exists()


def test_main_ask_malformed_spec_returns_2(pdf12):
    rc = cli.main(["--ask", str(pdf12)], ask=lambda path: "abc", notifier=_silent)
    assert rc == 2
    assert not (pdf12.parent / "doc12").exists()


def test_main_ask_requires_single_file(pdf3, pdf12):
    rc = cli.main(["--ask", str(pdf3), str(pdf12)], ask=lambda path: "1", notifier=_silent)
    assert rc == 2


# --- default-verb routing -------------------------------------------------

def test_default_verb_bare_file_converts(pdf3):
    # first token is a file (not merge/split/compress) -> convert path
    rc = cli.main([str(pdf3)], notifier=_silent)
    assert rc == 0
    assert (pdf3.parent / "doc" / "1.png").exists()


def test_default_verb_pages_flag_still_converts(pdf12):
    # first token is an option, not a verb -> still routes to convert
    rc = cli.main(["--pages", "5-8", str(pdf12)], notifier=_silent)
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


# --- --format / --dpi plumbed into convert --------------------------------

def test_format_flag_changes_extension(pdf3):
    rc = cli.main(["--format", "jpg", str(pdf3)], notifier=_silent)
    assert rc == 0
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*")) == ["1.jpg", "2.jpg", "3.jpg"]


def test_format_and_dpi_threaded_into_core(pdf3, monkeypatch):
    captured = {}

    def spy(pdf_path, segments=None, fmt="png", dpi=core.DEFAULT_DPI):
        captured["fmt"] = fmt
        captured["dpi"] = dpi
        return core.FileResult(pdf_path, ok=True, pages=1)

    monkeypatch.setattr(core, "convert_pdf", spy)
    rc = cli.main(["--format", "webp", "--dpi", "300", str(pdf3)], notifier=_silent)
    assert rc == 0
    assert captured == {"fmt": "webp", "dpi": 300}


def test_invalid_format_choice_returns_2(pdf3, capsys):
    import pytest
    with pytest.raises(SystemExit) as exc:
        cli.main(["--format", "gif", str(pdf3)], notifier=_silent)
    assert exc.value.code == 2


def test_dpi_default_is_200(pdf3, monkeypatch):
    captured = {}

    def spy(pdf_path, segments=None, fmt="png", dpi=None):
        captured["fmt"] = fmt
        captured["dpi"] = dpi
        return core.FileResult(pdf_path, ok=True, pages=1)

    monkeypatch.setattr(core, "convert_pdf", spy)
    rc = cli.main([str(pdf3)], notifier=_silent)
    assert rc == 0
    assert captured == {"fmt": "png", "dpi": 200}


# --- --ask AskResult override ---------------------------------------------

def test_ask_result_overrides_format_and_dpi(pdf3, monkeypatch):
    captured = {}

    def spy(pdf_path, segments=None, fmt="png", dpi=core.DEFAULT_DPI):
        captured["fmt"] = fmt
        captured["dpi"] = dpi
        return core.FileResult(pdf_path, ok=True, pages=1)

    monkeypatch.setattr(core, "convert_pdf", spy)
    # CLI says png/200, AskResult says jpg/300 -> AskResult wins
    rc = cli.main(
        ["--ask", "--format", "png", "--dpi", "200", str(pdf3)],
        ask=lambda path: AskResult("1-2", "jpg", 300),
        notifier=_silent,
    )
    assert rc == 0
    assert captured == {"fmt": "jpg", "dpi": 300}


def test_ask_result_empty_spec_is_noop(pdf12):
    rc = cli.main(
        ["--ask", str(pdf12)],
        ask=lambda path: AskResult("", "png", 200),
        notifier=_silent,
    )
    assert rc == 0
    assert not (pdf12.parent / "doc12").exists()


def test_ask_result_drives_conversion(pdf12):
    rc = cli.main(
        ["--ask", str(pdf12)],
        ask=lambda path: AskResult("5-8", "png", 200),
        notifier=_silent,
    )
    assert rc == 0
    out = pdf12.parent / "doc12"
    assert sorted(f.name for f in out.glob("*.png")) == [
        "05.png", "06.png", "07.png", "08.png"
    ]


# --- merge / split / compress dispatch ------------------------------------

def test_merge_dispatches_to_pdfops(tmp_path, monkeypatch):
    calls = {}

    def spy(inputs, out=None):
        calls["inputs"] = [str(p) for p in inputs]
        return core.FileResult(tmp_path / "merged.pdf", ok=True, pages=5)

    monkeypatch.setattr(pdfops, "merge", spy)
    msgs = []
    rc = cli.main(
        ["merge", "a.pdf", "b.pdf"],
        notifier=lambda s, b="": msgs.append((s, b)),
    )
    assert rc == 0
    assert calls["inputs"] == ["a.pdf", "b.pdf"]
    assert msgs[0] == ("Merged 2 PDFs", str(tmp_path / "merged.pdf"))


def test_merge_no_inputs_returns_2():
    assert cli.main(["merge"], notifier=_silent) == 2


def test_merge_failure_returns_1(monkeypatch):
    monkeypatch.setattr(
        pdfops, "merge",
        lambda inputs, out=None: core.FileResult(inputs[0], ok=False,
                                                  error="encrypted or unreadable PDF"),
    )
    msgs = []
    rc = cli.main(["merge", "a.pdf", "b.pdf"],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 1
    assert msgs[0] == ("encrypted or unreadable PDF", "")


def test_split_dispatches_to_pdfops(monkeypatch):
    monkeypatch.setattr(
        pdfops, "split",
        lambda p: core.FileResult(p, ok=True, pages=7),
    )
    msgs = []
    rc = cli.main(["split", "doc.pdf"],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 0
    assert msgs[0] == ("Split into 7 pages", "")


def test_split_failure_returns_1(monkeypatch):
    monkeypatch.setattr(
        pdfops, "split",
        lambda p: core.FileResult(p, ok=False, error="encrypted or unreadable PDF"),
    )
    msgs = []
    rc = cli.main(["split", "doc.pdf"],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 1
    assert msgs[0] == ("encrypted or unreadable PDF", "")


def test_compress_dispatches_to_pdfops(tmp_path, monkeypatch):
    out = tmp_path / "doc_compressed.pdf"
    out.write_bytes(b"x" * 10)  # output must exist for the size report
    captured = {}

    def fake_compress(p, quality="medium"):
        captured["quality"] = quality
        return core.FileResult(out, ok=True, pages=3)

    monkeypatch.setattr(pdfops, "compress", fake_compress)
    msgs = []
    rc = cli.main(["compress", "--quality", "low", "doc.pdf"],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 0
    assert captured["quality"] == "low"          # --quality threaded through
    assert msgs[0][0].startswith("Compressed")   # size-delta summary
    assert msgs[0][1] == "doc_compressed.pdf"


def test_compress_failure_returns_1(monkeypatch):
    monkeypatch.setattr(
        pdfops, "compress",
        lambda p, quality="medium": core.FileResult(
            p, ok=False, error="encrypted or unreadable PDF"),
    )
    msgs = []
    rc = cli.main(["compress", "doc.pdf"],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 1
    assert msgs[0] == ("encrypted or unreadable PDF", "")


# --- real end-to-end pdfops dispatch (built with fpdf2 via fixtures) ------

def test_merge_real_pdfs_end_to_end(pdf3, pdf12):
    msgs = []
    rc = cli.main([
        "merge", str(pdf3), str(pdf12),
    ], notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 0
    out = pdf3.parent / "merged.pdf"
    assert out.exists()
    assert msgs[0] == ("Merged 2 PDFs", str(out))


def test_split_real_pdf_end_to_end(pdf3):
    msgs = []
    rc = cli.main(["split", str(pdf3)],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 0
    outs = sorted(p.name for p in pdf3.parent.glob("doc_p*.pdf"))
    assert outs == ["doc_p1.pdf", "doc_p2.pdf", "doc_p3.pdf"]
    assert msgs[0] == ("Split into 3 pages", "")


def test_compress_real_pdf_end_to_end(pdf3):
    msgs = []
    rc = cli.main(["compress", str(pdf3)],
                  notifier=lambda s, b="": msgs.append((s, b)))
    assert rc == 0
    assert (pdf3.parent / "doc_compressed.pdf").exists()
    assert msgs[0][0].startswith("Compressed")
    assert msgs[0][1] == "doc_compressed.pdf"


# --- usage errors ----------------------------------------------------------

def test_split_no_file_returns_2():
    import pytest
    with pytest.raises(SystemExit) as exc:
        cli.main(["split"], notifier=_silent)
    assert exc.value.code == 2


def test_compress_no_file_returns_2():
    import pytest
    with pytest.raises(SystemExit) as exc:
        cli.main(["compress"], notifier=_silent)
    assert exc.value.code == 2
