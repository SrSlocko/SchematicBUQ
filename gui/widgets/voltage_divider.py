#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calculadora de divisor de tensión (para diagnóstico y reparación).

Permite:
  * Calcular Vout a partir de Vin, R1 y R2.
  * Calcular R2 (o R1) necesaria para obtener un Vout deseado.
  * Ver la corriente y la potencia disipada en cada resistencia y avisar si
    se supera la potencia típica de 1/4 W (causa habitual de averías).
"""
import math
import re

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Multiplicadores admitidos: 10k, 4k7, 1M, 2M2, 470, 0R22 ...
_MULT = {'': 1.0, 'r': 1.0, 'k': 1e3, 'K': 1e3, 'm': 1e-3,
         'M': 1e6, 'meg': 1e6, 'g': 1e9, 'G': 1e9}


def parse_number(text):
    """Convierte '4k7', '10K', '1M', '2,2k', '470', '0R22' en float. None si no."""
    if text is None:
        return None
    s = str(text).strip().replace(',', '.')
    if not s:
        return None
    s = s.replace('Ω', '').replace('ohms', '').replace('ohm', '')
    s = s.replace(' ', '')
    # Notación 4k7 / 2M2 / 0R22 (letra EN MEDIO de dos grupos de dígitos)
    m = re.match(r'^([0-9.]+)([a-zA-Z]+)([0-9]+)$', s)
    if m:
        mult = _MULT.get(m.group(2), None)
        if mult is None:
            mult = _MULT.get(m.group(2).lower(), None)
        if mult is None:
            return None
        return float(m.group(1) + '.' + m.group(3)) * mult
    # Número con sufijo final: 10k, 100n, 4.7M, 470
    m = re.match(r'^([0-9.]+)\s*([a-zA-Z]*)$', s)
    if not m:
        return None
    try:
        base = float(m.group(1))
    except ValueError:
        return None
    suf = m.group(2)
    if suf == '':
        return base
    if suf in _MULT:
        return base * _MULT[suf]
    if suf.lower() in _MULT:
        return base * _MULT[suf.lower()]
    return None


def fmt_ohms(v):
    if v is None:
        return "-"
    if v >= 1e6:
        return f"{v / 1e6:.4g} MΩ"
    if v >= 1e3:
        return f"{v / 1e3:.4g} kΩ"
    return f"{v:.4g} Ω"


def fmt_v(v):
    if v is None:
        return "-"
    return f"{v:.4g} V"


def fmt_w(v):
    if v is None:
        return "-"
    if v < 1.0:
        return f"{v * 1000:.4g} mW"
    return f"{v:.4g} W"


def fmt_a(v):
    if v is None:
        return "-"
    if v < 1.0:
        return f"{v * 1000:.4g} mA"
    return f"{v:.4g} A"


def fmt_num(v):
    """Formatea un número para poder volver a leerlo (sin notación científica)."""
    if v is None:
        return ""
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 1e12 or a < 1e-3:
        return f"{v:.4g}"
    if a >= 100:
        return f"{v:.0f}"
    if a >= 1:
        return f"{v:.2f}".rstrip('0').rstrip('.')
    return f"{v:.4f}".rstrip('0').rstrip('.')


class VoltageDividerPanel(QWidget):
    """Panel de la pestaña 'Divisor de tensión'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    # ---------------- UI ----------------
    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("🧮  Calculadora de divisor de tensión")
        tf = QFont(); tf.setBold(True); tf.setPointSize(12)
        title.setFont(tf)
        layout.addWidget(title)

        formula = QLabel("Fórmula:   Vout = Vin × R2 / (R1 + R2)      "
                         "I = Vin / (R1 + R2)")
        formula.setStyleSheet("color:#8fa3bf; font-size:11px;")
        layout.addWidget(formula)

        # --- Modo ---
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("¿Qué quieres calcular?"))
        self.mode = QComboBox()
        self.mode.addItems([
            "Vout (dados Vin, R1 y R2)",
            "R2 (dados Vin, Vout y R1)",
            "R1 (dados Vin, Vout y R2)",
        ])
        self.mode.currentIndexChanged.connect(self._update_fields)
        mode_row.addWidget(self.mode, 1)
        layout.addLayout(mode_row)

        # --- Entradas ---
        box = QGroupBox("Datos")
        grid = QGridLayout(box)

        self.lbl_vin = QLabel("Vin (V)")
        self.ed_vin = QLineEdit()
        self.ed_vin.setPlaceholderText("ej. 40")
        self.lbl_r1 = QLabel("R1 — resistencia superior")
        self.ed_r1 = QLineEdit()
        self.ed_r1.setPlaceholderText("ej. 10k")
        self.lbl_r2 = QLabel("R2 — resistencia inferior")
        self.ed_r2 = QLineEdit()
        self.ed_r2.setPlaceholderText("ej. 4k7")
        self.lbl_vout = QLabel("Vout (V)")
        self.ed_vout = QLineEdit()
        self.ed_vout.setPlaceholderText("ej. 12")

        grid.addWidget(self.lbl_vin, 0, 0);   grid.addWidget(self.ed_vin, 0, 1)
        grid.addWidget(self.lbl_r1, 1, 0);    grid.addWidget(self.ed_r1, 1, 1)
        grid.addWidget(self.lbl_r2, 2, 0);    grid.addWidget(self.ed_r2, 2, 1)
        grid.addWidget(self.lbl_vout, 3, 0);  grid.addWidget(self.ed_vout, 3, 1)
        grid.setColumnStretch(1, 1)
        layout.addWidget(box)

        # --- Botones ---
        btns = QHBoxLayout()
        self.btn_calc = QPushButton("🧮  Calcular")
        self.btn_calc.setStyleSheet("background-color:#2563eb;color:white;")
        self.btn_clear = QPushButton("Limpiar")
        btns.addWidget(self.btn_calc)
        btns.addWidget(self.btn_clear)
        btns.addStretch()
        layout.addLayout(btns)

        # --- Resultado ---
        res_box = QGroupBox("Resultado")
        rl = QVBoxLayout(res_box)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        rl.addWidget(self.result)
        layout.addWidget(res_box, 1)

        # --- Referencia rápida E24 ---
        ref = QLabel(
            "Valores estándar (serie E24): 1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, "
            "2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1\n"
            "Puedes escribir 10k, 4k7, 2M2, 470, 0R22. Introduciendo solo un número se "
            "interpreta en ohmios.")
        ref.setWordWrap(True)
        ref.setStyleSheet("color:#8fa3bf; font-size:11px;")
        layout.addWidget(ref)

        self.btn_calc.clicked.connect(self.calculate)
        self.btn_clear.clicked.connect(self.clear)
        for ed in (self.ed_vin, self.ed_r1, self.ed_r2, self.ed_vout):
            ed.returnPressed.connect(self.calculate)

        self._update_fields()

    def _update_fields(self):
        """Marca visualmente el campo que se va a calcular según el modo."""
        mode = self.mode.currentIndex()
        outputs = {0: self.ed_vout, 1: self.ed_r2, 2: self.ed_r1}
        for ed in (self.ed_vin, self.ed_r1, self.ed_r2, self.ed_vout):
            ed.setStyleSheet("")
        out = outputs.get(mode)
        if out is not None:
            out.setStyleSheet("background-color:#1e2a40;color:#9fb4d0;")

    # ---------------- Cálculo ----------------
    def calculate(self):
        mode = self.mode.currentIndex()
        vin = parse_number(self.ed_vin.text())
        r1 = parse_number(self.ed_r1.text())
        r2 = parse_number(self.ed_r2.text())
        vout = parse_number(self.ed_vout.text())

        if vin is None:
            self._error("Introduce Vin (tensión de entrada).")
            return

        if mode == 0:
            if not r1 or not r2:
                self._error("Introduce R1 y R2 (distintas de cero).")
                return
            vout = vin * r2 / (r1 + r2)
            self.ed_vout.setText(fmt_num(vout))
        elif mode == 1:
            if not r1 or vout is None:
                self._error("Introduce Vout y R1 (R1 distinto de cero).")
                return
            if vin <= 0:
                self._error("Vin debe ser mayor que cero.")
                return
            if vout <= 0:
                self._error("Vout debe ser mayor que cero.")
                return
            if vout >= vin:
                self._error("Vout debe ser menor que Vin en un divisor atenuador.")
                return
            r2 = r1 * vout / (vin - vout)
            self.ed_r2.setText(fmt_num(r2))
        else:  # mode == 2
            if not r2 or vout is None:
                self._error("Introduce Vout y R2 (R2 distinto de cero).")
                return
            # Vout = 0 exigiría una R1 infinita: se evita la división por cero
            # (que antes provocaba un fallo no controlado y cerraba la app).
            if vout <= 0:
                self._error("Vout debe ser mayor que cero para calcular R1.")
                return
            if vin <= 0:
                self._error("Vin debe ser mayor que cero.")
                return
            if vout >= vin:
                self._error("Vout debe ser menor que Vin en un divisor atenuador.")
                return
            r1 = r2 * (vin - vout) / vout
            self.ed_r1.setText(fmt_num(r1))

        self._show_result(vin, r1, r2, vout)

    def _show_result(self, vin, r1, r2, vout):
        total = (r1 or 0) + (r2 or 0)
        current = vin / total if total else None
        p1 = (current ** 2) * r1 if (r1 and current) else None
        p2 = (current ** 2) * r2 if (r2 and current) else None

        lines = []
        lines.append(f"<b>Vin = {fmt_v(vin)}</b>")
        lines.append(f"R1 (arriba) = {fmt_ohms(r1)}")
        lines.append(f"R2 (abajo)  = {fmt_ohms(r2)}")
        lines.append(f"<b>Vout = {fmt_v(vout)}</b>   "
                     f"({(vout / vin * 100 if vin else 0):.1f}% de Vin)")
        lines.append("")
        lines.append(f"Corriente por el divisor: <b>{fmt_a(current)}</b>")
        lines.append(f"Potencia en R1: {fmt_w(p1)}")
        lines.append(f"Potencia en R2: {fmt_w(p2)}")

        warns = []
        if p1 and p1 > 0.25:
            warns.append(f"⚠️  R1 disipa {fmt_w(p1)}: usa una resistencia de al menos "
                         f"{self._next_power(p1)}.")
        if p2 and p2 > 0.25:
            warns.append(f"⚠️  R2 disipa {fmt_w(p2)}: usa una resistencia de al menos "
                         f"{self._next_power(p2)}.")
        if current is not None and current > 0.05:
            warns.append("ℹ️  Corriente alta (>50 mA): comprueba que el divisor no "
                         "cargue en exceso la etapa anterior.")
        if warns:
            lines.append("")
            lines.extend(warns)

        lines.append("")
        lines.append("<i>Recuerda: al conectar una carga en paralelo con R2, la tensión "
                     "real baja. Si mides un Vout muy distinto, revisa R1/R2 y las "
                     "cargas conectadas.</i>")

        self.result.setHtml("<br>".join(lines))

    @staticmethod
    def _next_power(p):
        for w in (0.25, 0.5, 1.0, 2.0, 5.0, 10.0):
            if p <= w:
                return f"{w:g} W"
        return "más de 10 W"

    def _error(self, msg):
        self.result.setHtml(f"<span style='color:#ff6b6b;'>{msg}</span>")

    def clear(self):
        for ed in (self.ed_vin, self.ed_r1, self.ed_r2, self.ed_vout):
            ed.clear()
        self.result.clear()

    def prefill(self, r1=None, r2=None, vin=None):
        """Rellena el divisor con valores ya conocidos (p. ej. desde el mapa de
        interacción) y calcula Vout si hay tensión de entrada."""
        self.mode.setCurrentIndex(0)
        if r1:
            self.ed_r1.setText(str(r1))
        if r2:
            self.ed_r2.setText(str(r2))
        if vin:
            self.ed_vin.setText(str(vin))
        self._update_fields()
        if parse_number(self.ed_r1.text()) and parse_number(self.ed_r2.text()) \
                and parse_number(self.ed_vin.text()):
            self.calculate()
