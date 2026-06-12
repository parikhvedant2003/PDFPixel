#!/usr/bin/env bash
set -euo pipefail

python3 -m pip uninstall -y pdfpixel 2>/dev/null || true
rm -f "$HOME/.local/share/nautilus-python/extensions/pdfpixel.py"
# legacy path from older installs
rm -f "$HOME/.local/share/nautilus/python-extensions/pdfpixel.py"
killall nautilus 2>/dev/null || true  # plain signal; avoids GTK-load crash in polluted shells
echo "PDFPixel removed."
