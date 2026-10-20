# -*- coding: utf-8 -*-
"""Verificación final de la app: pestañas, auto-carga, búsqueda y visor."""
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
w.resize(1440, 860)
w.show()
app.processEvents()

print("Pestañas:")
for i in range(w.tabs.count()):
    print(f"   {i}: {w.tabs.tabText(i)}")
assert hasattr(w, "divider_panel"), "falta el panel del divisor"

t0 = time.time()
while w._indexing and time.time() - t0 < 120:
    app.processEvents()
    time.sleep(0.05)

print("\nAparato:", repr(w.current_device), "| componentes:", len(w.index.results),
      f"| indexado en {time.time()-t0:.2f}s")

# Buscar R21 y abrir
w.search_input.setText("R21")
w.search()
app.processEvents()
print("Resultados R21:", w.table.rowCount())
assert w.table.rowCount() > 0

w.table.selectRow(0)
app.processEvents()
w.open_in_viewer(w.table.model().index(0, 0))
app.processEvents()
pm = w.pdf_viewer.page_label.pixmap()
print("Visor -> pixmap válido:", pm is not None and not pm.isNull(),
      "| resaltados:", len(w.pdf_viewer.highlight_rects.get(1, [])))

# Probar la calculadora dentro de la app
w.divider_panel.ed_vin.setText("40")
w.divider_panel.ed_r1.setText("10k")
w.divider_panel.ed_r2.setText("4k7")
w.divider_panel.calculate()
print("Calculadora Vout:", w.divider_panel.ed_vout.text())

print("\nOK: la aplicación funciona correctamente")
