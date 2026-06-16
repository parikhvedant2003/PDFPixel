"""Tests for the shared right-click menu source and the launcher generator.

pdfpixel_menu.py lives under integrations/linux/ (it ships into the system
Python's extension dirs, not the pdfpixel package), so we add that dir to the
import path here. The three gi-based shims can't be import-tested without
Nautilus/Nemo/Caja installed, so this covers the pure-stdlib core they share.
"""
import configparser
import importlib.util
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTEGRATIONS = os.path.join(REPO_ROOT, "integrations", "linux")
sys.path.insert(0, INTEGRATIONS)
import pdfpixel_menu as M  # noqa: E402


def _visible(pdfs_count):
    """Mirror the shim's arity filter: which actions show for N selected PDFs."""
    return [a for a in M.ACTIONS if not (a.arity == "single" and pdfs_count != 1)]


# --- is_pdf -----------------------------------------------------------------

def test_is_pdf_true_for_local_pdf():
    assert M.is_pdf("file", "application/pdf") is True


@pytest.mark.parametrize("scheme,mime", [
    ("trash", "application/pdf"),   # remote/trash URI
    ("sftp", "application/pdf"),
    ("file", "image/png"),          # local but not a PDF
    ("file", "text/plain"),
])
def test_is_pdf_false_otherwise(scheme, mime):
    assert M.is_pdf(scheme, mime) is False


# --- build_argv expansion ---------------------------------------------------

def test_build_argv_single_f_takes_first_path():
    split = next(a for a in M.ACTIONS if a.id == "split")
    assert M.build_argv(split, ["/a.pdf"]) == ["split", "/a.pdf"]


def test_build_argv_single_f_ignores_extra_paths():
    first = next(a for a in M.ACTIONS if a.id == "first")
    # "{f}" only ever consumes paths[0]
    assert M.build_argv(first, ["/a.pdf", "/b.pdf"]) == ["--pages", "1", "/a.pdf"]


def test_build_argv_ff_spreads_all_paths():
    merge = next(a for a in M.ACTIONS if a.id == "merge")
    assert M.build_argv(merge, ["/a.pdf", "/b.pdf", "/c.pdf"]) == [
        "merge", "/a.pdf", "/b.pdf", "/c.pdf"]


def test_build_argv_all_ff_only():
    allp = next(a for a in M.ACTIONS if a.id == "all")
    assert M.build_argv(allp, ["/a.pdf", "/b.pdf"]) == ["/a.pdf", "/b.pdf"]


def test_build_argv_custom_ask():
    custom = next(a for a in M.ACTIONS if a.id == "custom")
    assert M.build_argv(custom, ["/a.pdf"]) == ["--ask", "/a.pdf"]


def test_build_argv_excludes_helper_binary():
    # Result is a plain argv WITHOUT the pdfpixel binary in front.
    compress = next(a for a in M.ACTIONS if a.id == "compress")
    argv = M.build_argv(compress, ["/a.pdf"])
    assert M.helper_path() not in argv


# --- arity filtering --------------------------------------------------------

def test_single_selection_shows_everything():
    ids = [a.id for a in _visible(1)]
    assert ids == ["all", "first", "custom", "merge", "split", "compress"]


def test_multi_selection_hides_single_actions():
    ids = [a.id for a in _visible(3)]
    # only the "multi" actions survive a multi-select
    assert ids == ["all", "merge"]
    assert all(a.arity == "multi" for a in _visible(3))


def test_actions_have_expected_ids_and_arities():
    by_id = {a.id: a.arity for a in M.ACTIONS}
    assert by_id == {
        "all": "multi", "first": "single", "custom": "single",
        "merge": "multi", "split": "single", "compress": "single",
    }


def test_parent_labels():
    assert M.PARENT_LABEL == "PDFPixel"
    assert M.PARENT_TIP == "PDF tools by PDFPixel"


# --- gen_servicemenus -------------------------------------------------------

def _load_gen():
    path = os.path.join(REPO_ROOT, "packaging", "linux", "gen_servicemenus.py")
    spec = importlib.util.spec_from_file_location("gen_servicemenus", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gen_desktop_is_valid_and_has_all_actions():
    gen = _load_gen()
    text = gen.render_desktop()

    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)

    assert parser["Desktop Entry"]["Type"] == "Service"
    assert parser["Desktop Entry"]["ServiceTypes"] == "KonqPopupMenu/Plugin"
    assert parser["Desktop Entry"]["MimeType"] == "application/pdf;"
    assert parser["Desktop Entry"]["X-KDE-Submenu"] == "PDFPixel"

    # one [Desktop Action <Id>] section per ACTION, with the right field code
    for a in M.ACTIONS:
        section = f"Desktop Action PdfPixel{a.id.capitalize()}"
        assert section in parser, section
        assert parser[section]["Name"] == a.label
        assert parser[section]["Icon"] == "application-pdf"
        exec_line = parser[section]["Exec"]
        assert exec_line.startswith(gen.HELPER)
        code = "%f" if a.arity == "single" else "%F"
        assert code in exec_line


def test_gen_thunar_xml_has_one_action_per_action():
    gen = _load_gen()
    xml = gen.render_thunar_xml()
    assert xml.count("<action>") == len(M.ACTIONS)
    assert xml.count("</action>") == len(M.ACTIONS)
    for a in M.ACTIONS:
        assert f"PDFPixel: {a.label}" in xml


def test_gen_main_is_idempotent(tmp_path):
    gen = _load_gen()
    # Run twice; the committed files must be byte-identical between runs.
    gen.main()
    with open(gen.DESKTOP_PATH, "rb") as fh:
        first_desktop = fh.read()
    with open(gen.THUNAR_PATH, "rb") as fh:
        first_thunar = fh.read()

    gen.main()
    with open(gen.DESKTOP_PATH, "rb") as fh:
        assert fh.read() == first_desktop
    with open(gen.THUNAR_PATH, "rb") as fh:
        assert fh.read() == first_thunar
