#!/usr/bin/env bash
# build-icons.sh — Regenerate Cotrix application icons for macOS / Windows / Linux.
#
# Source of truth: src/includes/Icons/cotrix-app.svg
#   (dedicated full-bleed app-icon variant; the 96x96 cotrix.svg remains the
#    toolbar brand mark used by gui_theme.py and is NOT used here — it leaves
#    ~11% margin which renders undersized as an app icon.)
#
# Outputs (all overwritten in place):
#   src/artisan.icns                              — macOS app icon (10 sizes)
#   src/artisan.ico                               — Windows app icon (7 sizes)
#   src/artisan.png                               — Linux / window icon (512px)
#   src/debian/usr/share/pixmaps/artisan.png      — Debian package pixmap (512px)
#   src/includes/Icons/artisan-trayicon.svg       — macOS tray / notification (22px)
#   src/includes/Icons/artisan-trayicon-large.svg — larger tray variant (22px viewBox)
#
# Toolchain (all verified on a clean macOS install):
#   qlmanage  — macOS built-in SVG -> PNG rasterizer
#   sips      — macOS built-in PNG resizer / format converter
#   iconutil  — macOS built-in iconset <-> icns
#   Pillow    — venv Python imaging lib for assembling Windows .ico
#
# NOTE on Assets.car:
#   The legacy macOS adaptive "liquid glass" icon lived in src/Assets.car, compiled
#   from an Xcode asset catalog via `actool`. actool requires full Xcode (not just
#   Command Line Tools), so this script does NOT rebuild Assets.car. The mac spec
#   was updated to drop Assets.car and CFBundleIconName so the new artisan.icns is
#   the active icon. See docs/cotrix-icons.md for how to rebuild Assets.car later
#   on a machine that has Xcode installed.
#
# Usage:
#   cd src && bash build-icons.sh
set -euo pipefail

# --- locate repo paths -------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}"
ICONS_DIR="${SRC_DIR}/includes/Icons"
SOURCE_SVG="${ICONS_DIR}/cotrix-app.svg"

if [[ ! -f "${SOURCE_SVG}" ]]; then
    echo "ERROR: source SVG not found: ${SOURCE_SVG}" >&2
    exit 1
fi

# tools
for t in qlmanage sips iconutil; do
    if ! command -v "${t}" >/dev/null 2>&1; then
        echo "ERROR: required tool '${t}' not found (macOS built-in)" >&2
        exit 1
    fi
done

# venv python with Pillow (for .ico assembly)
VENV_PY="${SRC_DIR}/.venv/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
    VENV_PY="$(command -v python3)"
fi
if ! "${VENV_PY}" -c 'import PIL' >/dev/null 2>&1; then
    echo "ERROR: Pillow not importable via ${VENV_PY}; create src/.venv and 'pip install Pillow'" >&2
    exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "==> Working directory: ${WORK}"
echo "==> Source SVG:        ${SOURCE_SVG}"

# ----------------------------------------------------------------------------
# Step 1: rasterize cotrix.svg to a 1024x1024 master PNG via qlmanage, then
# downscale with sips for crisp anti-aliasing.
# ----------------------------------------------------------------------------
echo "==> [1/6] Rasterizing cotrix.svg -> 1024px master PNG"
qlmanage -t -s 1024 -o "${WORK}" "${SOURCE_SVG}" >/dev/null 2>&1
MASTER_RAW="${WORK}/$(basename "${SOURCE_SVG}").png"
if [[ ! -f "${MASTER_RAW}" ]]; then
    echo "ERROR: qlmanage did not produce a PNG" >&2
    exit 1
fi
MASTER="${WORK}/master_1024.png"
# qlmanage output may not be exactly 1024; normalize with sips resample
sips -z 1024 1024 "${MASTER_RAW}" --out "${MASTER}" >/dev/null
echo "    master: $(sips -g pixelWidth -g pixelHeight "${MASTER}" | tail -2 | tr '\n' ' ')"

