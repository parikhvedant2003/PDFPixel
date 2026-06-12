"""Generate a sample multi-page PDF for CI smoke tests: make_sample_pdf.py OUT [PAGES]."""
import sys

from fpdf import FPDF

out = sys.argv[1]
pages = int(sys.argv[2]) if len(sys.argv) > 2 else 5
pdf = FPDF()
for i in range(1, pages + 1):
    pdf.add_page()
    pdf.set_font("Helvetica", size=48)
    pdf.cell(0, 60, f"Page {i}")
pdf.output(out)
