# -*- coding: utf-8 -*-
"""Prueba de la ruta doble-clic -> visor y navegación desde conexiones."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp
from utils.search_index import ComponentResult

w = SchematicSearchApp()
dump = json.load(open("_idx_dump.json", encoding="utf-8"))
for d in dump:
    w.index.results.append(ComponentResult(**d))

ok = True

# 1) Buscar un componente escaneado con valor y abrirlo con doble clic
w.search_input.setText("C17")
w.search()
print("Resultados C17:", w.table.rowCount())
if w.table.rowCount():
    idx = w.table.model().index(0, 0)
    w.open_in_viewer(idx)
    app.processEvents()
    cur = w.pdf_viewer.page + 1
    nrects = len(w.pdf_viewer.highlight_rects.get(cur, []))
    print(f"  Visor abierto: pag {cur}/{w.pdf_viewer.total_pages}, "
          f"rects resaltados={nrects}, pestaña={w.tabs.currentIndex()}")
    if w.pdf_viewer.total_pages == 0 or nrects == 0 or w.tabs.currentIndex() != 0:
        ok = False
        print("  !! FALLO en la ruta de visor")

# 2) Fin de la tabla (row inválida) no debe romper
w.open_in_viewer(w.table.model().index(9999, 0))
print("open_in_viewer con fila inválida: OK")

# 3) Navegación por conexiones sin nets (debe avisar, no romper)
w.conn_panel.show_component("R46", w.index)
print("conn_panel sin nets: OK")

# 4) Cambio de pestañas
w.tabs.setCurrentIndex(1)
w.tabs.setCurrentIndex(2)
w.tabs.setCurrentIndex(0)
print("Cambio de pestañas: OK")

# 5) Selección de fila dispara el panel de nomenclatura
w.table.selectRow(0)
app.processEvents()
print("Nomenclatura (panel):", type(w.nomen_panel).__name__, "mostrado sin errores")

print("\nRESULTADO:", "TODO OK" if ok else "HAY FALLOS")
