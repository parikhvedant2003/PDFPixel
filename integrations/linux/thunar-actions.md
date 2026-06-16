# XFCE / Thunar custom actions

Thunar stores custom actions per-user in `~/.config/Thunar/uca.xml`, so they
can't be dropped in by a package. Add them once via **Thunar → Edit → Configure
custom actions… → +**, or append these to `~/.config/Thunar/uca.xml` (inside
the top-level `<actions>` element) and restart Thunar (`thunar -q`).

```xml
<action>
  <icon>application-pdf</icon>
  <name>PDFPixel: All Pages → PNG</name>
  <command>/usr/bin/pdfpixel %F</command>
  <description>PDF tools by PDFPixel — All Pages → PNG</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
<action>
  <icon>application-pdf</icon>
  <name>PDFPixel: First Page → PNG</name>
  <command>/usr/bin/pdfpixel --pages 1 %f</command>
  <description>PDF tools by PDFPixel — First Page → PNG</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
<action>
  <icon>application-pdf</icon>
  <name>PDFPixel: Custom…</name>
  <command>/usr/bin/pdfpixel --ask %f</command>
  <description>PDF tools by PDFPixel — Custom…</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
<action>
  <icon>application-pdf</icon>
  <name>PDFPixel: Merge selected PDFs</name>
  <command>/usr/bin/pdfpixel merge %F</command>
  <description>PDF tools by PDFPixel — Merge selected PDFs</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
<action>
  <icon>application-pdf</icon>
  <name>PDFPixel: Split into pages</name>
  <command>/usr/bin/pdfpixel split %f</command>
  <description>PDF tools by PDFPixel — Split into pages</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
<action>
  <icon>application-pdf</icon>
  <name>PDFPixel: Compress</name>
  <command>/usr/bin/pdfpixel compress %f</command>
  <description>PDF tools by PDFPixel — Compress</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
```

(If you installed the AppImage instead of the `.deb`, replace `/usr/bin/pdfpixel`
with the path to the AppImage.)
