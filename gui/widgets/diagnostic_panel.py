#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pestaña de diagnóstico: usos, prueba con multímetro, detección de corto,
fallos típicos y guía por síntoma para el componente seleccionado.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser,
    QApplication
)

from utils.component_symbols import component_kind, kind_name
from utils import diagnostics


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class DiagnosticPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._designator = ""
        self.init_ui()
        self.clear()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        head = QHBoxLayout()
        self.lbl_title = QLabel("🔬  Diagnóstico y pruebas")
        f = QFont(); f.setBold(True); f.setPointSize(11)
        self.lbl_title.setFont(f)
        head.addWidget(self.lbl_title)
        head.addStretch(1)
        self.btn_copy = QPushButton("📋  Copiar diagnóstico")
        self.btn_copy.clicked.connect(self.copy_all)
        head.addWidget(self.btn_copy)
        root.addLayout(head)

        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(False)
        self.view.setStyleSheet("QTextBrowser{background:#12161d;border:1px solid #2b3444;}")
        root.addWidget(self.view, 1)

    # ---------------- Contenido ----------------
    def clear(self):
        self._designator = ""
        self.lbl_title.setText("🔬  Diagnóstico y pruebas")
        self.view.setHtml(self._general_html())

    def show_component(self, designator, value="", type_name=""):
        self._designator = (designator or "").upper()
        if not self._designator:
            self.clear()
            return
        kind = component_kind(self._designator, type_name or "")
        name = kind_name(kind)
        data = diagnostics.diagnose(kind, value, self._designator, type_name)
        self.lbl_title.setText(f"🔬  Diagnóstico: {self._designator} — {name}")
        self.view.setHtml(self._component_html(data, value, name))

    def copy_all(self):
        QApplication.clipboard().setText(self.view.toPlainText())

    # ---------------- HTML ----------------
    def _component_html(self, data, value, name):
        h = []
        h.append("<div style='font-family:Segoe UI;color:#dbe3ee;'>")
        h.append(f"<h2 style='color:#7fd1a0;margin-bottom:2px'>"
                 f"{_esc(data['designator'])} — {_esc(name)}</h2>")
        if value:
            h.append(f"<p style='color:#9fb0c7;margin-top:0'>Valor detectado: "
                     f"<b style='color:#e6ecf5'>{_esc(value)}</b></p>")

        # Usos
        if data["uses"]:
            h.append("<h3 style='color:#7ec8ff'>🎯 Uso en el circuito</h3><ul>")
            for u in data["uses"]:
                h.append(f"<li>{_esc(u)}</li>")
            h.append("</ul>")

        # Prueba con multímetro
        test = data.get("test", {})
        if test:
            h.append("<h3 style='color:#7ec8ff'>🔧 Prueba con multímetro</h3>")
            if test.get("mode"):
                h.append(f"<p>Modo/escala: <b style='color:#ffd166'>"
                         f"{_esc(test['mode'])}</b></p>")
            if test.get("steps"):
                h.append("<ol>")
                for s in test["steps"]:
                    h.append(f"<li>{_esc(s)}</li>")
                h.append("</ol>")
            if data["expected"]:
                h.append("<p><b>Lecturas esperadas:</b></p><ul>")
                for e in data["expected"]:
                    h.append(f"<li>{e}</li>")
                h.append("</ul>")

        # Detección de cortocircuito
        short = data.get("short", {})
        if short:
            h.append("<h3 style='color:#ff8a80'>🔴 Detección de cortocircuito</h3>")
            if short.get("steps"):
                h.append("<ol>")
                for s in short["steps"]:
                    h.append(f"<li>{_esc(s)}</li>")
                h.append("</ol>")
            rows = short.get("rows", [])
            if rows:
                h.append("<table border='1' cellspacing='0' cellpadding='5' "
                         "width='100%' style='border-color:#3a465a'>")
                h.append("<tr style='background:#1c2431'>"
                         "<th align='left'>Estado</th>"
                         "<th align='left'>Lectura del multímetro</th>"
                         "<th align='left'>Qué significa</th></tr>")
                for estado, lectura, sig in rows:
                    col = {"Bueno": "#7fd1a0", "En corto": "#ff8a80"}.get(estado, "#e6ecf5")
                    h.append(f"<tr><td style='color:{col}'><b>{_esc(estado)}</b></td>"
                             f"<td>{_esc(lectura)}</td><td>{_esc(sig)}</td></tr>")
                h.append("</table>")

        # Fallos típicos
        if data["faults"]:
            h.append("<h3 style='color:#7ec8ff'>📋 Fallos típicos</h3>")
            h.append("<table border='1' cellspacing='0' cellpadding='5' width='100%' "
                     "style='border-color:#3a465a'>")
            h.append("<tr style='background:#1c2431'>"
                     "<th align='left'>Fallo</th><th align='left'>Síntoma</th>"
                     "<th align='left'>Firma en multímetro</th>"
                     "<th align='left'>Causa / nota</th></tr>")
            for row in data["faults"]:
                fault, sym, sig, cause = (list(row) + ["", "", "", ""])[:4]
                h.append(f"<tr><td style='color:#ffd166'><b>{_esc(fault)}</b></td>"
                         f"<td>{_esc(sym)}</td><td>{_esc(sig)}</td>"
                         f"<td>{_esc(cause)}</td></tr>")
            h.append("</table>")

        # Guía por síntoma del componente
        if data["symptoms"]:
            h.append("<h3 style='color:#7ec8ff'>🩺 Guía por síntoma</h3>")
            for sym, checks in data["symptoms"].items():
                h.append(f"<p style='margin-bottom:2px'><b style='color:#e6ecf5'>"
                         f"{_esc(sym)}</b></p><ul style='margin-top:0'>")
                for c in checks:
                    h.append(f"<li>{_esc(c)}</li>")
                h.append("</ul>")

        # Seguridad
        if data["safety"]:
            h.append("<h3 style='color:#ff8a80'>⚠️ Seguridad</h3><ul>")
            for s in data["safety"]:
                h.append(f"<li>{_esc(s)}</li>")
            h.append("</ul>")

        # Guía general
        h.append(self._general_section())
        h.append("</div>")
        return "".join(h)

    def _general_section(self):
        h = ["<h3 style='color:#7ec8ff'>🧭 Guía rápida general (cualquier aparato)</h3>"]
        for sym, checks in diagnostics.GENERAL_SYMPTOMS.items():
            h.append(f"<p style='margin-bottom:2px'><b style='color:#e6ecf5'>"
                     f"{_esc(sym)}</b></p><ul style='margin-top:0'>")
            for c in checks:
                h.append(f"<li>{_esc(c)}</li>")
            h.append("</ul>")
        return "".join(h)

    def _general_html(self):
        h = ["<div style='font-family:Segoe UI;color:#dbe3ee;'>"]
        h.append("<h2 style='color:#7fd1a0'>🔬 Diagnóstico y pruebas</h2>")
        h.append("<p style='color:#9fb0c7'>Selecciona un componente en los "
                 "resultados para ver: usos, cómo medirlo con el multímetro, "
                 "cómo detectar un cortocircuito y sus fallos típicos.</p>")
        h.append("<h3 style='color:#7ec8ff'>📏 Cómo detectar un cortocircuito "
                 "(método general)</h3>")
        h.append("<ol>"
                 "<li>Equipo <b>desenchufado</b> y condensadores descargados.</li>"
                 "<li>Multímetro en <b>continuidad (🔔)</b> o en Ω mínimo.</li>"
                 "<li>Mide entre los dos terminales del componente sospechoso.</li>"
                 "<li><b>0 Ω / pitido fijo</b> = probable corto.</li>"
                 "<li>O.L. en dos puntos que deben unirse = abierto.</li>"
                 "<li>Con la placa alimentada, mide tensiones y compara con el "
                 "esquema.</li>"
                 "<li>Confirma levantando un terminal para descartar caminos en "
                 "paralelo.</li>"
                 "</ol>")
        h.append("<h3 style='color:#ff8a80'>🧰 Imprescindible</h3><ul>"
                 "<li>Multímetro (V, Ω, continuidad, modo diodo, capacímetro).</li>"
                 "<li>Fuente de alimentación regulable y limitada en corriente.</li>"
                 "<li>Osciloscopio (para osciladores y señales).</li>"
                 "<li>Soldador, estaño, malla, alcohol y lupa.</li>"
                 "</ul>")
        h.append("<h3 style='color:#ff8a80'>⚠️ Reglas de oro</h3><ul>"
                 "<li>Nunca puentees un fusible sin encontrar la causa.</li>"
                 "<li>Descarga los condensadores antes de medir Ω.</li>"
                 "<li>Al medir Ω/continuidad, el circuito debe estar SIN tensión.</li>"
                 "<li>Un corto casi siempre es: semiconductores, condensadores o "
                 "aislamientos.</li>"
                 "</ul>")
        h.append(self._general_section())
        h.append("</div>")
        return "".join(h)
