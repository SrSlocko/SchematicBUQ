#!/bin/bash
# Construye un AppImage autocontenido a partir del ejecutable de PyInstaller.
# Requiere: dist/SchematicBuq (generado por `pyinstaller SchematicBuq.spec`).
set -e

APP=SchematicBuq
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

APPDIR="build/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Binario principal
if [ ! -f "dist/$APP" ]; then
  echo "ERROR: falta dist/$APP (ejecuta antes: pyinstaller SchematicBuq.spec)" >&2
  exit 1
fi
cp "dist/$APP" "$APPDIR/usr/bin/$APP"
chmod +x "$APPDIR/usr/bin/$APP"

# Iconos y metadatos
if [ -f resources/icons/app.png ]; then
  cp resources/icons/app.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/schematicbuq.png"
elif [ -f resources/icons/app.ico ]; then
  # Intenta convertir el .ico si hay ImageMagick; si no, genera uno simple
  convert resources/icons/app.ico "$APPDIR/usr/share/icons/hicolor/256x256/apps/schematicbuq.png" 2>/dev/null || true
fi
if [ ! -f "$APPDIR/usr/share/icons/hicolor/256x256/apps/schematicbuq.png" ]; then
  python3 - <<'PY'
from PIL import Image
import os
os.makedirs("build/AppDir/usr/share/icons/hicolor/256x256/apps", exist_ok=True)
Image.new("RGBA", (256, 256), (37, 99, 235, 255)).save(
    "build/AppDir/usr/share/icons/hicolor/256x256/apps/schematicbuq.png")
PY
fi

cp schematicbuq.desktop "$APPDIR/schematicbuq.desktop"
cp schematicbuq.desktop "$APPDIR/usr/share/applications/schematicbuq.desktop"

# Icono también en la raíz del AppDir (lo exige appimagetool)
if [ -f "$APPDIR/usr/share/icons/hicolor/256x256/apps/schematicbuq.png" ]; then
  cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/schematicbuq.png" "$APPDIR/schematicbuq.png"
  cp "$APPDIR/schematicbuq.png" "$APPDIR/.DirIcon"
fi

# AppRun: arranca el ejecutable
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/SchematicBuq" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Descarga appimagetool si no está
if ! command -v appimagetool >/dev/null 2>&1; then
  ARCH="$(uname -m)"
  TOOL="appimagetool-${ARCH}.AppImage"
  wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/$TOOL" -O "build/$TOOL"
  chmod +x "build/$TOOL"
  APPIMAGETOOL="build/$TOOL"
else
  APPIMAGETOOL="appimagetool"
fi

VERSION="$(grep -m1 '^pkgver=' PKGBUILD | cut -d= -f2 | tr -d "'\" ")"
OUT="${APP}-${VERSION:-1.0.0}-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUT"
echo "AppImage generado: $OUT"
