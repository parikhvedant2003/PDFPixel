#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
EXT_DIR="$HOME/.local/share/nautilus/python-extensions"
SRC="$(cd "$(dirname "$0")" && pwd)/src"

echo "==> Checking dependencies"
missing_pkgs=()
command -v pdftoppm    >/dev/null 2>&1 || missing_pkgs+=("poppler-utils")
command -v notify-send >/dev/null 2>&1 || missing_pkgs+=("libnotify-bin")
dpkg -l python3-nautilus >/dev/null 2>&1 || missing_pkgs+=("python3-nautilus")

if [ "${#missing_pkgs[@]}" -gt 0 ]; then
    echo "Missing: ${missing_pkgs[*]}"
    echo "Install with:  sudo apt install ${missing_pkgs[*]}"
    read -r -p "Run that now with sudo? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        sudo apt update && sudo apt install -y "${missing_pkgs[@]}"
    else
        echo "Install the packages above, then re-run this script." >&2
        exit 1
    fi
fi

echo "==> Installing helper -> $BIN_DIR/pdfpixel"
mkdir -p "$BIN_DIR"
install -m 0755 "$SRC/pdfpixel.py" "$BIN_DIR/pdfpixel"

echo "==> Installing extension -> $EXT_DIR/pdfpixel.py"
mkdir -p "$EXT_DIR"
install -m 0644 "$SRC/pdfpixel_nautilus.py" "$EXT_DIR/pdfpixel.py"

echo "==> Reloading Nautilus"
nautilus -q || true

echo "Done. Right-click a PDF and choose 'Convert to Images'."
