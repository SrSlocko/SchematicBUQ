# -*- coding: utf-8 -*-
"""Prueba de integración: MainWindow -> panel Componente al seleccionar una fila."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtCore import Qt
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp

w = SchematicSearchApp()
print("Ventana creada. Pestañas:", [w.tabs.tabText(i) for i in range(w.tabs.count())])

# ¿Existe la pestaña de componente?
titles = [w.tabs.tabText(i) for i in range(w.tabs.count())]
assert any("Componente" in t for t in titles), "Falta la pestaña Componente"

# Simulamos resultados en la tabla y seleccionamos una fila
class FakeR:
    designator = "R28"; value = "10k"; component_type = "resistencia"
    file_path = r"D:\schematicbuq\schematics\Ampeg_B2R\descarga (3).pdf"
    page = 2; source_type = "pdf"; device = "Ampeg_B2R"; rects = []

w.populate_table([FakeR()], "R28")
w.table.selectRow(0)
app.processEvents()

print("Designador en panel:", w.component_view._designator)
print("Tipo:", w.component_view.lbl_kind.text())
print("Valor:", w.component_view.lbl_value.text())
print("Símbolo dibujado:", w.component_view._symbol_pm is not None
      and not w.component_view._symbol_pm.isNull())
print("Panel de código visible:", w.component_view.grp_code.isVisible())
print("Texto del código:", w.component_view.lbl_code.text()[:80])

ok = (w.component_view.lbl_kind.text() == "Resistencia"
      and "Código de colores" in w.component_view.lbl_code.text())
print("Antes de reset -> ok:", ok)

# Limpiar espacio de trabajo debe vaciar el panel
w._reset_workspace("prueba")
print("Tras reset, designador:", repr(w.component_view._designator))

print("\nRESULTADO:", "TODO OK" if ok else "REVISAR")
