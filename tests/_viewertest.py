# -*- coding: utf-8 -*-
"""Prueba del visor mejorado (zoom, pan, mini-mapa, centrado)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.widgets.pdf_viewer import PDFViewer

PDF = r"D:\schematicbuq\schematics\Ampeg_B2R\descarga (3).pdf"
v = PDFViewer()
v.resize(1100, 700)
v.show()
app.processEvents()

ok = v.load_pdf(PDF, highlight_words=["R46"], highlight_rects={}, page=1)
app.processEvents()
print("cargado:", ok, "| páginas:", v.total_pages, "| zoom:", round(v.zoom, 3))
print("página mostrada:", v.lbl_page.text())
print("etiqueta componente:", repr(v.lbl_shown.text()))
print("miniatura:", v.minimap._thumb is not None and not v.minimap._thumb.isNull())
print("recuadros resaltados:", len(v._last_rects))

v.step_zoom(+1); app.processEvents()
z1 = v.zoom
v.step_zoom(-1); app.processEvents()
print("zoom tras + y -:", round(z1, 3), "->", round(v.zoom, 3))

v.fit_page(); app.processEvents()
print("fit_page ->", round(v.zoom, 3))
v.fit_width(); app.processEvents()
print("fit_width ->", round(v.zoom, 3))

v.next_page(); app.processEvents()
print("tras siguiente:", v.lbl_page.text())
v.go_to_page(1); app.processEvents()
print("go_to_page(1):", v.lbl_page.text())

v.center_on_highlight()
print("centrado: hscroll=", v.scroll.horizontalScrollBar().value(),
      "vscroll=", v.scroll.verticalScrollBar().value())

v.minimap.jump.emit(0.8, 0.7); app.processEvents()
print("tras salto en mini-mapa: hscroll=", v.scroll.horizontalScrollBar().value())

v.close_pdf()
print("tras cerrar:", v.lbl_page.text(), "| doc:", v.doc)
print("TODO OK")
