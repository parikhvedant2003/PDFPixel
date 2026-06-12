#!/usr/bin/env bash
# Runs INSIDE an old-glibc container (Debian 11 = glibc 2.31) to produce a
# portable binary, then packages it as a .deb and a universal .AppImage.
# Wrapper: packaging/linux/build_in_container.sh
set -euo pipefail

ROOT="${1:-/src}"
cd "$ROOT"

export DEBIAN_FRONTEND=noninteractive
echo "==> Installing build deps (python, tk, packaging tools)"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv python3-tk \
    binutils file desktop-file-utils wget ca-certificates fakeroot >/dev/null

echo "==> glibc on this builder: $(ldd --version | head -1)"

python3 -m venv /tmp/benv
. /tmp/benv/bin/activate
pip install -q --upgrade pip
pip install -q . pyinstaller

VERSION="$(python3 -c 'import pdfpixel; print(pdfpixel.__version__)')"
ARCH="$(dpkg --print-architecture)"
BUILD="$ROOT/build"; DIST="$BUILD/dist"
rm -rf "$BUILD"; mkdir -p "$DIST"

echo "==> PyInstaller onedir"
pyinstaller --onedir --name pdfpixel --noconfirm \
    --paths "$ROOT" \
    --collect-all pypdfium2 --collect-all pypdfium2_raw \
    --distpath "$DIST" --workpath "$BUILD/work" --specpath "$BUILD" \
    "$ROOT/packaging/entry.py"

# ---- .deb -----------------------------------------------------------------
echo "==> Building .deb"
STAGE="$BUILD/deb/pdfpixel"
mkdir -p "$STAGE/opt" "$STAGE/usr/bin" \
         "$STAGE/usr/share/nautilus-python/extensions" "$STAGE/DEBIAN"
cp -r "$DIST/pdfpixel" "$STAGE/opt/pdfpixel"
ln -sf /opt/pdfpixel/pdfpixel "$STAGE/usr/bin/pdfpixel"
install -m 0644 "$ROOT/integrations/linux/pdfpixel_nautilus.py" \
    "$STAGE/usr/share/nautilus-python/extensions/pdfpixel.py"
# Nemo (Cinnamon) + Caja (MATE) share the Nautilus-python API.
mkdir -p "$STAGE/usr/share/nemo-python/extensions" "$STAGE/usr/share/caja-python/extensions"
install -m 0644 "$ROOT/integrations/linux/pdfpixel_nemo.py" \
    "$STAGE/usr/share/nemo-python/extensions/pdfpixel.py" 2>/dev/null || true
install -m 0644 "$ROOT/integrations/linux/pdfpixel_caja.py" \
    "$STAGE/usr/share/caja-python/extensions/pdfpixel.py" 2>/dev/null || true
# KDE Dolphin ServiceMenu + XFCE Thunar action (declarative).
mkdir -p "$STAGE/usr/share/kio/servicemenus"
install -m 0644 "$ROOT/integrations/linux/pdfpixel.desktop" \
    "$STAGE/usr/share/kio/servicemenus/pdfpixel.desktop" 2>/dev/null || true
cat > "$STAGE/DEBIAN/control" <<EOF
Package: pdfpixel
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: libnotify-bin
Recommends: python3-nautilus | python3-nemo | python3-caja
Maintainer: PDFPixel <noreply@pdfpixel.local>
Description: Right-click a PDF -> every page as a PNG image
 Adds a "Convert to Images" entry (All Pages / Custom Range) to GNOME Files,
 Nemo, Caja and Dolphin. Self-contained: bundles its PDF engine and dialog.
EOF
printf '#!/bin/sh\nset -e\nkillall nautilus nemo caja 2>/dev/null || true\n' \
    > "$STAGE/DEBIAN/postinst"
cp "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"
chmod 0755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"
dpkg-deb --build --root-owner-group "$STAGE" "$DIST/pdfpixel_${VERSION}_${ARCH}.deb"

# ---- .rpm (Fedora/RHEL/openSUSE) via fpm -----------------------------------
echo "==> Building .rpm (fpm)"
apt-get install -y -qq ruby ruby-dev build-essential rpm >/dev/null
gem install --no-document -q fpm >/dev/null 2>&1 || gem install --no-document fpm
printf '#!/bin/sh\nkillall nautilus nemo caja 2>/dev/null || true\n' > "$BUILD/rpm_post.sh"
fpm -s dir -t rpm -n pdfpixel -v "$VERSION" \
    --rpm-summary "Right-click a PDF -> every page as a PNG image" \
    --description "Adds a Convert to Images entry to GNOME Files / Nemo / Caja / Dolphin. Self-contained." \
    --license MIT --url "https://github.com/parikhvedant2003/PDFPixel" \
    --depends libnotify \
    --after-install "$BUILD/rpm_post.sh" --after-remove "$BUILD/rpm_post.sh" \
    --package "$DIST/pdfpixel-${VERSION}.x86_64.rpm" \
    -C "$STAGE" --exclude DEBIAN opt usr

# ---- AppImage (universal; runs on any glibc >= builder's) ------------------
echo "==> Building AppImage"
APPDIR="$BUILD/PDFPixel.AppDir"
mkdir -p "$APPDIR/usr/bin"
cp -r "$DIST/pdfpixel" "$APPDIR/usr/bin/pdfpixel"
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/pdfpixel/pdfpixel" "$@"
EOF
chmod +x "$APPDIR/AppRun"
cat > "$APPDIR/pdfpixel.desktop" <<EOF
[Desktop Entry]
Name=PDFPixel
Exec=pdfpixel
Icon=pdfpixel
Type=Application
Categories=Utility;Graphics;
Terminal=false
EOF
python3 - "$APPDIR/pdfpixel.png" <<'PY'
import sys
from PIL import Image, ImageDraw
img = Image.new("RGBA", (256, 256), (32, 96, 180, 255))
d = ImageDraw.Draw(img)
d.text((70, 110), "PDF", fill=(255, 255, 255, 255))
img.save(sys.argv[1])
PY
ARCH_AI="$(uname -m)"
wget -qO /tmp/appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH_AI}.AppImage"
chmod +x /tmp/appimagetool
ARCH="$ARCH_AI" /tmp/appimagetool --appimage-extract-and-run "$APPDIR" \
    "$DIST/PDFPixel-${VERSION}-${ARCH_AI}.AppImage"

echo "==> Artifacts:"
ls -lh "$DIST"/*.deb "$DIST"/*.rpm "$DIST"/*.AppImage
