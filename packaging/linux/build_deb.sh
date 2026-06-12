#!/usr/bin/env bash
# Build a self-contained .deb: PyInstaller onedir (bundles pypdfium2, Pillow,
# tkinter) + Nautilus shim. Run from a checkout with dev deps installed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${PYTHON:-python3}"
VERSION="$("$PY" -c 'import pdfpixel; print(pdfpixel.__version__)')"
ARCH="$(dpkg --print-architecture)"

BUILD="$ROOT/build"
DIST="$BUILD/dist"
STAGE="$BUILD/deb/pdfpixel"
rm -rf "$BUILD"
mkdir -p "$DIST"

echo "==> Freezing pdfpixel $VERSION ($ARCH) with PyInstaller"
"$PY" -m PyInstaller --onedir --name pdfpixel --noconfirm \
    --paths "$ROOT" \
    --collect-all pypdfium2 --collect-all pypdfium2_raw \
    --distpath "$DIST" --workpath "$BUILD/work" --specpath "$BUILD" \
    "$ROOT/packaging/entry.py"

echo "==> Staging .deb tree"
mkdir -p "$STAGE/opt" "$STAGE/usr/bin" \
         "$STAGE/usr/share/nautilus-python/extensions" "$STAGE/DEBIAN"
cp -r "$DIST/pdfpixel" "$STAGE/opt/pdfpixel"
ln -s /opt/pdfpixel/pdfpixel "$STAGE/usr/bin/pdfpixel"
install -m 0644 "$ROOT/integrations/linux/pdfpixel_nautilus.py" \
    "$STAGE/usr/share/nautilus-python/extensions/pdfpixel.py"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: pdfpixel
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3-nautilus, libnotify-bin
Maintainer: PDFPixel <noreply@pdfpixel.local>
Description: Right-click a PDF -> every page as a PNG image
 Adds a "Convert to Images" entry (All Pages / Custom Range) to the Nautilus
 right-click menu. Self-contained: bundles its PDF engine and dialog.
EOF

cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
killall nautilus 2>/dev/null || true
EOF
cat > "$STAGE/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
killall nautilus 2>/dev/null || true
EOF
chmod 0755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"

DEB="$DIST/pdfpixel_${VERSION}_${ARCH}.deb"
echo "==> Building $DEB"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB"
echo "built: $DEB"
