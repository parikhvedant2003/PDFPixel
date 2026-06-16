# Distributing PDFPixel on Linux

What each channel reaches, whether it carries the right-click file-manager
integration, and the steps to publish it.

| Channel | Format | Right-click menu? | Auto-update | Status |
|---|---|---|---|---|
| GitHub Release | `.deb` `.rpm` `.AppImage` | `.deb`/`.rpm`: yes · AppImage: no | no | shipping |
| PyPI | wheel/sdist (`pip install`) | no (CLI only) | `pip install -U` | wired (this repo) |
| AUR | source pkg | yes | `pacman`/helper | scaffolded |
| Flatpak / Flathub | sandboxed app | no (Open With only) | yes | scaffolded |
| Snap | sandboxed app | no | yes | not started |

Sandbox rule of thumb: only **natively installed** packages (`.deb`, `.rpm`, AUR)
can drop a file-manager extension into the host and give the inline
"Convert to Images" submenu. Flatpak/Snap are sandboxed → "Open With" + all-pages
conversion only.

---

## PyPI  (`pip install pdfpixel`)

Wired in `.github/workflows/build.yml` (`publish-pypi` job) via Trusted Publishing.

One-time setup, before the first `v*` tag:
1. https://pypi.org/manage/account/publishing/ → add a **pending publisher**:
   project `pdfpixel`, owner `parikhvedant2003`, repo `PDFPixel`,
   workflow `build.yml`, environment `pypi`.
2. GitHub repo → Settings → Environments → create environment `pypi`.

Per release: bump `__version__` in `pdfpixel/__init__.py` (single source of truth —
`pyproject.toml` reads it dynamically), tag `vX.Y.Z`, push. The job builds + uploads
automatically. (PyPI rejects re-uploading a version that already exists — never reuse a tag.)

## AUR  (`yay -S pdfpixel`)

Source package in `packaging/linux/aur/` — native install, full right-click menu.

Publish:
1. Register an AUR account + add your SSH key.
2. `git clone ssh://aur@aur.archlinux.org/pdfpixel.git`
3. Copy `PKGBUILD` in; `cd` there and run `updpkgsums` (pins the source
   `sha256sums`), then `makepkg --printsrcinfo > .SRCINFO`.
4. Test in a clean chroot: `makepkg -si` (or `extra-x86_64-build`).
5. `git add PKGBUILD .SRCINFO && git commit && git push`.

Per release: bump `pkgver`, reset `pkgrel=1`, rerun steps 3–5.

## Flatpak / Flathub

Manifest + desktop + appstream in `packaging/linux/flatpak/`.

Local test:
```
flatpak install -y flathub org.freedesktop.Platform//24.08 org.freedesktop.Sdk//24.08
flatpak-builder --user --install --force-clean build-dir \
    packaging/linux/flatpak/io.github.parikhvedant2003.PDFPixel.yaml
flatpak run io.github.parikhvedant2003.PDFPixel some.pdf
```

To submit to Flathub:
1. Replace the `dir` source with a tagged git/archive source.
2. Pre-generate offline pip sources (`flatpak-pip-generator pypdfium2 pillow`) —
   Flathub build sandboxes have no network.
3. Add ≥1 screenshot to the metainfo.
4. PR the manifest to https://github.com/flathub/flathub (new-submissions).

## Snap  (not started)

Lowest priority — overlaps AppImage (universal, no install) and the Flatpak.
Add a `snapcraft.yaml` only if users ask for Snap Store auto-updates.

## arm64 (applies to every binary channel above)

Wired. `build-linux` in `build.yml` runs a matrix: `ubuntu-latest` (amd64) +
`ubuntu-24.04-arm` (aarch64). Docker pulls the debian:11 image for each runner's
arch, so every release ships both `amd64` and `arm64` `.deb`/`.rpm`/AppImage
(artifacts named `pdfpixel-linux-amd64` / `pdfpixel-linux-arm64`).
