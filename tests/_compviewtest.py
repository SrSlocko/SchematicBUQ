# -*- coding: utf-8 -*-
"""Prueba del panel gráfico del componente."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.widgets.component_view import ComponentView

v = ComponentView()

casos = [
    ("R28", "10k", "resistencia", "pdf"),
    ("R46", "4.7k", "resistencia", "ocr"),
    ("C12", "100n", "condensador", "pdf"),
    ("C30", "10u", "condensador electrolítico", "pdf"),
    ("D3", "1N4148", "diodo", "pdf"),
    ("U5", "TL074", "circuito integrado", "pdf"),
    ("Q1", "BC547", "transistor", "pdf"),
    ("L2", "100uH", "bobina", "pdf"),
]

ok = 0
for des, val, typ, src in casos:
    try:
        v.show_component(des, val, typ, src)
        pm = v._symbol_pm
        has = pm is not None and not pm.isNull()
        code_txt = v.lbl_code.text()
        # longitud del texto sin etiquetas HTML
        import re
        plain = re.sub(r'<[^>]+>', '', code_txt)
        print(f"  {des:<5} {val:<7} -> símbolo={'OK' if has else 'FALLA'} "
              f"| tipo='{v.lbl_kind.text()}' | código='{plain.strip()[:60]}'")
        ok += 1 if has else 0
    except Exception as e:
        print(f"  {des} -> ERROR {type(e).__name__}: {e}")

print(f"\nComponentes mostrados: {ok}/{len(casos)}")
print("RESULTADO:", "TODO OK" if ok == len(casos) else "REVISAR")