# ----------------------------------------------------------------------------
# Step 2: build macOS .icns from a standard 10-size iconset
# ----------------------------------------------------------------------------
echo "==> [2/6] Building macOS artisan.icns (10 sizes)"
ICONSET="${WORK}/AppIcon.iconset"
mkdir -p "${ICONSET}"
# pairs of: output filename, edge size in px
declare -a SIZES=(
    "icon_16x16.png"            16
    "icon_16x16@2x.png"         32
    "icon_32x32.png"            32
    "icon_32x32@2x.png"         64
    "icon_128x128.png"         128
    "icon_128x128@2x.png"      256
    "icon_256x256.png"         256
    "icon_256x256@2x.png"      512
    "icon_512x512.png"         512
    "icon_512x512@2x.png"     1024
)
for ((i=0; i<${#SIZES[@]}; i+=2)); do
    name="${SIZES[$i]}"
    px="${SIZES[$((i+1))]}"
    sips -z "${px}" "${px}" "${MASTER}" --out "${ICONSET}/${name}" >/dev/null
done
iconutil -c icns "${ICONSET}" -o "${SRC_DIR}/artisan.icns"
echo "    wrote ${SRC_DIR}/artisan.icns ($(wc -c <"${SRC_DIR}/artisan.icns") bytes)"

# ----------------------------------------------------------------------------
# Step 3: build Windows .ico with Pillow (multi-size embedded)
# ----------------------------------------------------------------------------
echo "==> [3/6] Building Windows artisan.ico (7 sizes)"
ICO_SIZES=(16 24 32 48 64 128 256)
for px in "${ICO_SIZES[@]}"; do
    sips -z "${px}" "${px}" "${MASTER}" --out "${WORK}/win_${px}.png" >/dev/null
done
"${VENV_PY}" - "${WORK}" "${SRC_DIR}/artisan.ico" "${ICO_SIZES[@]}" <<'PYEOF'
import sys
from PIL import Image
work, out, *sizes = sys.argv[1:]
# Load largest as the base, then append smaller frames via thumbnail().
imgs = []
for px in sizes:
    im = Image.open(f"{work}/win_{px}.png").convert("RGBA")
    imgs.append((px, im))
base = Image.open(f"{work}/win_256.png").convert("RGBA")
base.save(
    out,
    format="ICO",
    sizes=[(int(px), int(px)) for px, _ in imgs],
)
print(f"    wrote {out}")
PYEOF
echo "    wrote ${SRC_DIR}/artisan.ico ($(wc -c <"${SRC_DIR}/artisan.ico") bytes)"

# ----------------------------------------------------------------------------
# Step 4: Linux PNGs (512x512) — app pixmap + runtime window icon
# ----------------------------------------------------------------------------
echo "==> [4/6] Building Linux PNGs (512px)"
LINUX_TARGETS=(
    "${SRC_DIR}/artisan.png"
    "${SRC_DIR}/debian/usr/share/pixmaps/artisan.png"
)
for tgt in "${LINUX_TARGETS[@]}"; do
    mkdir -p "$(dirname "${tgt}")"
    sips -z 512 512 "${MASTER}" --out "${tgt}" >/dev/null
    echo "    wrote ${tgt}"
done

# ----------------------------------------------------------------------------
# Step 5: tray icons — Cotrix mark without the background tile, sized for 22px.
# Two SVGs are emitted (regular + large) to match the legacy filenames used by
# artisanlib/notifications.py.
# ----------------------------------------------------------------------------
echo "==> [5/6] Writing Cotrix tray icons (artisan-trayicon*.svg)"
# Regular tray icon — Cotrix "C" + twin waves, no tile background.
read -r -d '' TRAY_SVG <<'SVG' || true
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
  <path d="M15.5 7.2c-1.05-.85-2.28-1.28-3.68-1.28C8.55 5.92 6 8.4 6 11.5s2.55 5.58 5.82 5.58c1.45 0 2.7-.45 3.75-1.32" fill="none" stroke="#3E7179" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M10.5 10.9c1.9-1.4 3.95-1.4 6.12 0" fill="none" stroke="#B46B5E" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M10.5 13.1c1.9 1.4 3.95 1.4 6.12 0" fill="none" stroke="#6E8C7A" stroke-width="1.8" stroke-linecap="round"/>
</svg>
SVG
# Large variant — same viewBox, slightly heavier strokes (matches legacy pattern
# where artisan-trayicon-large.svg scales the path up for higher-DPI trays).
read -r -d '' TRAY_SVG_LARGE <<'SVG' || true
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
  <path d="M16 6.6c-1.18-.95-2.55-1.43-4.12-1.43C8.06 5.17 5.2 7.95 5.2 11.5s2.86 6.33 6.68 6.33c1.62 0 3.02-.51 4.2-1.48" fill="none" stroke="#3E7179" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M10 10.6c2.13-1.57 4.42-1.57 6.85 0" fill="none" stroke="#B46B5E" stroke-width="2" stroke-linecap="round"/>
  <path d="M10 12.9c2.13 1.57 4.42 1.57 6.85 0" fill="none" stroke="#6E8C7A" stroke-width="2" stroke-linecap="round"/>
</svg>
SVG
printf '%s\n' "${TRAY_SVG}"       > "${ICONS_DIR}/artisan-trayicon.svg"
printf '%s\n' "${TRAY_SVG_LARGE}" > "${ICONS_DIR}/artisan-trayicon-large.svg"
echo "    wrote ${ICONS_DIR}/artisan-trayicon.svg"
echo "    wrote ${ICONS_DIR}/artisan-trayicon-large.svg"

# ----------------------------------------------------------------------------
# Step 6: summary
# ----------------------------------------------------------------------------
echo "==> [6/6] Done. Generated Cotrix icons:"
echo "    macOS:   ${SRC_DIR}/artisan.icns"
echo "    Windows: ${SRC_DIR}/artisan.ico"
echo "    Linux:   ${SRC_DIR}/artisan.png, ${SRC_DIR}/debian/usr/share/pixmaps/artisan.png"
echo "    Tray:    ${ICONS_DIR}/artisan-trayicon.svg, ${ICONS_DIR}/artisan-trayicon-large.svg"
echo ""
echo "    Reminder: artisan-mac.spec no longer bundles Assets.car (see docs/cotrix-icons.md)."
echo "    To roll back: git checkout -- src/artisan.icns src/artisan.ico src/artisan.png \\"
echo "                      src/debian/usr/share/pixmaps/artisan.png \\"
echo "                      src/includes/Icons/artisan-trayicon.svg \\"
echo "                      src/includes/Icons/artisan-trayicon-large.svg"
