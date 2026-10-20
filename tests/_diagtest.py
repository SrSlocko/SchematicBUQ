# -*- coding: utf-8 -*-
"""Prueba del motor de diagnóstico y del panel."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from utils import diagnostics as D
from gui.widgets.diagnostic_panel import DiagnosticPanel
from gui.widgets.component_view import ComponentView

print("=== Lecturas esperadas con valor real ===")
casos = [
    ("resistor", "10k"), ("resistor", "4.7k"), ("electrolytic", "470u"),
    ("capacitor", "100n"), ("diode", ""), ("zener", "5V1"),
    ("transistor", ""), ("fet", ""), ("ic", ""), ("fuse", ""),
    ("led", "rojo"), ("led", "azul"), ("bridge", ""), ("speaker", "8"),
]
for kind, val in casos:
    lines = D.expected_readings(kind, val)
    print(f"\n[{kind} {val}]")
    for l in lines[:3]:
        print("   -", re.sub('<[^>]+>', '', l))

print("\n=== Panel de diagnóstico (HTML) ===")
p = DiagnosticPanel()
p.show_component("R28", "10k", "resistencia")
html = p.view.toHtml()
checks = {
    "uso": "Uso en el circuito" in html,
    "multimetro": "Prueba con multímetro" in html,
    "corto": "Detección de cortocircuito" in html,
    "fallos": "Fallos típicos" in html,
    "sintoma": "Guía por síntoma" in html,
    "general": "Guía rápida general" in html,
    "valor_10k": "10 kΩ" in html,
}
for k, v in checks.items():
    print(f"   {k:<12}: {'OK' if v else 'FALTA'}")
print("   Título:", p.lbl_title.text())
print("   Longitud HTML:", len(html), "caracteres")

print("\n=== Panel de diagnóstico con otros componentes ===")
for des, val, typ in [("C30", "470u", "condensador electrolítico"),
                      ("Q1", "BC547", "transistor"),
                      ("U5", "TL074", "circuito integrado"),
                      ("F1", "2A", "fusible"),
                      ("D3", "1N4148", "diodo")]:
    p.show_component(des, val, typ)
    h = p.view.toHtml()
    print(f"   {des:<5} {typ:<28} -> {p.lbl_title.text()}")

print("\n=== Panel Componente: resumen de diagnóstico ===")
v = ComponentView()
v.show_component("R28", "10k", "resistencia")
diag_plain = re.sub('<[^>]+>', ' ', v.lbl_diag.text())
print("   Resumen:", " ".join(diag_plain.split())[:200])
print("   Visible:", v.grp_diag.isVisibleTo(v))

print("\n=== Limpiar ===")
p.clear(); v.clear()
print("   Panel diag título:", p.lbl_title.text())
print("   Panel comp designador:", repr(v._designator))

allok = all(checks.values())
print("\nRESULTADO:", "TODO OK" if allok else "REVISAR")
