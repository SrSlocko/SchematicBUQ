# -*- coding: utf-8 -*-
"""Prueba del visor con rects guardados (escaneos) y comportamiento GUI."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp
from utils.search_index import ComponentResult

w = SchematicSearchApp()

# Cargar el dump (sin re-OCR)
dump = json.load(open("_idx_dump.json", encoding="utf-8"))
for d in dump:
    w.index.results.append(ComponentResult(**d))

print("Componentes cargados:", len(w.index.results))

# 1) Buscar un componente de un escaneo
escan = [r for r in w.index.results if r.rects and "descarga.pdf" in r.file_path]
print("Con rects en escaneo:", len(escan))

# 2) Buscar R46 y probar el mapa de resaltado
w.search_input.setText("R46")
w.search()
print("Resultados R46:", w.table.rowCount())

# 3) Abrir en visor el primer resultado con rects
target = next((r for r in w.index.results if r.rects and r.source_type == 'pdf'), None)
if target:
    print(f"\nAbriendo {target.designator} ({target.value}) en {os.path.basename(target.file_path)} pag {target.page}")
    hmap = w._highlight_map_for(target.file_path, target.designator)
    print("Mapa de resaltado:", {k: len(v) for k, v in hmap.items()})
    w.pdf_viewer.load_pdf(target.file_path, highlight_words=[target.designator],
                          highlight_rects=hmap)
    w.pdf_viewer.go_to_page(target.page)
    print("Visor: pagina actual", w.pdf_viewer.page + 1, "/", w.pdf_viewer.total_pages)
    print("Rects que se dibujarán:", len(w.pdf_viewer.highlight_rects.get(w.pdf_viewer.page + 1, [])))

# 4) Probar el panel de conexiones
w.conn_panel.show_component(target.designator if target else "R46", w.index)
print("\nPanel conexiones OK. Nets:", w.conn_panel.list_nets.count(),
      "Conectados:", w.conn_panel.list_conn.count())

# 5) Probar búsqueda vacía
w.search_input.setText("")
w.search()
print("Búsqueda vacía -> filas:", w.table.rowCount())

# 6) Probar búsqueda inexistente
w.search_input.setText("ZZ999")
w.search()
print("Búsqueda 'ZZ999' -> filas:", w.table.rowCount())

# 7) Probar búsqueda por valor
w.search_input.setText("47K")
w.search()
print("Búsqueda por valor '47K' -> filas:", w.table.rowCount())

# 8) Probar jump
if target:
    w.jump_to_component(target.designator)
    print("jump_to_component('" + target.designator + "') -> filas:", w.table.rowCount())

print("\nTODO OK")
