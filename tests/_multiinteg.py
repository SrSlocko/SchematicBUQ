# -*- coding: utf-8 -*-
"""Integración: la pestaña MULTÍMETRO se abre al seleccionar un componente."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Aísla la configuración para no modificar la del usuario durante la prueba.
import tempfile
os.environ["SCHEMATICBUQ_CONFIG"] = os.path.join(tempfile.mkdtemp(), "config.json")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp

w = SchematicSearchApp()
titles = [w.tabs.tabText(i) for i in range(w.tabs.count())]
print("Pestañas:", titles)
assert any("Multímetro" in t for t in titles), "Falta la pestaña Multímetro"


class FakeR:
    designator = "R46"; value = "10k"; component_type = "resistencia"
    file_path = r"D:\schematicbuq\schematics\Ampeg_B2R\descarga (3).pdf"
    page = 2; source_type = "pdf"; device = "Ampeg_B2R"; rects = []


# 1) Rellenar la tabla NO debe cambiar de pestaña.
w.tabs.setCurrentIndex(0)
w.populate_table([FakeR()], "R46")
app.processEvents()
print("Tras rellenar la tabla, pestaña actual:", w.tabs.tabText(w.tabs.currentIndex()))
assert w.tabs.currentIndex() == 0, "La tabla abrió sola la pestaña Multímetro"

# 2) Seleccionar una fila SÍ debe abrir la pestaña Multímetro.
#    La pestaña automática es configurable; forzamos la opción por defecto
#    («Multímetro») para que la prueba no dependa de la preferencia guardada.
w.cmb_auto.setCurrentText("Multímetro")
app.processEvents()
w.table.selectRow(0)
app.processEvents()
cur = w.tabs.tabText(w.tabs.currentIndex())
print("Tras seleccionar fila, pestaña actual:", cur)
print("Panel multímetro designador:", w.multi_panel._designator)
print("Título:", w.multi_panel.lbl_title.text())
print("Botones:", [b.text().strip() for b in w.multi_panel._buttons])
ok_tab = w.tabs.currentWidget() is w.multi_panel
ok_data = w.multi_panel._designator == "R46"
print("Verificador visible:", w.multi_panel.box_check.isVisible())

# 3) Probar el verificador interactivo (corto).
pressed = False
for i, b in enumerate(w.multi_panel._buttons):
    if "corto" in b.text().lower():
        w.multi_panel._on_state(i)
        pressed = True
        break
res = w.multi_panel.lbl_result.text()
print("Veredicto tras pulsar 'En corto':", res[:120].replace("\n", " "))
ok_verdict = pressed and "CORTOCIRCUITO" in res

# 4) Reset limpia el panel.
w._reset_workspace("prueba")
app.processEvents()
print("Tras reset, designador:", repr(w.multi_panel._designator))
print("Tras reset, título:", w.multi_panel.lbl_title.text())
ok_reset = w.multi_panel._designator == ""

print("\nRESULTADO:", "TODO OK" if (ok_tab and ok_data and ok_verdict and ok_reset)
      else "REVISAR")
