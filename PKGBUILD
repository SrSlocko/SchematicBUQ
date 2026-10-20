# Maintainer: SrSlocko
pkgname=schematicbuq
pkgver=1.1.0
pkgrel=1
pkgdesc="Buscador inteligente de esquemáticos con visor integrado, indexado inteligente y soporte para OCR y multidióma"
arch=('any')
url="https://github.com/SrSlocko/SchematicBUQ"
license=('MIT')
depends=('python-pyqt5' 'python-pymupdf' 'python-pytesseract' 'python-pillow'
         'python-opencv' 'python-qdarkstyle' 'python-pdfminer' 'python-pyqtgraph'
         'tesseract' 'tesseract-data-spa' 'tesseract-data-eng' 'poppler')
optdepends=('python-colorama: salida de color en consola'
            'python-requests: importar PDF desde una URL')
install=schematicbuq.install
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/SchematicBUQ-$pkgver"

    install -dm755 "$pkgdir/usr/share/schematicbuq"
    # Copia el programa excluyendo datos de usuario/caché (la app los crea en ~)
    tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='config.json' --exclude='logs' \
        --exclude='data/parse_cache.json' --exclude='database/devices.json' \
        --exclude='build' --exclude='dist' --exclude='tests' \
        -cf - . | (cd "$pkgdir/usr/share/schematicbuq" && tar -xf -)

    # Lanzador
    install -Dm755 schematicbuq "$pkgdir/usr/bin/schematicbuq"

    # Entrada de escritorio
    install -Dm644 schematicbuq.desktop \
        "$pkgdir/usr/share/applications/schematicbuq.desktop"

    # Icono
    if [ -f resources/icons/app.png ]; then
        install -Dm644 resources/icons/app.png \
            "$pkgdir/usr/share/pixmaps/schematicbuq.png"
    elif [ -f resources/icons/app.ico ]; then
        install -Dm644 resources/icons/app.ico \
            "$pkgdir/usr/share/pixmaps/schematicbuq.ico"
        if command -v convert >/dev/null 2>&1; then
            convert resources/icons/app.ico \
                "$pkgdir/usr/share/pixmaps/schematicbuq.png" 2>/dev/null || true
        fi
    fi

    # Licencia
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
