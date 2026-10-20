# -*- coding: utf-8 -*-
"""Genera una hoja de muestra con los símbolos y el código de colores."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush

app = QApplication(sys.argv)

from utils.component_symbols import (
    symbol_pixmap, resistor_color_code, component_kind, kind_name,
    capacitor_code, format_ohms, format_farads, parse_farads
)

W, H = 1180, 820
sheet = QPixmap(W, H)
sheet.fill(QColor("#12161d"))
p = QPainter(sheet)
p.setRenderHint(QPainter.Antialiasing)

# Título
p.setPen(QPen(QColor("#e6ecf5")))
f = QFont("Segoe UI", 20); f.setBold(True); p.setFont(f)
p.drawText(QRectF(0, 16, W, 40), Qt.AlignCenter,
           "SchematicBuq  ·  Símbolos de componentes y código de colores")

# ---- Resistor grande R28 = 10k con bandas ----
cc = resistor_color_code("10k")
big = symbol_pixmap("resistor", 300, bands=cc["value_bands"],
                    tolerance=cc["tolerance"], label="")
p.drawPixmap(40, 80, big)

f = QFont("Segoe UI", 15); f.setBold(True); p.setFont(f)
p.setPen(QPen(QColor("#7fd1a0")))
p.drawText(QRectF(360, 110, 520, 30), Qt.AlignLeft, "R28   —   Resistencia   —   10 kΩ")
f2 = QFont("Segoe UI", 12); p.setFont(f2)
p.setPen(QPen(QColor("#cfd8e3")))
p.drawText(QRectF(360, 150, 780, 26), Qt.AlignLeft,
           "Valor normalizado: " + format_ohms(cc["ohms"]) + "  " + cc["tolerance_text"])

# Bandas con nombre y color
x = 360
for i, (nm, hx) in enumerate(cc["value_bands"] + [cc["tolerance"]]):
    p.setBrush(QBrush(QColor(hx))); p.setPen(QPen(QColor("#00000066")))
    p.drawRoundedRect(QRectF(x, 195, 44, 60), 4, 4)
    p.setPen(QPen(QColor("#cfd8e3")))
    p.drawText(QRectF(x - 18, 258, 80, 22), Qt.AlignCenter, nm)
    x += 82
p.setPen(QPen(QColor("#9fb0c7")))
p.drawText(QRectF(360, 288, 780, 24), Qt.AlignLeft,
           "Código: " + cc["summary"] + "  (" + cc["tolerance_text"] + ")")

# ---- Rejilla de otros símbolos ----
samples = [
    ("C12", "100n", "Condensador",        "capacitor"),
    ("C30", "10u",  "Condensador electrolítico", "electrolytic"),
    ("D3",  "1N4148", "Diodo",            "diode"),
    ("ZD17", "5V1", "Diodo Zener",        "zener"),
    ("LED2", "",    "LED",                "led"),
    ("Q1",  "BC547", "Transistor",        "transistor"),
    ("U5",  "TL074", "Circuito integrado", "ic"),
    ("L2",  "100uH", "Bobina",            "inductor"),
    ("T1",  "",     "Transformador",      "transformer"),
    ("Y1",  "8MHz", "Cristal",            "crystal"),
    ("J1",  "",     "Conector",           "connector"),
    ("SW1", "",     "Interruptor",        "switch"),
    ("F1",  "2A",   "Fusible",            "fuse"),
    ("RV1", "10k",  "Potenciómetro",      "potentiometer"),
    ("LS1", "",     "Altavoz",            "speaker"),
    ("BR1", "",     "Puente de diodos",   "bridge"),
]

cols = 8
tw, th = 140, 150
x0, y0 = 30, 350
for i, (des, val, name, kind) in enumerate(samples):
    cx = x0 + (i % cols) * tw
    cy = y0 + (i // cols) * th
    pm = symbol_pixmap(kind, 110, label=val if kind == "ic" else "")
    p.drawPixmap(cx + 15, cy, pm)
    p.setPen(QPen(QColor("#cfd8e3")))
    f = QFont("Segoe UI", 9); f.setBold(True); p.setFont(f)
    p.drawText(QRectF(cx, cy + 112, tw, 18), Qt.AlignCenter, des)
    f = QFont("Segoe UI", 8); f.setBold(False); p.setFont(f)
    p.setPen(QPen(QColor("#9fb0c7")))
    p.drawText(QRectF(cx, cy + 128, tw, 18), Qt.AlignCenter, name[:22])

# Nota de condensadores
p.setPen(QPen(QColor("#c9a227")))
f = QFont("Segoe UI", 10); p.setFont(f)
p.drawText(QRectF(30, H - 34, W - 60, 24), Qt.AlignLeft,
           "Condensadores cerámicos: marcaje de 3 cifras (p. ej. 104 = 10 × 10⁴ pF = 100 nF)")
p.end()

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_componentes.png")
sheet.save(out, "PNG")
print("Guardado:", out)
