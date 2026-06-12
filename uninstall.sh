#!/usr/bin/env bash
set -euo pipefail

rm -f "$HOME/.local/bin/pdfpixel"
rm -f "$HOME/.local/share/nautilus/python-extensions/pdfpixel.py"
nautilus -q || true
echo "PDFPixel removed."
