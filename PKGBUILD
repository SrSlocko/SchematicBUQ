# Maintainer: SrSlocko
pkgname=schematicbuq
pkgver=1.0.0
pkgrel=1
pkgdesc="Buscador inteligente de esquemáticos con visor integrado, indexado inteligente y soporte para OCR"
arch=('any')
url="https://github.com/SrSlocko/SchematicBUQ"
license=('MIT')
depends=('python-pyqt5' 'python-pymupdf' 'python-pytesseract' 'python-pillow' 'python-opencv' 'tesseract' 'tesseract-data-spa' 'tesseract-data-eng' 'poppler')
optdepends=('python-qdarkstyle' 'python-pdfminer.six' 'python-requests' 'python-pyqtgraph')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/heads/main.tar.gz")
sha256sums=('SKIP')

install=schematicbuq.install

package() {
    cd "$srcdir/SchematicBUQ-main"
    install -dm755 "$pkgdir/usr/share/schematicbuq"
    cp -r . "$pkgdir/usr/share/schematicbuq/"

    # Launcher
    install -Dm755 "$srcdir/../schematicbuq" "$pkgdir/usr/bin/schematicbuq"
    
    # Desktop entry
    install -Dm644 "$srcdir/SchematicBUQ-main/schematicbuq.desktop" "$pkgdir/usr/share/applications/schematicbuq.desktop"
    
    # Icon (try to use app.ico if exists, else create symlink)
    if [ -f "$srcdir/SchematicBUQ-main/resources/icons/app.ico" ]; then
        install -Dm644 "$srcdir/SchematicBUQ-main/resources/icons/app.ico" "$pkgdir/usr/share/pixmaps/schematicbuq.ico"
        # Try to install PNG if exists
        if [ -f "$srcdir/SchematicBUQ-main/resources/icons/app.png" ]; then
            install -Dm644 "$srcdir/SchematicBUQ-main/resources/icons/app.png" "$pkgdir/usr/share/pixmaps/schematicbuq.png"
        else
            # Create PNG from ICO using convert if available
            if command -v convert >/dev/null 2>&1; then
                convert "$srcdir/SchematicBUQ-main/resources/icons/app.ico" "$pkgdir/usr/share/pixmaps/schematicbuq.png" 2>/dev/null || true
            fi
        fi
    fi
}
