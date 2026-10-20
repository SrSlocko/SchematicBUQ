# -*- coding: utf-8 -*-
"""Prueba de la pestaña MULTÍMETRO (offscreen)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from gui.widgets.multimeter_panel import MultimeterPanel

app = QApplication(sys.argv)
p = MultimeterPanel()

casos = [
    ("R28", "10k", "Resistencia"),
    ("C30", "100nF", "Condensador"),
    ("Q1", "2N3904", "Transistor"),
    ("U5", "TL074", "Circuito integrado"),
    ("F1", "", "Fusible"),
    ("D12", "1N4007", "Diodo"),
]
for des, val, tp in casos:
    p.show_component(des, val, tp)
    print(f"[{des} {val}] titulo: {p.lbl_title.text()}")
    print(f"    botones: {[b.text().strip() for b in p._buttons]}")
    # simular pulsación del primer botón
    if p._buttons:
        p._on_state(0)
        txt = p.lbl_result.text()
        print(f"    veredicto[0]: {txt[:110].replace(chr(10),' ')}")
    # comprobar contenido del procedimiento
    body = p.view.toPlainText()
    print(f"    procedimiento: {len(body)} chars | tiene 'corto': {'corto' in body.lower()}")
    assert p.lbl_title.text().strip(), "titulo vacío"
    assert p.view.toPlainText().strip(), "procedimiento vacío"
    assert p._buttons, f"sin botones de verificación para {des}"

# limpiar
p.clear()
print("clear -> titulo:", p.lbl_title.text())
print("TODO OK")
