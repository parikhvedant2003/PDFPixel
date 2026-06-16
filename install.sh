#!/usr/bin/env bash
# Dev / from-source install for Linux. The shipping artifact is the .deb
# (see packaging/linux); this is for hacking on a checkout.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
EXT_DIR="$HOME/.local/share/nautilus-python/extensions"

echo "==> Checking system dependencies"
missing=()
command -v notify-send >/dev/null 2>&1 || missing+=("libnotify-bin")
dpkg -l python3-nautilus >/dev/null 2>&1 || missing+=("python3-nautilus")
# tkinter is bundled in the shipped .deb's frozen binary; a from-source install
# uses the system Python, which needs python3-tk for the Custom Range dialog.
python3 -c "import tkinter" >/dev/null 2>&1 || missing+=("python3-tk")

if [ "${#missing[@]}" -gt 0 ]; then
    echo "Missing: ${missing[*]}"
    read -r -p "Run 'sudo apt install ${missing[*]}' now? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        sudo apt update && sudo apt install -y "${missing[@]}"
    else
        echo "Install the packages above, then re-run." >&2
        exit 1
    fi
fi

echo "==> Installing pdfpixel (pip --user: console script + pypdfium2/pillow)"
python3 -m pip install --user "$HERE"

echo "==> Installing Nautilus extension -> $EXT_DIR/pdfpixel.py"
mkdir -p "$EXT_DIR"
install -m 0644 "$HERE/integrations/linux/pdfpixel_nautilus.py" "$EXT_DIR/pdfpixel.py"
# The shim imports the shared menu spec from its own dir — it MUST ship alongside.
install -m 0644 "$HERE/integrations/linux/pdfpixel_menu.py" "$EXT_DIR/pdfpixel_menu.py"

echo "==> Reloading Nautilus"
killall nautilus 2>/dev/null || true

echo "Done. Open Files (from your dock) and right-click a PDF -> 'PDFPixel'."
