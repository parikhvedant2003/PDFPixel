#!/usr/bin/env bash
# Build a .dmg: PyInstaller onedir (bundles pypdfium2, Pillow, tkinter) + the two
# Quick Action workflows + a double-clickable installer. macOS only.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${PYTHON:-python3}"
VERSION="$("$PY" -c 'import pdfpixel; print(pdfpixel.__version__)')"

BUILD="$ROOT/build"
DIST="$BUILD/dist"
STAGE="$BUILD/dmg"
rm -rf "$BUILD"
mkdir -p "$DIST" "$STAGE"

echo "==> Freezing pdfpixel $VERSION with PyInstaller"
"$PY" -m PyInstaller --onedir --name pdfpixel --noconfirm \
    --paths "$ROOT" \
    --collect-all pypdfium2 --collect-all pypdfium2_raw \
    --distpath "$DIST" --workpath "$BUILD/work" --specpath "$BUILD" \
    "$ROOT/packaging/entry.py"

echo "==> Staging .dmg contents"
mkdir -p "$STAGE/PDFPixel"
cp -R "$DIST/pdfpixel/." "$STAGE/PDFPixel/"
cp -R "$ROOT/integrations/macos/PDFPixel-AllPages.workflow" "$STAGE/"
cp -R "$ROOT/integrations/macos/PDFPixel-CustomRange.workflow" "$STAGE/"
cp "$ROOT/packaging/macos/Install PDFPixel.command" "$STAGE/"
chmod +x "$STAGE/Install PDFPixel.command"

DMG="$DIST/pdfpixel-${VERSION}.dmg"
echo "==> Building $DMG"
hdiutil create -volname "PDFPixel" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
echo "built: $DMG"
