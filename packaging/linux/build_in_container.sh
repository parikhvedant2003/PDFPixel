#!/usr/bin/env bash
# Build the Linux artifacts (.deb + universal .AppImage) inside an old-glibc
# container so the frozen binary runs on Debian 11+/Ubuntu 20.04+/RHEL 9+/etc.
# (glibc >= 2.31; older distros use the Flatpak or pip build instead.)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IMAGE="${1:-debian:11}"   # glibc 2.31
docker run --rm -v "$ROOT:/src" -w /src "$IMAGE" bash packaging/linux/build_linux.sh /src
# build/ is created as root inside the container; hand it back to the caller.
docker run --rm -v "$ROOT:/src" -w /src "$IMAGE" chown -R "$(id -u):$(id -g)" /src/build 2>/dev/null || true
