#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genera una imagen de la pestaña Interacción para revisar el aspecto."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config
Config.load = lambda self: None          # no auto-cargar el último aparato

from PyQt5.QtWidgets import QApplication
from utils.search_index import SearchIndex, ComponentResult

app = QApplication(sys.argv)
from gui.app import SchematicSearchApp

w = SchematicSearchApp()
w._indexing = False
w.index.clear()
F = os.path.abspath(__file__)
comps = [
    ("R46", "10k",  "Resistencia",           [100, 100, 130, 110]),
    ("R47", "4k7",  "Resistencia",           [150, 100, 180, 110]),
    ("C10", "100n", "Condensador",           [200, 100, 225, 110]),
    ("C11", "47uF", "Condensador electrolit.", [250, 100, 280, 112]),
    ("Q2",  "",     "Transistor",            [305, 98, 335, 115]),
    ("D7",  "1N4148", "Diodo",               [150, 140, 175, 152]),
    ("U1",  "TL072", "Circuito integrado",   [210, 140, 265, 165]),
    ("R48", "220",  "Resistencia",           [305, 140, 335, 150]),
    ("K1",  "",     "Conector",              [400, 400, 430, 420]),
]
for des, val, typ, rect in comps:
    w.index.add_result(ComponentResult(designator=des, value=val, component_type=typ,
                                       file_path=F, page=1, location="",
                                       source_type="pdf", rects=[rect]))
w.populate_table(list(w.index.results))
w.table.selectRow(0)
w.cmb_auto.setCurrentText("Interacción")
app.processEvents()
w.tabs.setCurrentWidget(w.inter_panel)
app.processEvents()
w.resize(1460, 900)
w.show()
app.processEvents()
print("inter designator:", w.inter_panel._designator)
print("map size:", w.inter_panel.map.size().width(), w.inter_panel.map.size().height())
print("nodes:", [n[3].get("designator") for n in w.inter_panel.map._nodes])
print("tab actual:", w.tabs.tabText(w.tabs.currentIndex()))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interaccion_preview.png")
w.grab().save(out)
print("guardado:", out)
