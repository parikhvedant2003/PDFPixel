from PIL import Image

from pdfpixel import core, dialog


# --- fmt -> extension + pixel content ------------------------------------

def test_convert_pdf_jpg_produces_jpg_files_as_rgb(pdf3):
    res = core.convert_pdf(pdf3, fmt="jpg")
    assert res.ok
    assert res.pages == 3
    out = pdf3.parent / "doc"
    names = sorted(f.name for f in out.glob("*.jpg"))
    assert names == ["1.jpg", "2.jpg", "3.jpg"]
    # JPG has no alpha channel: image must open as RGB
    with Image.open(out / "1.jpg") as img:
        assert img.mode == "RGB"
        assert "A" not in img.getbands()


def test_convert_pdf_jpeg_alias_writes_jpg(pdf3):
    res = core.convert_pdf(pdf3, fmt="jpeg")
    assert res.ok
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*")) == ["1.jpg", "2.jpg", "3.jpg"]


def test_convert_pdf_webp_extension(pdf3):
    res = core.convert_pdf(pdf3, fmt="webp")
    assert res.ok
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*.webp")) == ["1.webp", "2.webp", "3.webp"]


def test_convert_pdf_tiff_extension(pdf3):
    res = core.convert_pdf(pdf3, fmt="tiff")
    assert res.ok
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*.tiff")) == ["1.tiff", "2.tiff", "3.tiff"]


def test_convert_pdf_fmt_is_case_insensitive(pdf3):
    res = core.convert_pdf(pdf3, fmt="PNG")
    assert res.ok
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*.png")) == ["1.png", "2.png", "3.png"]


# --- dpi controls pixel dimensions ---------------------------------------

def test_convert_pdf_higher_dpi_makes_larger_images(pdf3):
    lo = core.convert_pdf(pdf3, dpi=96)
    assert lo.ok
    with Image.open(pdf3.parent / "doc" / "1.png") as img:
        lo_size = img.size

    # second run lands in a suffixed sibling dir (doc (1)) -> no collision
    hi = core.convert_pdf(pdf3, dpi=300)
    assert hi.ok
    with Image.open(pdf3.parent / "doc (1)" / "1.png") as img:
        hi_size = img.size

    assert hi_size[0] > lo_size[0]
    assert hi_size[1] > lo_size[1]


# --- unsupported fmt ------------------------------------------------------

def test_convert_pdf_unknown_fmt_fails(pdf3):
    res = core.convert_pdf(pdf3, fmt="gif")
    assert not res.ok
    assert res.error == "unsupported format: gif"
    assert not (pdf3.parent / "doc").exists()  # validated before any work


# --- back-compat: default call unchanged ---------------------------------

def test_convert_pdf_default_is_png_200_unchanged(pdf3):
    # default (no fmt/dpi) must still produce PNGs at 200 dpi
    res = core.convert_pdf(pdf3)
    assert res.ok
    out = pdf3.parent / "doc"
    assert sorted(f.name for f in out.glob("*.png")) == ["1.png", "2.png", "3.png"]

    with Image.open(out / "1.png") as img:
        default_size = img.size

    # an explicit fmt="png", dpi=DEFAULT_DPI render is byte-identical in size
    res2 = core.convert_pdf(pdf3, fmt="png", dpi=core.DEFAULT_DPI)
    assert res2.ok
    with Image.open(pdf3.parent / "doc (1)" / "1.png") as img:
        assert img.size == default_size


def test_default_dpi_is_200():
    assert core.DEFAULT_DPI == 200


# --- dialog module (no tkinter import in headless tests) ------------------

def test_dialog_module_imports_and_askresult_shape():
    assert hasattr(dialog, "AskResult")
    r = dialog.AskResult("1-3", "jpg", 300)
    assert r.spec == "1-3"
    assert r.fmt == "jpg"
    assert r.dpi == 300
    assert tuple(r._fields) == ("spec", "fmt", "dpi")
