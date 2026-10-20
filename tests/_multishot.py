# -*- coding: utf-8 -*-
"""Genera una muestra visual de la pestaña MULTÍMETRO (PNG) para revisarla."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)

from gui.widgets.multimeter_panel import MultimeterPanel

W, H = 950, 780
shots = []
for des, val, tp, state in [
    ("R28", "10k", "Resistencia", 1),      # 1 = "En corto"
    ("C30", "100uF", "Condensador electrolítico", 0),
]:
    p = MultimeterPanel()
    p.resize(W, H)
    p.show()
    app.processEvents()
    p.show_component(des, val, tp)
    if 0 <= state < len(p._buttons):
        p._on_state(state)
    app.processEvents()
    pm = QPixmap(W, H)
    pm.fill(QColor("#12161d"))
    p.render(pm)
    shots.append(pm)
    p.close()

total = QPixmap(W, H * len(shots) + 10 * (len(shots) - 1))
total.fill(QColor("#0b0e13"))
painter = QPainter(total)
for i, pm in enumerate(shots):
    painter.drawPixmap(0, i * (H + 10), pm)
painter.end()

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_multimetro.png")
ok = total.save(out, "PNG")
print("Guardado:", out, "->", ok, "|", total.width(), "x", total.height())
