from pdfpixel import cli


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
