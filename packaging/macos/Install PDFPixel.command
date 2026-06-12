#!/bin/bash
# Double-click to install PDFPixel: copies the app to /Applications/PDFPixel and
# the two Quick Actions to ~/Library/Services.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing PDFPixel binary -> /Applications/PDFPixel"
rm -rf "/Applications/PDFPixel"
mkdir -p "/Applications/PDFPixel"
cp -R "$DIR/PDFPixel/." "/Applications/PDFPixel/"

echo "Installing Quick Actions -> ~/Library/Services"
mkdir -p "$HOME/Library/Services"
for wf in PDFPixel-AllPages.workflow PDFPixel-CustomRange.workflow; do
    rm -rf "$HOME/Library/Services/$wf"
    cp -R "$DIR/$wf" "$HOME/Library/Services/"
done

# Clear quarantine (unsigned build) and refresh the Services menu.
xattr -dr com.apple.quarantine "/Applications/PDFPixel" 2>/dev/null || true
xattr -dr com.apple.quarantine "$HOME/Library/Services/PDFPixel-AllPages.workflow" 2>/dev/null || true
xattr -dr com.apple.quarantine "$HOME/Library/Services/PDFPixel-CustomRange.workflow" 2>/dev/null || true
/System/Library/CoreServices/pbs -flush 2>/dev/null || true

echo "Done. Right-click a PDF in Finder -> Quick Actions -> PDFPixel."
