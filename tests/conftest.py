import os
import stat

import pytest
from fpdf import FPDF


def _make_pdf(path, pages=3, user_password=None):
    pdf = FPDF()
    for i in range(1, pages + 1):
        pdf.add_page()
        pdf.set_font("Helvetica", size=48)
        pdf.cell(0, 60, f"Page {i}")
    if user_password is not None:
        # user_password forces an open-password so pdftoppm fails without -upw
        pdf.set_encryption(owner_password="owner", user_password=user_password)
    pdf.output(str(path))
    return path


@pytest.fixture
def pdf3(tmp_path):
    return _make_pdf(tmp_path / "doc.pdf", pages=3)


@pytest.fixture
def pdf_encrypted(tmp_path):
    return _make_pdf(tmp_path / "secret.pdf", pages=2, user_password="hunter2")


@pytest.fixture
def readonly_pdf(tmp_path):
    d = tmp_path / "ro"
    d.mkdir()
    pdf = _make_pdf(d / "x.pdf", pages=1)
    os.chmod(d, stat.S_IRUSR | stat.S_IXUSR)  # read+exec, no write
    yield pdf
    os.chmod(d, stat.S_IRWXU)  # restore so tmp_path cleanup succeeds
