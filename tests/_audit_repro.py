# -*- coding: utf-8 -*-
"""Reproducción de fallos candidatos detectados en la auditoría."""
import os, sys, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

print("=" * 60)
print("A) DeviceDB.find_device: coincidencia por subcadena")
print("=" * 60)
from database.device_db import DeviceDB

tmp = tempfile.mkdtemp()
db = DeviceDB(db_path=os.path.join(tmp, "devices.json"))
db.add_device("Ampeg_B2R", os.path.join(tmp, "Ampeg_B2R"))
db.add_device("B2R", os.path.join(tmp, "B2R"))

print("  aparatos:", [d["name"] for d in db.get_devices()])
r = db.find_device("B2R")
print("  find_device('B2R') ->", r["name"] if r else None, " (esperado: B2R)")
r2 = db.find_device("Ampeg_B2R")
print("  find_device('Ampeg_B2R') ->", r2["name"] if r2 else None, " (esperado: Ampeg_B2R)")

# Escenario real: 'add_folder' con una carpeta cuya base es subcadena de un aparato
print("\n  -> add_folder con carpeta 'Amp':")
name = "Amp"
if name and not db.find_device(name):
    db.add_device(name, os.path.join(tmp, name))
    print("     registrado 'Amp'")
else:
    print("     BUG: NO se registró 'Amp' (find_device lo confundió con",
          db.find_device(name)["name"] + ")")

print("\n" + "=" * 60)
print("B) NetlistParser: extracción de valores")
print("=" * 60)
from utils.netlist_parser import NetlistParser

kicad = '''(export (version D)
  (components
    (comp (ref R1) (value "10k") (footprint "R_0805"))
    (comp (ref C2) (value "100nF") (footprint "C_0805"))
    (comp (ref U1) (value "LM358") (footprint "SOIC-8")))
  (nets
    (net (code 1) (name "GND") (node (ref R1) (pin 2)) (node (ref C2) (pin 2)))
    (net (code 2) (name "OUT") (node (ref U1) (pin 1)) (node (ref C2) (pin 1)))))
'''
p = os.path.join(tmp, "k.net")
open(p, "w", encoding="utf-8").write(kicad)
np = NetlistParser()
res = np.parse(p)
print("  KiCad .net ->", [(r.designator, r.value) for r in res])
print("  valores extraídos:", sum(1 for r in res if r.value), "/", len(res))

spice = """* netlist
R1 N001 N002 10k
C1 N002 0 100n
Q1 N003 N002 N001 BC547
"""
p2 = os.path.join(tmp, "s.cir")
open(p2, "w", encoding="utf-8").write(spice)
res2 = np.parse(p2)
print("  SPICE .cir ->", [(r.designator, r.value) for r in res2])
print("  valores extraídos:", sum(1 for r in res2 if r.value), "/", len(res2))

print("\nFIN")
