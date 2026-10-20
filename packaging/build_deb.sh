#!/bin/bash
# Construye un paquete .deb para Debian/Ubuntu a partir del código fuente.
# Uso: ./packaging/build_deb.sh [version]
set -e

VERSION="${1:-1.0.0}"
PKG=schematicbuq
ARCH=all
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

ROOT="build/deb/${PKG}_${VERSION}_${ARCH}"
rm -rf "$ROOT"
mkdir -p "$ROOT/DEBIAN"
mkdir -p "$ROOT/usr/share/${PKG}"
mkdir -p "$ROOT/usr/bin"
mkdir -p "$ROOT/usr/share/applications"
mkdir -p "$ROOT/usr/share/pixmaps"

# Copia el programa (sin datos de usuario ni cachés)
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='config.json' --exclude='logs' --exclude='build' --exclude='dist' \
    --exclude='data/parse_cache.json' --exclude='database/devices.json' \
    -cf - . | (cd "$ROOT/usr/share/${PKG}" && tar -xf -)

# Lanzador
install -Dm755 schematicbuq "$ROOT/usr/bin/schematicbuq"

# Icono
if [ -f resources/icons/app.png ]; then
  cp resources/icons/app.png "$ROOT/usr/share/pixmaps/schematicbuq.png"
elif [ -f resources/icons/app.ico ]; then
  convert resources/icons/app.ico "$ROOT/usr/share/pixmaps/schematicbuq.png" 2>/dev/null || true
fi

# .desktop
cp schematicbuq.desktop "$ROOT/usr/share/applications/schematicbuq.desktop"

cat > "$ROOT/DEBIAN/control" <<EOF
Package: ${PKG}
Version: ${VERSION}
Section: electronics
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-pyqt5, python3-pymupdf, python3-pytesseract, python3-pil, python3-opencv, python3-requests, tesseract-ocr, tesseract-ocr-spa, tesseract-ocr-eng, poppler-utils
Recommends: python3-qdarkstyle, python3-pyqtgraph
Maintainer: SrSlocko <https://github.com/SrSlocko>
Homepage: https://github.com/SrSlocko/SchematicBUQ
Description: Buscador inteligente de esquematicos con visor, indexado y OCR
 Aplicacion de escritorio para buscar componentes en esquematicos
 electronicos (PDF, imagenes, netlists), verlos en un visor integrado y
 seguir sus conexiones. Soporta OCR para esquemas escaneados.
EOF

dpkg-deb --build --root-owner-group "$ROOT"
mv "build/deb/${PKG}_${VERSION}_${ARCH}.deb" "./${PKG}_${VERSION}_${ARCH}.deb"
echo "Paquete .deb generado: ${PKG}_${VERSION}_${ARCH}.deb"
