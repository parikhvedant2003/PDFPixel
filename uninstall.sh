#!/usr/bin/env bash
set -euo pipefail

rm -f "$HOME/.local/bin/pdfpixel"
rm -f "$HOME/.local/share/nautilus-python/extensions/pdfpixel.py"
# legacy path from older installs — clean up if present
rm -f "$HOME/.local/share/nautilus/python-extensions/pdfpixel.py"
killall nautilus 2>/dev/null || true  # plain signal; avoids GTK-load crash in polluted shells
echo "PDFPixel removed."
