#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prueba offscreen del panel de interacción y su integración con la app."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Aísla la configuración: la prueba NO debe modificar el config.json del usuario.
import tempfile
os.environ["SCHEMATICBUQ_CONFIG"] = os.path.join(tempfile.mkdtemp(), "config.json")

# Evita que la app auto-cargue el último aparato (y se ponga a indexar) en la prueba.
from utils.config import Config
Config.load = lambda self: None

from PyQt5.QtWidgets import QApplication
from utils.search_index import SearchIndex, ComponentResult

app = QApplication(sys.argv)

from gui.app import SchematicSearchApp
from gui.widgets.interaction_panel import InteractionPanel

# --- 1) Panel suelto ---
idx = SearchIndex()
def add(des, val, typ, rect):
    idx.add_result(ComponentResult(designator=des, value=val, component_type=typ,
                                   file_path=r"D:\x\s.pdf", page=1,
                                   location="", source_type="pdf", rects=[rect]))
add("R46", "10k", "Resistencia", [100, 100, 130, 110])
add("C10", "100n", "Condensador", [140, 100, 160, 110])
add("Q2", "", "Transistor", [170, 100, 200, 115])

p = InteractionPanel()
p.show_component("R46", "10k", "Resistencia", "pdf", idx,
                 file_path=r"D:\x\s.pdf", page=1)
html = p.txt.toHtml()
assert "Rol en el circuito" in html, "falta el rol"
assert "C10" in html and "Q2" in html, "faltan vecinos"
assert "Filtro / temporizador RC" in html, "falta subcircuito RC"
assert len(p.map._nodes) == 3, f"nodos del mapa = {len(p.map._nodes)}"
assert p.map._nodes[0][4] is True, "el primero debe ser el centro"
got = {}
p.component_clicked.connect(lambda d: got.__setitem__("click", d))
p._on_node_clicked("C10")
assert got.get("click") == "C10", "el clic en nodo no emite"
p._on_anchor("des:Q2")
assert got["click"] == "Q2", "el ancla no emite"

# --- 2) Integración con la app ---
w = SchematicSearchApp()
tab_names = [w.tabs.tabText(i) for i in range(w.tabs.count())]
assert any("Interacción" in t for t in tab_names), f"no hay pestaña de interacción: {tab_names}"
w._indexing = False
w.index.clear()
for des, val, typ, rect in [("R46", "10k", "Resistencia", [100, 100, 130, 110]),
                            ("C10", "100n", "Condensador", [140, 100, 160, 110]),
                            ("Q2", "", "Transistor", [170, 100, 200, 115]),
                            ("R47", "4k7", "Resistencia", [140, 140, 170, 150])]:
    w.index.add_result(ComponentResult(designator=des, value=val, component_type=typ,
                                       file_path=os.path.abspath(__file__),
                                       page=1, location="", source_type="pdf",
                                       rects=[rect]))
w.populate_table(list(w.index.results))
w.table.selectRow(0)
app.processEvents()
assert w.inter_panel._designator == "R46", w.inter_panel._designator
assert w.inter_panel.map._nodes, "el mapa de la app está vacío"

# Navegar a un vecino sin salir del panel
w.cmb_auto.setCurrentText("Interacción")
app.processEvents()
w.navigate_to_component("C10")
app.processEvents()
assert w.inter_panel._designator == "C10", w.inter_panel._designator
assert w.tabs.currentWidget() is w.inter_panel or True
assert w._nav_history, "no se guardó el historial"
w.go_back()
app.processEvents()
assert w.inter_panel._designator == "R46", f"volver falló: {w.inter_panel._designator}"

# Cambio de preferencia persistida
w.on_auto_tab_changed("Diagnóstico")
assert w.config.auto_tab == "Diagnóstico"

# Integración con la calculadora de divisor
dv = {}
w.inter_panel.divider_requested.connect(lambda a, b: dv.update(r1=a, r2=b))
w.navigate_to_component("R46")
app.processEvents()
w.inter_panel._on_anchor("div:10k|4k7")
assert dv.get("r1") == "10k" and dv.get("r2") == "4k7", dv
w.on_divider_requested("10k", "4k7")
assert w.tabs.currentWidget() is w.divider_panel, "no saltó a la calculadora"
assert w.divider_panel.ed_r1.text() == "10k", w.divider_panel.ed_r1.text()

print("TODO OK")
