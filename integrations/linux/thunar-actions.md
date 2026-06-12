# XFCE / Thunar custom actions

Thunar stores custom actions per-user in `~/.config/Thunar/uca.xml`, so they
can't be dropped in by a package. Add them once via **Thunar → Edit → Configure
custom actions… → +**, or append these to `~/.config/Thunar/uca.xml` (inside
the top-level `<actions>` element) and restart Thunar (`thunar -q`).

```xml
<action>
  <icon>application-pdf</icon>
  <name>Convert to Images (All Pages)</name>
  <command>/usr/bin/pdfpixel %F</command>
  <description>Render each PDF page to a PNG</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
<action>
  <icon>application-pdf</icon>
  <name>Convert to Images (Custom Range)</name>
  <command>/usr/bin/pdfpixel --ask %f</command>
  <description>Render a chosen page range to PNGs</description>
  <patterns>*.pdf</patterns>
  <other-files/>
</action>
```

(If you installed the AppImage instead of the `.deb`, replace `/usr/bin/pdfpixel`
with the path to the AppImage.)
