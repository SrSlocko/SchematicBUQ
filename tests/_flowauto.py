# -*- coding: utf-8 -*-
"""Flujo automático: al abrir la app debe cargar el aparato e indexar solo."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp

w = SchematicSearchApp()
w.resize(1440, 860)
w.show()
app.processEvents()

print("Aparato en el combo:", repr(w.cmb_devices.currentText()))
print("current_device     :", repr(w.current_device))
print("paths en cola      :", w.paths)

t0 = time.time()
while w._indexing and time.time() - t0 < 120:
    app.processEvents()
    time.sleep(0.05)
print(f"Auto-indexado: {time.time() - t0:.1f}s  componentes={len(w.index.results)}")

# Buscar R21
w.search_input.setText("R21")
w.search()
app.processEvents()
print(f"\nFilas para 'R21': {w.table.rowCount()}")
for i in range(w.table.rowCount()):
    print("   ", [w.table.item(i, c).text() for c in range(6)])

if w.table.rowCount():
    w.table.selectRow(0)
    app.processEvents()
    w.open_in_viewer(w.table.model().index(0, 0))
    app.processEvents()
    v = w.pdf_viewer
    pm = v.page_label.pixmap()
    print("\n--- VISOR ---")
    print("página:", v.page + 1, "/", v.total_pages, "zoom:", round(v.zoom, 3),
          "pestaña:", w.tabs.currentIndex())
    print("pixmap nulo?:", None if pm is None else pm.isNull())
    if pm is not None and not pm.isNull():
        img = pm.toImage()
        nw = tot = 0
        for y in range(0, img.height(), 4):
            for x in range(0, img.width(), 4):
                tot += 1
                c = img.pixelColor(x, y)
                if c.red() < 245 or c.green() < 245 or c.blue() < 245:
                    nw += 1
        print(f"píxeles no blancos: {nw}/{tot} ({100 * nw / max(tot,1):.1f}%)")
    print("rects de resaltado en la página:", v.highlight_rects.get(v.page + 1))
    w.grab().save(os.path.abspath("tests/_auto_visor.png"))
    print("captura:", os.path.abspath("tests/_auto_visor.png"))

print("FIN")
