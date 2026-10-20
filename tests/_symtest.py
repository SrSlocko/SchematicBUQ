# -*- coding: utf-8 -*-
"""Prueba de símbolos y código de colores."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from utils.component_symbols import (
    resistor_color_code, component_kind, kind_name, symbol_pixmap,
    parse_resistance, format_ohms, KIND_BY_PREFIX
)

print("=== Código de colores ===")
casos = ["470", "1k", "4.7k", "4k7", "10k", "100", "220", "4700", "100k",
         "1M", "2M2", "0.22", "4.7", "47", "5.6k", "499"]
for v in casos:
    cc = resistor_color_code(v)
    if cc:
        print(f"  {v:>6} = {format_ohms(cc['ohms']):>9}  ->  {cc['summary']:<34} "
              f"{cc['tolerance_text']}")
    else:
        print(f"  {v:>6} -> (no representable)")

print("\n=== Valor -> ohmios ===")
for v in ["4k7", "10K", "2M2", "0R22", "4.7k", "470"]:
    print(f"  {v:>6} -> {parse_resistance(v)}")

print("\n=== Tipo por designador ===")
for d in ["R28", "RN1", "C12", "CP5", "D3", "ZD17", "LED2", "Q1", "U5", "IC2",
          "J1", "SW1", "F1", "T1", "Y1", "L2", "LS1", "BT1", "RV1", "H2", "X9"]:
    k = component_kind(d)
    print(f"  {d:>5} -> {k:<16} ({kind_name(k)})")

print("\n=== Dibujado de todos los símbolos ===")
kinds = sorted(set(KIND_BY_PREFIX.values())) + ["generic"]
errs = 0
for k in kinds:
    try:
        pm = symbol_pixmap(k, 160, bands=["#fbc02d", "#7b1fa2", "#d32f2f"],
                           tolerance=("#c9a227", "#c9a227"), label="AB")
        img = pm.toImage()
        # contar píxeles no transparentes
        nz = 0
        for y in range(0, img.height(), 6):
            for x in range(0, img.width(), 6):
                if img.pixelColor(x, y).alpha() > 0:
                    nz += 1
        flag = "OK " if nz > 20 else "VACIO?"
        if nz <= 20:
            errs += 1
        print(f"  {k:<18} -> {flag} ({nz} muestras)")
    except Exception as e:
        errs += 1
        print(f"  {k:<18} -> ERROR {type(e).__name__}: {e}")

print(f"\nSímbolos con problema: {errs}")
print("RESULTADO:", "TODO OK" if errs == 0 else "REVISAR")
