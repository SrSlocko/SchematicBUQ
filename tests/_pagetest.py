# -*- coding: utf-8 -*-
"""Prueba: lista «Componentes de esta hoja» del visor + ayuda + integración."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp
w = SchematicSearchApp()
w.resize(1400, 860)
w.show()
app.processEvents()

print("aparato:", w.current_device)
# Esperamos a que termine el indexado automático (usa la caché: debería ser rápido)
t0 = time.time()
while w._indexing and time.time() - t0 < 900:
    app.processEvents()
    time.sleep(0.05)
print(f"indexado en {time.time()-t0:.1f}s -> {len(w.index.results)} componentes")

w.search_input.setText("R46")
w.search()
t0 = time.time()
while w._indexing and time.time() - t0 < 900:
    app.processEvents()
    time.sleep(0.05)
if w.table.rowCount() == 0:
    w.search_input.setText("R")
    w.search()
    t0 = time.time()
    while w._indexing and time.time() - t0 < 900:
        app.processEvents()
        time.sleep(0.05)
print("filas:", w.table.rowCount())

if w.table.rowCount():
    w.table.setCurrentCell(0, 0)
    app.processEvents()
    w.open_in_viewer()
    app.processEvents()
    print("visor:", w.pdf_viewer.lbl_page.text(),
          "|", os.path.basename(w.pdf_viewer._doc_path))
    n = w.pdf_viewer.lst_page_components.count()
    print("componentes en la hoja:", n)
    print("muestra:", [w.pdf_viewer.lst_page_components.item(i).text()
                       for i in range(min(6, n))])
    if n:
        it = w.pdf_viewer.lst_page_components.item(0)
        des = it.data(0x0100)  # Qt.UserRole
        w.pdf_viewer._on_page_component_clicked(it)
        app.processEvents()
        print("pulsado:", des, "|", w.pdf_viewer.lbl_shown.text())
        print("pestaña activa (debe seguir siendo el visor):",
              w.tabs.tabText(w.tabs.currentIndex()))
        print("multímetro recibió:",
              w.multi_panel.lbl_title.text() if hasattr(w.multi_panel, 'lbl_title') else "n/a")
print("TODO OK")
