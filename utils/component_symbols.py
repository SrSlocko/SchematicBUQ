#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Símbolos vectoriales de componentes + código de colores de resistencias.

No depende de ninguna API: los símbolos son estándar (IEC/ANSI) y se dibujan
con QPainter, así que funcionan sin internet. Para las resistencias se calcula
el código de colores real a partir del valor (p. ej. 4.7k -> amarillo-violeta-rojo-oro).
"""
import math
import re

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath
)

# ---------- Colores del código de resistencias ----------
DIGIT_COLORS = [
    ("Negro",    "#111111"),  # 0
    ("Marrón",   "#7a4a21"),  # 1
    ("Rojo",     "#d32f2f"),  # 2
    ("Naranja",  "#f57c00"),  # 3
    ("Amarillo", "#fbc02d"),  # 4
    ("Verde",    "#2e7d32"),  # 5
    ("Azul",     "#1565c0"),  # 6
    ("Violeta",  "#7b1fa2"),  # 7
    ("Gris",     "#9e9e9e"),  # 8
    ("Blanco",   "#f5f5f5"),  # 9
]
GOLD = ("Oro", "#c9a227")
SILVER = ("Plata", "#cfcfcf")
TOL_COLORS = {
    "Oro": "±5 %", "Plata": "±10 %", "Marrón": "±1 %", "Rojo": "±2 %",
    "Verde": "±0.5 %", "Azul": "±0.25 %", "Violeta": "±0.1 %", "Gris": "±0.05 %",
}

# ---------- Prefijo de designador -> tipo de símbolo ----------
KIND_BY_PREFIX = {
    "RN": "resistor_network", "RP": "resistor_network", "BR": "bridge",
    "RV": "potentiometer", "PT": "potentiometer",
    "R": "resistor", "TH": "thermistor", "NTC": "thermistor", "PTC": "thermistor",
    "VR": "varistor", "VDR": "varistor", "MOV": "varistor",
    "C": "capacitor", "CP": "electrolytic", "CX": "capacitor", "CY": "capacitor",
    "TC": "electrolytic", "VC": "capacitor",
    "L": "inductor", "FB": "ferrite", "FL": "filter", "BEAD": "ferrite", "CH": "inductor",
    "Y": "crystal", "X": "crystal", "XTAL": "crystal", "OSC": "crystal",
    "ZD": "zener", "TVS": "tvs", "LED": "led", "IR": "led", "LD": "led", "PD": "photodiode",
    "D": "diode", "CR": "diode", "VD": "diode", "DB": "bridge",
    "Q": "transistor", "T": "transformer", "TR": "transistor", "FET": "fet", "MOS": "fet",
    "U": "ic", "IC": "ic", "A": "ic",
    "J": "connector", "P": "connector", "CN": "connector", "K": "connector",
    "S": "switch", "SW": "switch", "SB": "switch", "SA": "switch", "JP": "jumper", "JW": "jumper",
    "F": "fuse", "FU": "fuse", "BT": "battery", "BAT": "battery", "B": "battery",
    "M": "motor", "MG": "motor", "SOL": "solenoid",
    "LS": "speaker", "SP": "speaker", "MIC": "mic", "ANT": "antenna",
    "TP": "testpoint", "TEST": "testpoint", "TB": "terminal", "W": "wire",
    "H": "mounting", "EH": "mounting", "G": "generator", "PS": "power", "PWR": "power",
}

KIND_NAMES = {
    "resistor": "Resistencia", "resistor_network": "Red de resistencias",
    "potentiometer": "Potenciómetro / Trimmer", "thermistor": "Termistor (NTC/PTC)",
    "varistor": "Varistor / MOV", "capacitor": "Condensador",
    "electrolytic": "Condensador electrolítico", "inductor": "Bobina / Inductor",
    "ferrite": "Ferrita / Filtro", "filter": "Filtro", "crystal": "Cristal / Oscilador",
    "diode": "Diodo", "zener": "Diodo Zener", "tvs": "Diodo TVS",
    "led": "LED / Diodo emisor", "photodiode": "Fotodiodo", "bridge": "Puente de diodos",
    "transistor": "Transistor", "fet": "Transistor MOSFET/JFET", "ic": "Circuito integrado",
    "connector": "Conector", "switch": "Interruptor / Pulsador", "jumper": "Jumper",
    "fuse": "Fusible", "battery": "Pila / Batería", "motor": "Motor",
    "solenoid": "Solenoide", "speaker": "Altavoz", "mic": "Micrófono",
    "transformer": "Transformador", "antenna": "Antena", "testpoint": "Punto de prueba", "terminal": "Borne / Regleta",
    "wire": "Cable", "mounting": "Anclaje / Tornillo", "generator": "Generador",
    "power": "Alimentación", "generic": "Componente",
}

# Colores de trazo/fondo
WIRE = QColor("#cfd8e3")
FILL = QColor("#2a3140")
ACCENT = QColor("#4a90d9")
TEXT = QColor("#e6ecf5")


# =================== Designador -> tipo ===================
def prefix_of(designator):
    m = re.match(r'^([A-Za-z]+)', (designator or '').strip())
    return m.group(1).upper() if m else ""


def component_kind(designator, component_type=""):
    """Determina el tipo de símbolo a dibujar."""
    pref = prefix_of(designator)
    # Prefijo más largo primero (RN antes que R)
    for length in range(len(pref), 0, -1):
        p = pref[:length]
        if p in KIND_BY_PREFIX:
            return KIND_BY_PREFIX[p]
    t = (component_type or '').lower()
    if "resist" in t:
        return "resistor"
    if "condensador" in t or "capacitor" in t:
        return "capacitor"
    if "bobina" in t or "induct" in t:
        return "inductor"
    if "zener" in t:
        return "zener"
    if "diodo" in t or "diode" in t:
        return "diode"
    if "led" in t:
        return "led"
    if "transistor" in t:
        return "transistor"
    if "integrado" in t or "ic" in t:
        return "ic"
    if "conector" in t or "connector" in t:
        return "connector"
    if "fusible" in t or "fuse" in t:
        return "fuse"
    if "transformador" in t or "transformer" in t:
        return "transformer"
    return "generic"


def kind_name(kind):
    return KIND_NAMES.get(kind, "Componente")


# =================== Valor -> ohmios ===================
_MULT = {'': 1.0, 'r': 1.0, 'k': 1e3, 'm': 1e-3, 'M': 1e6, 'g': 1e9}


def parse_resistance(text):
    """Devuelve el valor en ohmios de '4k7', '10K', '4.7k', '470', '2M2'..."""
    if not text:
        return None
    s = str(text).strip().replace(',', '.')
    s = s.replace('Ω', '').replace('ohms', '').replace('ohm', '').replace('OHM', '')
    s = s.replace(' ', '')
    m = re.match(r'^([0-9.]+)([a-zA-Z]+)([0-9]+)$', s)   # 4k7 / 2M2 / 0R22
    if m:
        mult = _MULT.get(m.group(2), _MULT.get(m.group(2).lower()))
        if mult is None:
            return None
        try:
            return float(m.group(1) + '.' + m.group(3)) * mult
        except ValueError:
            return None
    m = re.match(r'^([0-9.]+)\s*([a-zA-Z]*)$', s)
    if not m:
        return None
    try:
        base = float(m.group(1))
    except ValueError:
        return None
    suf = m.group(2)
    mult = _MULT.get(suf, _MULT.get(suf.lower()))
    if suf == '':
        return base
    return base * mult if mult is not None else None


def resistor_color_code(value, bands_count=None):
    """Calcula el código de colores a partir del valor.

    Devuelve dict con 'value_bands' [(nombre, hex)...] (dígitos + multiplicador),
    'tolerance' (nombre, hex), 'tolerance_text' y 'summary'.
    """
    ohms = parse_resistance(value)
    if ohms is None or ohms <= 0:
        return None
    chosen = None
    for sig in (2, 3):
        exp = int(math.floor(math.log10(ohms)))
        e_mult = exp - (sig - 1)
        if e_mult < -2 or e_mult > 9:
            continue
        mult = 10 ** e_mult
        digits = int(round(ohms / mult))
        if digits <= 0:
            continue
        # Aceptar solo si el valor se representa EXACTO con esas cifras
        # (si no, p. ej. 499 se redondearía a 500 y perderíamos un dígito).
        if abs(digits * mult - ohms) <= max(1e-9, ohms * 1e-6):
            chosen = (sig, digits, e_mult)
            break
    if chosen is None:
        return None
    sig, digits, e_mult = chosen
    digit_list = [int(c) for c in str(digits).zfill(sig)]
    vbands = [DIGIT_COLORS[d] for d in digit_list]
    if 0 <= e_mult <= 9:
        vbands.append(DIGIT_COLORS[e_mult])
    elif e_mult == -1:
        vbands.append(GOLD)
    else:
        vbands.append(SILVER)
    tol = GOLD if sig == 2 else ("Marrón", "#7a4a21")
    names = " · ".join(b[0] for b in vbands) + " · " + tol[0]
    return {
        "ohms": ohms,
        "sig": sig,
        "value_bands": vbands,
        "tolerance": tol,
        "tolerance_text": TOL_COLORS.get(tol[0], ""),
        "summary": names,
    }


def format_ohms(v):
    if v is None:
        return "-"
    if v >= 1e6:
        return f"{v / 1e6:.4g} MΩ"
    if v >= 1e3:
        return f"{v / 1e3:.4g} kΩ"
    return f"{v:.4g} Ω"


_CAP_MULT = {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'm': 1e-3,
             'f': 1.0, '': 1.0, 'k': 1e3}


def parse_farads(text):
    """Devuelve el valor en faradios de '100n', '10u', '4.7u', '22p', '1n'..."""
    if not text:
        return None
    s = str(text).strip().replace(',', '.').replace(' ', '')
    m = re.match(r'^([0-9.]+)\s*([a-zA-Zµ]*)$', s)
    if not m:
        return None
    try:
        base = float(m.group(1))
    except ValueError:
        return None
    suf = m.group(2)
    if suf.endswith(('f', 'F')):
        suf = suf[:-1]
    mult = _CAP_MULT.get(suf, _CAP_MULT.get(suf.lower()))
    if mult is None:
        return None
    return base * mult


def format_farads(f):
    if f is None:
        return "-"
    pf = f * 1e12
    if pf >= 1e6:
        return f"{f * 1e6:.4g} µF"
    if pf >= 1e3:
        return f"{f * 1e9:.4g} nF"
    return f"{pf:.4g} pF"


def capacitor_code(value):
    """Código de 3 dígitos grabado en condensadores cerámicos (104, 473...)."""
    f = parse_farads(value)
    if f is None or f <= 0:
        return None
    pf = f * 1e12
    if pf < 10 or pf >= 1e6:          # fuera del rango del marcaje (10 pF .. 1 µF)
        return None
    exp = int(math.floor(math.log10(pf))) - 1
    digits = int(round(pf / (10 ** exp)))
    if abs(digits * 10 ** exp - pf) > max(1e-6, pf * 1e-6):
        return None
    if digits < 10 or digits > 99 or not (0 <= exp <= 9):
        return None
    return f"{digits}{exp}"


# =================== Dibujo de símbolos ===================
def symbol_pixmap(kind, size=200, bands=None, tolerance=None, label="", bg=None):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    if bg:
        p.fillRect(0, 0, size, size, QColor(bg))
    m = size * 0.10
    p.translate(m, m)
    p.scale((size - 2 * m) / 200.0, (size - 2 * m) / 200.0)
    _draw(p, kind, bands or [], tolerance, label)
    p.end()
    return pm


def _stroke(color=WIRE, width=5):
    pen = QPen(color, width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _leads(p, y=100, xa=(8, 52), xb=(148, 192)):
    p.setPen(_stroke(WIRE, 5))
    p.drawLine(QPointF(*xa if isinstance(xa, tuple) else xa), QPointF(xa[1], y))
    p.drawLine(QPointF(xb[0], y), QPointF(xb[1], y))


def _text(p, x, y, s, size=16, color=TEXT, bold=False):
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    p.setFont(f)
    p.setPen(QPen(color))
    p.drawText(QRectF(x - 90, y - 14, 180, 28), Qt.AlignCenter, s)


def _draw(p, kind, bands, tolerance, label):
    p.setPen(_stroke(WIRE, 5))
    p.setBrush(Qt.NoBrush)

    if kind in ("resistor", "thermistor", "varistor", "resistor_network"):
        # Cuerpo
        p.setBrush(QBrush(FILL))
        p.setPen(_stroke(WIRE, 4))
        p.drawRoundedRect(QRectF(50, 78, 100, 44), 6, 6)
        _leads(p)
        if kind == "varistor":
            p.setPen(_stroke(ACCENT, 4))
            p.drawLine(QPointF(40, 150), QPointF(160, 55))
            p.drawLine(QPointF(150, 55), QPointF(160, 55))
            p.drawLine(QPointF(160, 55), QPointF(160, 65))
        elif kind == "thermistor":
            p.setPen(_stroke(ACCENT, 4))
            p.drawLine(QPointF(48, 148), QPointF(165, 148))
            p.drawLine(QPointF(165, 148), QPointF(152, 140))
        elif kind == "resistor_network":
            for xx in (70, 100, 130):
                p.setPen(_stroke(WIRE, 3))
                p.drawLine(QPointF(xx, 78), QPointF(xx, 55))
        # Bandas de color
        if bands:
            p.setPen(Qt.NoPen)
            for i, col in enumerate(bands):
                hx = col[1] if isinstance(col, (tuple, list)) else col
                bx = 60 + i * 13
                p.setBrush(QBrush(QColor(hx)))
                p.drawRect(QRectF(bx, 80, 8, 40))
            if tolerance:
                thx = tolerance[1] if isinstance(tolerance, (tuple, list)) else tolerance
                p.setBrush(QBrush(QColor(thx)))
                p.drawRect(QRectF(134, 80, 8, 40))

    elif kind == "potentiometer":
        p.setBrush(QBrush(FILL)); p.setPen(_stroke(WIRE, 4))
        p.drawRoundedRect(QRectF(50, 78, 100, 44), 6, 6)
        _leads(p)
        p.setPen(_stroke(ACCENT, 5))
        p.drawLine(QPointF(100, 30), QPointF(100, 70))
        p.setBrush(QBrush(ACCENT)); p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([QPointF(92, 60), QPointF(108, 60), QPointF(100, 74)]))

    elif kind in ("capacitor", "filter"):
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(82, 100))
        p.drawLine(QPointF(118, 100), QPointF(192, 100))
        p.setPen(_stroke(WIRE, 7))
        p.drawLine(QPointF(82, 55), QPointF(82, 145))
        p.drawLine(QPointF(118, 55), QPointF(118, 145))

    elif kind == "electrolytic":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(84, 100))
        p.drawLine(QPointF(128, 100), QPointF(192, 100))
        p.setPen(_stroke(WIRE, 7))
        p.drawLine(QPointF(84, 55), QPointF(84, 145))
        path = QPainterPath()
        path.moveTo(128, 52)
        path.quadTo(108, 100, 128, 148)
        p.drawPath(path)
        p.setPen(_stroke(ACCENT, 5))
        _text(p, 60, 45, "+", 22, ACCENT, True)

    elif kind in ("inductor", "ferrite"):
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(40, 100))
        p.drawLine(QPointF(160, 100), QPointF(192, 100))
        path = QPainterPath()
        path.moveTo(40, 100)
        for i in range(4):
            cx = 40 + i * 30
            path.arcTo(QRectF(cx, 70, 30, 60), 180, -180)
        p.drawPath(path)
        if kind == "ferrite":
            p.setPen(_stroke(ACCENT, 4))
            p.drawLine(QPointF(40, 55), QPointF(160, 55))
            p.drawLine(QPointF(40, 145), QPointF(160, 145))

    elif kind == "crystal":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(62, 100))
        p.drawLine(QPointF(138, 100), QPointF(192, 100))
        p.setPen(_stroke(WIRE, 7))
        p.drawLine(QPointF(62, 55), QPointF(62, 145))
        p.drawLine(QPointF(138, 55), QPointF(138, 145))
        p.setPen(_stroke(WIRE, 5))
        p.setBrush(QBrush(FILL))
        p.drawRect(QRectF(84, 58, 32, 84))

    elif kind in ("diode", "zener", "tvs", "led", "photodiode", "bridge"):
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(74, 100))
        p.drawLine(QPointF(126, 100), QPointF(192, 100))
        p.setBrush(QBrush(FILL))
        p.drawPolygon(QPolygonF([QPointF(74, 62), QPointF(74, 138), QPointF(126, 100)]))
        p.setPen(_stroke(WIRE, 6))
        p.drawLine(QPointF(126, 58), QPointF(126, 142))
        if kind == "zener":
            p.setPen(_stroke(WIRE, 6))
            p.drawLine(QPointF(112, 58), QPointF(126, 58))
            p.drawLine(QPointF(126, 142), QPointF(140, 142))
        elif kind == "led":
            p.setPen(_stroke(ACCENT, 4))
            for dx in (0, 18):
                p.drawLine(QPointF(96 + dx, 46), QPointF(112 + dx, 20))
                p.drawLine(QPointF(112 + dx, 20), QPointF(103 + dx, 24))
                p.drawLine(QPointF(112 + dx, 20), QPointF(108 + dx, 29))
        elif kind == "photodiode":
            p.setPen(_stroke(ACCENT, 4))
            for dx in (0, 18):
                p.drawLine(QPointF(80 + dx, 22), QPointF(96 + dx, 48))

    elif kind == "bridge":
        p.setPen(_stroke(WIRE, 5))
        p.setBrush(QBrush(FILL))
        p.drawPolygon(QPolygonF([QPointF(100, 45), QPointF(155, 100),
                                 QPointF(100, 155), QPointF(45, 100)]))
        _text(p, 100, 100, "~", 20, ACCENT, True)

    elif kind == "transistor":
        p.setPen(_stroke(WIRE, 4)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(100, 100), 58, 58)
        p.setPen(_stroke(WIRE, 7))
        p.drawLine(QPointF(78, 55), QPointF(78, 145))          # base
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(78, 100))          # base lead
        p.drawLine(QPointF(78, 78), QPointF(130, 50))          # collector
        p.drawLine(QPointF(130, 50), QPointF(160, 50))
        p.drawLine(QPointF(78, 122), QPointF(130, 150))        # emitter
        p.drawLine(QPointF(130, 150), QPointF(160, 150))
        p.setBrush(QBrush(WIRE)); p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([QPointF(78, 122), QPointF(92, 108), QPointF(100, 120)]))

    elif kind == "fet":
        p.setPen(_stroke(WIRE, 4)); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(100, 100), 58, 58)
        p.setPen(_stroke(WIRE, 6))
        p.drawLine(QPointF(74, 55), QPointF(74, 145))          # gate bar
        p.setPen(_stroke(WIRE, 4))
        for yy in (62, 100, 138):
            p.drawLine(QPointF(88, yy), QPointF(104, yy))      # channel segments
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(74, 100))
        p.drawLine(QPointF(104, 62), QPointF(150, 62)); p.drawLine(QPointF(150, 62), QPointF(160, 62))
        p.drawLine(QPointF(104, 138), QPointF(150, 138)); p.drawLine(QPointF(150, 138), QPointF(160, 138))
        p.drawLine(QPointF(104, 100), QPointF(140, 100))

    elif kind == "ic":
        p.setPen(_stroke(WIRE, 4)); p.setBrush(QBrush(FILL))
        p.drawRoundedRect(QRectF(52, 40, 96, 120), 8, 8)
        p.setPen(_stroke(WIRE, 4))
        for yy in (62, 88, 114, 140):
            p.drawLine(QPointF(28, yy), QPointF(52, yy))
            p.drawLine(QPointF(148, yy), QPointF(172, yy))
        p.setBrush(QBrush(ACCENT)); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(68, 56), 6, 6)
        if label:
            _text(p, 100, 100, label[:6], 15, TEXT, True)

    elif kind in ("connector", "terminal", "jumper", "testpoint"):
        p.setPen(_stroke(WIRE, 4)); p.setBrush(QBrush(FILL))
        p.drawRoundedRect(QRectF(60, 50, 80, 100), 6, 6)
        p.setPen(_stroke(WIRE, 6))
        for yy in (70, 100, 130):
            p.drawLine(QPointF(30, yy), QPointF(60, yy))
            p.setBrush(QBrush(ACCENT)); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(72, yy), 6, 6)
            p.setPen(_stroke(WIRE, 6))

    elif kind == "switch":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(60, 100))
        p.drawLine(QPointF(140, 100), QPointF(192, 100))
        p.setBrush(QBrush(ACCENT)); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(60, 100), 7, 7)
        p.drawEllipse(QPointF(140, 100), 7, 7)
        p.setPen(_stroke(WIRE, 6))
        p.drawLine(QPointF(60, 100), QPointF(150, 48))

    elif kind == "fuse":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(50, 100))
        p.drawLine(QPointF(150, 100), QPointF(192, 100))
        p.setBrush(QBrush(FILL)); p.setPen(_stroke(WIRE, 4))
        p.drawRoundedRect(QRectF(50, 78, 100, 44), 8, 8)
        p.setPen(_stroke(ACCENT, 5))
        p.drawLine(QPointF(50, 100), QPointF(150, 100))

    elif kind == "transformer":
        _leads(p, y=100, xa=(8, 45), xb=(155, 192))
        p.setPen(_stroke(WIRE, 5))
        for xx in (62, 138):
            path = QPainterPath()
            path.moveTo(xx, 55)
            for i in range(3):
                path.arcTo(QRectF(xx - 15, 55 + i * 30, 30, 30), 90, -180)
            p.drawPath(path)
        p.setPen(_stroke(WIRE, 4))
        p.drawLine(QPointF(96, 45), QPointF(96, 155))
        p.drawLine(QPointF(104, 45), QPointF(104, 155))

    elif kind == "battery":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(70, 100))
        p.drawLine(QPointF(130, 100), QPointF(192, 100))
        p.setPen(_stroke(WIRE, 6))
        p.drawLine(QPointF(70, 60), QPointF(70, 140))          # long (+)
        p.drawLine(QPointF(90, 78), QPointF(90, 122))          # short
        p.drawLine(QPointF(110, 60), QPointF(110, 140))
        p.drawLine(QPointF(130, 78), QPointF(130, 122))
        _text(p, 45, 50, "+", 20, ACCENT, True)

    elif kind == "speaker":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(60, 100))
        p.setBrush(QBrush(FILL))
        p.drawRect(QRectF(60, 78, 26, 44))
        p.drawPolygon(QPolygonF([QPointF(86, 78), QPointF(126, 44),
                                 QPointF(126, 156), QPointF(86, 122)]))
        p.setPen(_stroke(ACCENT, 4)); p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(132, 70, 40, 60), -60 * 16, 120 * 16)

    elif kind == "mic":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(70, 100))
        p.drawLine(QPointF(130, 100), QPointF(192, 100))
        p.drawRoundedRect(QRectF(80, 60, 40, 80), 18, 18)
        p.setPen(_stroke(WIRE, 4))
        p.drawArc(QRectF(62, 78, 76, 70), 200 * 16, 140 * 16)

    elif kind == "motor":
        p.setPen(_stroke(WIRE, 4)); p.setBrush(QBrush(FILL))
        p.drawEllipse(QPointF(100, 100), 58, 58)
        _text(p, 100, 100, "M", 30, TEXT, True)

    elif kind == "generator":
        p.setPen(_stroke(WIRE, 4)); p.setBrush(QBrush(FILL))
        p.drawEllipse(QPointF(100, 100), 58, 58)
        _text(p, 100, 100, "G", 30, TEXT, True)

    elif kind == "solenoid":
        p.setPen(_stroke(WIRE, 5))
        p.drawRect(QRectF(70, 70, 60, 60))
        p.drawLine(QPointF(8, 100), QPointF(70, 100))
        p.drawLine(QPointF(130, 100), QPointF(192, 100))
        _text(p, 100, 100, "SOL", 14, TEXT, True)

    elif kind == "antenna":
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(8, 100), QPointF(100, 100))
        p.drawLine(QPointF(100, 100), QPointF(100, 40))
        p.drawLine(QPointF(100, 40), QPointF(70, 70))
        p.drawLine(QPointF(100, 40), QPointF(130, 70))

    elif kind == "mounting":
        p.setPen(_stroke(WIRE, 5)); p.setBrush(QBrush(FILL))
        p.drawEllipse(QPointF(100, 100), 52, 52)
        p.setPen(_stroke(ACCENT, 4))
        p.drawLine(QPointF(70, 70), QPointF(130, 130))
        p.drawLine(QPointF(130, 70), QPointF(70, 130))

    elif kind == "power":
        p.setPen(_stroke(WIRE, 5)); p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(8, 100), QPointF(80, 100))
        p.drawEllipse(QPointF(112, 100), 32, 32)
        _text(p, 112, 100, "V", 24, ACCENT, True)
        p.setPen(_stroke(WIRE, 5))
        p.drawLine(QPointF(144, 100), QPointF(192, 100))

    else:  # generic
        p.setPen(_stroke(WIRE, 4)); p.setBrush(QBrush(FILL))
        p.drawRoundedRect(QRectF(55, 55, 90, 90), 12, 12)
        _text(p, 100, 100, "?", 40, ACCENT, True)
