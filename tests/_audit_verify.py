# -*- coding: utf-8 -*-
"""Verificación de las correcciones de la auditoría QA."""
import os, sys, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["SCHEMATICBUQ_CONFIG"] = os.path.join(tempfile.mkdtemp(), "config.json")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

ok = {}

# --- 1) DeviceDB: coincidencia exacta y sin pisar datos ---
from database.device_db import DeviceDB
tmp = tempfile.mkdtemp()
db = DeviceDB(db_path=os.path.join(tmp, "d.json"))
db.add_device("Ampeg_B2R", os.path.join(tmp, "Ampeg_B2R"))
db.set_components("Ampeg_B2R", 575)
db.add_device("B2R", os.path.join(tmp, "B2R"))
ok["find exacto 'B2R'"] = db.find_device("B2R")["name"] == "B2R"
ok["find exacto 'ampeg_b2r' (mayúsculas)"] = db.find_device("ampeg_b2r")["name"] == "Ampeg_B2R"
ok["find desconocido -> None"] = db.find_device("Inexistente_XYZ") is None
ok["find '' -> None"] = db.find_device("") is None
# add_device sobre uno existente NO debe reiniciar el contador
db.add_device("Ampeg_B2R", os.path.join(tmp, "Ampeg_B2R"))
ok["add_device preserva components_indexed"] = db.find_device("Ampeg_B2R")["components_indexed"] == 575
ok["has_device"] = db.has_device("B2R") and not db.has_device("Nope")

# --- 2) search_index: ida y vuelta completa (componentes + nets + aparato) ---
from utils.search_index import SearchIndex, ComponentResult
idx = SearchIndex()
idx.add_result(ComponentResult("R1", "10k", "Resistencia", "/x/a.pdf", 1, "",
                              source_type="pdf", rects=[[1, 2, 3, 4]], device="A"))
idx.register_connection("OUT", "R1")
idx.register_connection("OUT", "C2")
idx.register_file_device("/x/a.pdf", "A")
dump = os.path.join(tmp, "idx.json")
idx.export_json(dump)
idx2 = SearchIndex()
idx2.load_json(dump)
ok["round-trip resultados"] = [r.to_dict() for r in idx2.results] == [r.to_dict() for r in idx.results]
ok["round-trip nets"] = idx2.connections == idx.connections
ok["round-trip device_of_file"] = idx2.device_of_file == idx.device_of_file
ok["load_json lectura de formato antiguo"] = True
legacy = os.path.join(tmp, "legacy.json")
json.dump([r.to_dict() for r in idx.results], open(legacy, "w", encoding="utf-8"))
idx3 = SearchIndex(); idx3.load_json(legacy)
ok["load_json formato antiguo"] = len(idx3.results) == 1

# --- 3) Panel de nomenclatura: clear() ---
from gui.widgets.nomenclature_panel import NomenclaturePanel
np_ = NomenclaturePanel()
np_.show_info("R46")
np_.clear()
ok["nomen clear designador"] = np_.lbl_designator.text() == "Designador: -"
ok["nomen clear campos"] = (np_.txt_what.toPlainText() == ""
                            and np_.txt_trouble.toPlainText() == ""
                            and np_.txt_sym.toPlainText() == "")

# --- 4) App: aparato sin carpeta no deja el índice de otro aparato ---
from utils.config import Config
Config.load = lambda self: None
from gui.app import SchematicSearchApp
from database.device_db import DeviceDB as _DeviceDB
w = SchematicSearchApp()
# Aislamos la base de datos de aparatos: la prueba no debe tocar la real.
w.device_db = _DeviceDB(db_path=os.path.join(tmp, "devices_test.json"))
w.reload_devices()
w._indexing = False
w.index.clear()
w.index.add_result(ComponentResult("R1", "10k", "Resistencia", "/old/a.pdf", 1, "",
                                   source_type="pdf", device="AparatoViejo"))
w.populate_table(list(w.index.results))
# Creamos un aparato sin carpeta y lo seleccionamos
w.device_db.add_device("Sin Carpeta", os.path.join(tmp, "noexiste"))
w.reload_devices()
i = w.cmb_devices.findText("Sin Carpeta")
w.cmb_devices.setCurrentIndex(i)
app.processEvents()
ok["cambio a aparato sin carpeta limpia índice ajeno"] = len(w.index.results) == 0
ok["cambio a aparato sin carpeta limpia tabla"] = w.table.rowCount() == 0

print()
for k, v in ok.items():
    print(f"  [{'OK ' if v else 'FALLA'}] {k}")
print("\nRESULTADO:", "TODO OK" if all(ok.values()) else "REVISAR")
sys.exit(0 if all(ok.values()) else 1)
