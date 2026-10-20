#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pestaña MULTÍMETRO: guía práctica y interactiva para medir el componente.

Se abre sola al seleccionar un componente e indica:

  * Cómo preparar el polímetro (modo/escala) y avisos de seguridad.
  * Los pasos concretos de medición.
  * Las LECTURAS ESPERADAS calculadas con el valor real del componente.
  * Un verificador interactivo: eliges lo que marca tu multímetro y la app
    te dice si el componente está BUENO, EN CORTO o ABIERTO y qué hacer.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser,
    QFrame, QApplication, QSizePolicy
)

from utils.component_symbols import component_kind, kind_name
from utils import diagnostics


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _verdict(estado, lectura, significado):
    """Devuelve (emoji, color, titulo, consejo) para un estado medido."""
    e = (estado or "").lower()
    if e.startswith("bueno") or "correcto" in e:
        return ("✅", "#7fd1a0", "COMPONENTE BUENO",
                "La lectura coincide con lo esperado: el componente está bien. "
                "No lo sustituyas; el fallo está en otra parte del circuito.")
    if "corto" in e or "pegado" in e:
        return ("🔴", "#ff8a80", "EN CORTOCIRCUITO",
                "Cortocircuito confirmado. Sustituye el componente y, antes de "
                "volver a encender, busca la causa (otro componente en corto, "
                "sobrecarga o pico de tensión) para que no vuelva a fallar.")
    if "fundido" in e:
        return ("🔴", "#ff8a80", "FUSIBLE FUNDIDO",
                "El fusible se ha sacrificado. NO lo puentees ni pongas uno de "
                "más amperaje: primero mide en modo diodo/Ω el puente "
                "rectificador, el condensador de filtrado y el transistor de "
                "conmutación para encontrar el corto que lo fundió.")
    if "invertido" in e:
        return ("🟡", "#ffd166", "MONTADO AL REVÉS",
                "Revisa la polaridad: un electrolítico invertido se calienta y "
                "revienta. Móntalo con el positivo y la franja blanca correctos.")
    if "abierto" in e or e in ("o.l.", "ol", "∞"):
        return ("🟠", "#ffb74d", "ABIERTO (O.L.)",
                "El componente está interrumpido. Sustitúyelo por uno igual "
                "(mismo valor y, si es condensador, misma tensión o superior).")
    if "seco" in e or "agotad" in e or "pérdida" in e or "degrad" in e or "desvalor" in e:
        return ("🟡", "#ffd166", "DEGRADADO",
                "El componente ha perdido sus características aunque no esté en "
                "corto. Cámbialo, sobre todo si el equipo falla en caliente.")
    if "falso" in e or "sucio" in e or "intermitente" in e:
        return ("🟡", "#ffd166", "CONTACTO DEFECTUOSO",
                "Lectura inestable o alta: limpia y resuelda las conexiones. "
                "Si sigue igual, sustituye el componente.")
    if "sin aliment" in e:
        return ("🔵", "#7ec8ff", "SIN ALIMENTACIÓN",
                "El componente no recibe tensión: el problema está antes "
                "(fusible, pista, regulador). Sigue el circuito hacia la fuente.")
    return ("🔎", "#dbe3ee", (estado or "RESULTADO").upper(),
            significado or "Compara con el esquemático y con un componente igual "
                           "que funcione.")


class MultimeterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._designator = ""
        self._data = None
        self._rows = []
        self._buttons = []
        self.init_ui()
        self.clear()

    # ---------------- UI ----------------
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        head = QHBoxLayout()
        self.lbl_title = QLabel("🔌  Multímetro")
        f = QFont(); f.setBold(True); f.setPointSize(12)
        self.lbl_title.setFont(f)
        head.addWidget(self.lbl_title)
        head.addStretch(1)
        self.btn_copy = QPushButton("📋  Copiar")
        self.btn_copy.clicked.connect(self.copy_all)
        head.addWidget(self.btn_copy)
        root.addLayout(head)

        # Verificador interactivo
        self.box_check = QFrame()
        self.box_check.setStyleSheet(
            "QFrame{background:#1a212b;border:1px solid #3a465a;border-radius:8px;}")
        bl = QVBoxLayout(self.box_check)
        bl.setSpacing(4)
        self.lbl_ask = QLabel("¿Qué marca tu multímetro? Pulsa el resultado:")
        self.lbl_ask.setStyleSheet("color:#c7d2e0;")
        qf = QFont(); qf.setBold(True); qf.setPointSize(10)
        self.lbl_ask.setFont(qf)
        bl.addWidget(self.lbl_ask)

        self.row_btns = QHBoxLayout()
        self.row_btns.setSpacing(6)
        bl.addLayout(self.row_btns)

        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        self.lbl_result.setTextFormat(Qt.RichText)
        self.lbl_result.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        bl.addWidget(self.lbl_result)
        root.addWidget(self.box_check)

        # Procedimiento (HTML)
        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(False)
        self.view.setStyleSheet(
            "QTextBrowser{background:#12161d;border:1px solid #2b3444;}")
        root.addWidget(self.view, 1)

    # ---------------- Datos ----------------
    def clear(self):
        self._designator = ""
        self._data = None
        self._rows = []
        self.lbl_title.setText("🔌  Multímetro")
        self.box_check.setVisible(False)
        self.lbl_result.setText("")
        self._clear_buttons()
        self.view.setHtml(self._intro_html())

    def _clear_buttons(self):
        for b in self._buttons:
            self.row_btns.removeWidget(b)
            b.deleteLater()
        self._buttons = []
        # Elimina también los spacers añadidos por _build_buttons: si no, se
        # acumulan en cada reconstrucción y deforman la fila de botones.
        while self.row_btns.count():
            item = self.row_btns.takeAt(0)
            w = item.widget()
            if w is not None and w not in self._buttons:
                w.deleteLater()

    def show_component(self, designator, value="", type_name=""):
        self._designator = (designator or "").upper()
        if not self._designator:
            self.clear()
            return
        kind = component_kind(self._designator, type_name or "")
        name = kind_name(kind)
        data = diagnostics.diagnose(kind, value, self._designator, type_name)
        self._data = data
        self._rows = list(data.get("short", {}).get("rows", []) or [])

        self.lbl_title.setText(
            f"🔌  Multímetro: {self._designator} — {name}")
        self._build_buttons()
        self.lbl_result.setText(
            "<span style='color:#9fb0c7'>Mide con el polímetro y pulsa arriba "
            "la lectura que obtengas para saber si está en corto.</span>")
        self.view.setHtml(self._component_html(data, value, name))

    def _build_buttons(self):
        self._clear_buttons()
        if not self._rows:
            self.box_check.setVisible(False)
            return
        self.box_check.setVisible(True)
        for idx, row in enumerate(self._rows):
            estado = row[0] if row else ""
            emoji, color, _, _ = _verdict(estado, "", "")
            btn = QPushButton(f"{emoji}  {estado}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton{background:#232c39;border:1px solid #3a465a;"
                "border-radius:6px;padding:6px 10px;color:%s;}"
                "QPushButton:hover{background:#2c3746;}" % color)
            btn.clicked.connect(lambda _=False, i=idx: self._on_state(i))
            self.row_btns.addWidget(btn)
            self._buttons.append(btn)
        self.row_btns.addStretch(1)

    def _on_state(self, i):
        if i < 0 or i >= len(self._rows):
            return
        estado, lectura, significado = (list(self._rows[i]) + ["", "", ""])[:3]
        emoji, color, titulo, consejo = _verdict(estado, lectura, significado)
        html = [f"<div style='font-size:11pt'>"
                f"<span style='color:{color}'><b>{emoji} {_esc(titulo)}</b></span><br>"
                f"<span style='color:#c7d2e0'>Lectura: <b>{_esc(lectura)}</b></span><br>"
                f"<span style='color:#dbe3ee'>{_esc(consejo)}</span></div>"]
        self.lbl_result.setText("".join(html))

    def copy_all(self):
        txt = self.view.toPlainText()
        if self.lbl_result.text():
            txt += "\n\n--- Verificación ---\n" + self.lbl_result.text()
        QApplication.clipboard().setText(txt)

    # ---------------- HTML ----------------
    def _component_html(self, data, value, name):
        h = ["<div style='font-family:Segoe UI;color:#dbe3ee;'>"]
        h.append("<p style='color:#9fb0c7;margin-top:0'>Trabaja SIEMPRE con el "
                 "equipo <b>desenchufado</b> y los condensadores descargados "
                 "cuando midas Ω, continuidad o modo diodo.</p>")

        test = data.get("test", {})
        h.append("<h3 style='color:#7ec8ff'>1. Prepara el instrumento</h3>")
        if test.get("mode"):
            h.append(f"<p>Modo / escala: <b style='color:#ffd166;font-size:12pt'>"
                     f"{_esc(test['mode'])}</b></p>")
        if test.get("steps"):
            h.append("<ol>")
            for s in test["steps"]:
                h.append(f"<li>{_esc(s)}</li>")
            h.append("</ol>")

        if data.get("expected"):
            h.append("<h3 style='color:#7ec8ff'>2. Lecturas esperadas</h3><ul>")
            for e in data["expected"]:
                h.append(f"<li>{e}</li>")
            h.append("</ul>")

        short = data.get("short", {})
        if short:
            h.append("<h3 style='color:#ff8a80'>3. ¿Está en corto? "
                     "Cómo comprobarlo</h3>")
            if short.get("steps"):
                h.append("<ol>")
                for s in short["steps"]:
                    h.append(f"<li>{_esc(s)}</li>")
                h.append("</ol>")
            rows = short.get("rows", [])
            if rows:
                h.append(self._rows_table(rows))

        if data["faults"]:
            h.append("<h3 style='color:#7ec8ff'>Fallos típicos y su firma</h3>")
            h.append("<table border='1' cellspacing='0' cellpadding='5' width='100%' "
                     "style='border-color:#3a465a'>")
            h.append("<tr style='background:#1c2431'>"
                     "<th align='left'>Fallo</th><th align='left'>Síntoma</th>"
                     "<th align='left'>Multímetro</th><th align='left'>Causa</th></tr>")
            for row in data["faults"]:
                fault, sym, sig, cause = (list(row) + ["", "", "", ""])[:4]
                h.append(f"<tr><td style='color:#ffd166'><b>{_esc(fault)}</b></td>"
                         f"<td>{_esc(sym)}</td><td>{_esc(sig)}</td>"
                         f"<td>{_esc(cause)}</td></tr>")
            h.append("</table>")

        if data.get("safety"):
            h.append("<h3 style='color:#ff8a80'>⚠️ Seguridad</h3><ul>")
            for s in data["safety"]:
                h.append(f"<li>{_esc(s)}</li>")
            h.append("</ul>")

        h.append("<p style='color:#9fb0c7'>Para el análisis completo (usos, "
                 "guía por síntoma y seguridad ampliada) abre la pestaña "
                 "<b>🔬 Diagnóstico y pruebas</b>.</p>")
        h.append("</div>")
        return "".join(h)

    def _rows_table(self, rows):
        h = ["<table border='1' cellspacing='0' cellpadding='6' width='100%' "
             "style='border-color:#3a465a'>"
             "<tr style='background:#1c2431'>"
             "<th align='left'>Estado</th>"
             "<th align='left'>Lectura del multímetro</th>"
             "<th align='left'>Qué significa</th></tr>"]
        for row in rows:
            estado, lectura, sig = (list(row) + ["", "", ""])[:3]
            emoji, color, _, _ = _verdict(estado, lectura, sig)
            h.append(f"<tr><td style='color:{color}'><b>{emoji} {_esc(estado)}</b></td>"
                     f"<td>{_esc(lectura)}</td><td>{_esc(sig)}</td></tr>")
        h.append("</table>")
        return "".join(h)

    def _intro_html(self):
        return (
            "<div style='font-family:Segoe UI;color:#dbe3ee;'>"
            "<h2 style='color:#7fd1a0'>🔌 Multímetro</h2>"
            "<p style='color:#9fb0c7'>Selecciona un componente en los resultados "
            "y esta pestaña te dirá, paso a paso, cómo medirlo, qué lectura debes "
            "obtener y cómo saber si está EN CORTO, ABIERTO o BUENO.</p>"
            "<h3 style='color:#7ec8ff'>Reglas antes de medir</h3><ol>"
            "<li>Equipo <b>desenchufado</b> y condensadores grandes descargados.</li>"
            "<li>Multímetro en <b>Ω</b> o <b>continuidad (🔔)</b> para resistencias, "
            "bobinas, fusibles y cortos.</li>"
            "<li>En <b>modo diodo (→|)</b> para diodos, LEDs, transistores y MOSFET.</li>"
            "<li>0 Ω fijo o pitido continuo = <b>corto</b>; O.L./∞ = <b>abierto</b>.</li>"
            "<li>Con la placa alimentada mide <b>tensiones (V)</b> y compáralas "
            "con el esquemático.</li>"
            "</ol>"
            "<h3 style='color:#ff8a80'>Truco para localizar cortos</h3><ol>"
            "<li>Con la placa sin tensión, mide la resistencia de la línea de "
            "alimentación a masa.</li>"
            "<li>Si da ~0 Ω, ve levantando un terminal de los sospechosos "
            "(condensadores, semiconductores) hasta que desaparezca el corto.</li>"
            "<li>También sirve alimentar con fuente limitada en corriente: el "
            "componente en corto se calienta (o usa alcohol/frío localizado).</li>"
            "</ol></div>")
