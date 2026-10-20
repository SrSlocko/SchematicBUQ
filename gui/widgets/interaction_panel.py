#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pestaña INTERACCIÓN: cómo funciona un componente y con quién se relaciona.

Responde, en lenguaje sencillo, a tres preguntas:

  * ¿Para qué está este componente en el circuito?  (rol)
  * ¿Cómo se comporta?                              (comportamiento + fórmulas)
  * ¿Con quién interactúa y qué pasa si falla?       (vecinos y consecuencias)

Arriba hay un MAPA DE INTERACCIÓN dibujado con QPainter: el componente elegido
en el centro y sus vecinos alrededor. Los nodos son clicables para seguir
«paseando» por el circuito, y el panel avisa de si esas relaciones vienen de un
netlist real o se han inferido por proximidad en la hoja.
"""
import math

from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import (QColor, QFont, QFontMetrics, QPainter, QPen, QBrush)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser,
    QSizePolicy, QToolTip
)

from utils.component_symbols import kind_name
from utils import interaction as I


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


_KIND_COLORS = {
    "resistor": "#e8a33d", "resistor_network": "#e8a33d", "potentiometer": "#e8a33d",
    "thermistor": "#e8a33d", "varistor": "#e8a33d",
    "capacitor": "#4a90d9", "electrolytic": "#4a90d9",
    "inductor": "#45c1a8", "ferrite": "#45c1a8", "filter": "#45c1a8",
    "crystal": "#45c1a8", "transformer": "#45c1a8",
    "diode": "#a06be0", "zener": "#a06be0", "tvs": "#a06be0", "led": "#a06be0",
    "photodiode": "#a06be0", "bridge": "#a06be0", "transistor": "#a06be0",
    "fet": "#a06be0", "ic": "#a06be0",
    "connector": "#8b97a8", "switch": "#8b97a8", "jumper": "#8b97a8",
    "fuse": "#8b97a8", "testpoint": "#8b97a8", "terminal": "#8b97a8",
    "battery": "#e5534b", "power": "#e5534b", "generator": "#e5534b",
    "motor": "#d98cb3", "solenoid": "#d98cb3", "speaker": "#d98cb3",
    "mic": "#d98cb3", "antenna": "#d98cb3",
}


def kind_color(kind):
    return QColor(_KIND_COLORS.get(kind, "#9aa5b1"))


class InteractionMap(QWidget):
    """Mapa radial: componente en el centro y vecinos alrededor."""

    nodeClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self._center = None          # dict
        self._neighbors = []         # list[dict]
        self._real_nets = False
        self._nodes = []             # [(x, y, r, entry, is_center)]
        self._hover = None

    def set_graph(self, center, neighbors, real_nets=False, max_nodes=12):
        self._center = center
        self._neighbors = list(neighbors or [])[:max_nodes]
        self._real_nets = real_nets
        self._hover = None
        self._relayout()
        self.update()

    def clear(self):
        self._center = None
        self._neighbors = []
        self._nodes = []
        self._hover = None
        self.update()

    # ---------- geometría ----------
    def _relayout(self):
        self._nodes = []
        if not self._center:
            return
        w, h = max(self.width(), 220), max(self.height(), 200)
        cx, cy = w / 2.0, h / 2.0
        self._nodes.append((cx, cy, 26.0, self._center, True))
        n = len(self._neighbors)
        if not n:
            return
        rx = max(60.0, w / 2.0 - 78.0)
        ry = max(45.0, h / 2.0 - 58.0)
        for i, nb in enumerate(self._neighbors):
            ang = -math.pi / 2.0 + (2.0 * math.pi * i / n)
            x = cx + rx * math.cos(ang)
            y = cy + ry * math.sin(ang)
            self._nodes.append((x, y, 18.0, nb, False))

    def resizeEvent(self, ev):
        self._relayout()
        super().resizeEvent(ev)

    # ---------- ratón ----------
    def _node_at(self, pos):
        for x, y, r, entry, is_center in self._nodes:
            if (pos.x() - x) ** 2 + (pos.y() - y) ** 2 <= (r + 4) ** 2:
                return entry
        return None

    def mouseMoveEvent(self, ev):
        entry = self._node_at(ev.pos())
        self._hover = (entry or {}).get("designator") if entry else None
        if entry:
            txt = entry.get("designator", "")
            k = entry.get("kind", "")
            if k:
                txt += f" — {kind_name(k)}"
            if entry.get("value"):
                txt += f" ({entry['value']})"
            QToolTip.showText(ev.globalPos(), txt, self)
        else:
            QToolTip.hideText()
        self.update()

    def mousePressEvent(self, ev):
        entry = self._node_at(ev.pos())
        if entry and not entry.get("is_center"):
            self.nodeClicked.emit(entry.get("designator", ""))

    def leaveEvent(self, ev):
        self._hover = None
        self.update()

    # ---------- pintura ----------
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor("#1b2029"))

        if not self._center:
            p.setPen(QColor("#6b7686"))
            f = QFont(); f.setPointSize(10)
            p.setFont(f)
            p.drawText(self.rect(), Qt.AlignCenter,
                       "Selecciona un componente para ver su mapa de interacción")
            return

        # Aristas centro -> vecino
        cx, cy = self._nodes[0][0], self._nodes[0][1]
        pen = QPen(QColor("#39414f"), 2)
        if not self._real_nets:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        for x, y, r, entry, is_center in self._nodes[1:]:
            p.drawLine(QPointF(cx, cy), QPointF(x, y))

        fm = QFontMetrics(QFont("Segoe UI", 8))
        for x, y, r, entry, is_center in self._nodes:
            color = kind_color(entry.get("kind", ""))
            hovered = entry.get("designator") and entry.get("designator") == self._hover
            if is_center:
                color = QColor("#2d6cdf")
            # sombra
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, 70)))
            p.drawEllipse(QPointF(x + 1.5, y + 2.0), r, r)
            # cuerpo
            p.setBrush(QBrush(color))
            p.setPen(QPen(QColor("#eef2f8") if hovered else QColor("#10141b"),
                          2.5 if hovered else 1.5))
            p.drawEllipse(QPointF(x, y), r, r)

            # designador centrado en el nodo
            f = QFont("Segoe UI", 9 if is_center else 8)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor("#0b0e13"))
            p.drawText(QRectF(x - r, y - r, 2 * r, 2 * r), Qt.AlignCenter,
                       entry.get("designator", ""))

            # etiquetas debajo
            f2 = QFont("Segoe UI", 7)
            p.setFont(f2)
            p.setPen(QColor("#c7d0dc"))
            val = entry.get("value", "")
            txt = val if val else kind_name(entry.get("kind", ""))
            txt = fm.elidedText(txt, Qt.ElideRight, 92)
            p.drawText(QRectF(x - 46, y + r + 1, 92, 12), Qt.AlignHCenter, txt)

        # leyenda de origen
        p.setFont(QFont("Segoe UI", 7))
        p.setPen(QColor("#6b7686"))
        if self._real_nets:
            p.drawText(QRectF(6, 4, self.width() - 12, 12), Qt.AlignLeft,
                       "Conexiones reales del netlist")
        else:
            p.drawText(QRectF(6, 4, self.width() - 12, 12), Qt.AlignLeft,
                       "Vecinos inferidos por proximidad en la hoja (pulsa para navegar)")


class InteractionPanel(QWidget):
    """Pestaña de interacción y comportamiento del componente."""

    component_clicked = pyqtSignal(str)   # navegar a otro componente
    open_requested = pyqtSignal(str)      # abrir en el visor
    tab_requested = pyqtSignal(str)       # "multimetro" / "diagnostico" / "esquematico"
    back_requested = pyqtSignal()         # volver al componente anterior
    divider_requested = pyqtSignal(str, str)   # (R1, R2) -> calculadora

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
        title = QLabel("🔄  Interacción y comportamiento")
        f = QFont(); f.setBold(True); f.setPointSize(11)
        title.setFont(f)
        head.addWidget(title)
        head.addStretch(1)

        self.btn_back = QPushButton("◀ Volver")
        self.btn_back.setToolTip("Regresa al componente que estabas viendo antes")
        self.btn_back.clicked.connect(self.back_requested.emit)
        head.addWidget(self.btn_back)

        self.btn_view = QPushButton("🎯 Ver en el esquemático")
        self.btn_view.clicked.connect(lambda: self.open_requested.emit(self._designator))
        head.addWidget(self.btn_view)

        self.btn_multi = QPushButton("🔌 Multímetro")
        self.btn_multi.clicked.connect(lambda: self.tab_requested.emit("multimetro"))
        head.addWidget(self.btn_multi)

        self.btn_diag = QPushButton("🔬 Diagnóstico")
        self.btn_diag.clicked.connect(lambda: self.tab_requested.emit("diagnostico"))
        head.addWidget(self.btn_diag)
        root.addLayout(head)

        self.lbl_component = QLabel("Componente: —")
        self.lbl_component.setStyleSheet("color:#9fb0c6; font-size:13px;")
        root.addWidget(self.lbl_component)

        self.map = InteractionMap()
        self.map.nodeClicked.connect(self._on_node_clicked)
        root.addWidget(self.map, 1)

        self.txt = QTextBrowser()
        self.txt.setOpenLinks(False)
        self.txt.anchorClicked.connect(self._on_anchor)
        self.txt.setStyleSheet("QTextBrowser { font-size: 13px; }")
        root.addWidget(self.txt, 2)

    # ---------- API ----------
    def show_component(self, des, value="", ctype="", source="", index=None,
                       file_path="", page=0):
        des = (des or "").upper()
        self._designator = des
        if not des or index is None:
            self.clear()
            return

        info = I.build(index, des, value=value, type_name=ctype,
                       file_path=file_path, page=page)
        kind = info["kind"]
        kname = info["kind_name"]
        val = value or ""
        head = f"{des} — {kname}"
        if val:
            head += f" — {val}"
        self.lbl_component.setText(head)

        self.map.set_graph(
            {"designator": des, "kind": kind, "value": val},
            [{"designator": n["designator"], "kind": n["kind"],
              "value": n.get("value", "")} for n in info["neighbors"]],
            real_nets=info["real_nets"])

        self.txt.setHtml(self._html(info, val))
        self.btn_view.setEnabled(True)
        self.btn_back.setEnabled(True)

    def clear(self):
        self._designator = ""
        self.lbl_component.setText("Componente: —")
        self.map.clear()
        self.txt.setHtml(
            "<p style='color:#8b97a8'>Selecciona un componente para ver "
            "<b>cómo funciona</b>, <b>con quién interactúa</b> y <b>qué pasa si falla</b>.</p>")
        self.btn_view.setEnabled(False)
        self.btn_back.setEnabled(False)

    # ---------- HTML ----------
    def _html(self, info, value=""):
        h = []
        h.append("<div style='font-size:13px'>")

        h.append("<h3 style='color:#6fb1ff;margin-bottom:2px'>🧠 Rol en el circuito</h3>")
        h.append(f"<p style='margin-top:0'>{info['role']}</p>")

        h.append("<h3 style='color:#6fb1ff;margin-bottom:2px'>⚙️ Cómo se comporta</h3><ul>")
        for b in info["behavior"]:
            h.append(f"<li>{b}</li>")
        h.append("</ul>")

        # Vecinos
        h.append("<h3 style='color:#6fb1ff;margin-bottom:2px'>🤝 Con quién interactúa</h3>")
        nbs = info["neighbors"]
        if nbs:
            if info["real_nets"]:
                h.append("<p style='color:#7fd1a0;margin:0 0 4px 0'>"
                         "Relaciones tomadas del <b>netlist</b> del proyecto (conexiones reales).</p>")
            else:
                h.append("<p style='color:#e8c05a;margin:0 0 4px 0'>"
                         "No hay netlist: son los componentes <b>de la misma zona de la "
                         "hoja</b> (relación probable, no confirmada eléctricamente). "
                         "Pulsa cualquiera para explorarlo.</p>")
            h.append("<ul>")
            for n in nbs:
                k = n.get("kind", "")
                rel = I.relation_text(info["kind"], k)
                val = n.get("value", "")
                extra = f" — {val}" if val else ""
                net = n.get("net", "")
                net_txt = ""
                if info["real_nets"] and net:
                    net_txt = f" <span style='color:#8b97a8'>[net { _esc(net) }]</span>"
                elif not info["real_nets"]:
                    net_txt = ""
                rel_txt = f"<br><span style='color:#9fb0c6'>{rel}</span>" if rel else ""
                h.append(
                    f"<li><a href='des:{_esc(n['designator'])}' "
                    f"style='color:#ffcf6b;text-decoration:none'><b>{_esc(n['designator'])}</b></a>"
                    f" <span style='color:#c7d0dc'>{kind_name(k)}{extra}</span>"
                    f"{net_txt}{rel_txt}</li>")
            h.append("</ul>")
        else:
            h.append("<p style='color:#8b97a8'>No se han encontrado componentes "
                     "cerca en el esquemático. Añade el <b>netlist</b> del proyecto "
                     "(KiCad/EasyEDA/Altium/.net) para ver las conexiones reales.</p>")

        # Subcircuitos
        subs = info["subcircuits"]
        h.append("<h3 style='color:#6fb1ff;margin-bottom:2px'>🔗 Subcircuitos típicos detectados</h3>")
        if subs:
            div_vals = self._divider_values(info, value)
            for title, text in subs:
                h.append(f"<p style='margin:0 0 6px 0'><b style='color:#c8e6a0'>{title}</b><br>"
                         f"<span style='color:#c7d0dc'>{text}</span></p>")
                if div_vals and "divisor" in title.lower():
                    a, b = div_vals
                    h.append(
                        f"<p style='margin:-2px 0 8px 0'>"
                        f"<a href='div:{_esc(a)}|{_esc(b)}' style='color:#ffcf6b;"
                        f"text-decoration:none'>🧮 Calcular este divisor con "
                        f"{_esc(a)} y {_esc(b)} →</a></p>")
        else:
            h.append("<p style='color:#8b97a8'>No se reconoce ningún subcircuito "
                     "típico con los componentes cercanos.</p>")

        # Impacto de fallo
        imp = info["impact"]
        if imp:
            h.append("<h3 style='color:#6fb1ff;margin-bottom:2px'>💥 Si falla, qué pasa en el circuito</h3><ul>")
            for fallo, efecto in imp:
                h.append(f"<li><b>{_esc(fallo)}</b>: {_esc(efecto)}</li>")
            h.append("</ul>")

        h.append("</div>")
        return "".join(h)

    # ---------- señales internas ----------
    @staticmethod
    def _divider_values(info, value=""):
        """Dos valores de resistencia (el del componente + el de un vecino) para
        poder llevar el divisor a la calculadora."""
        vals = []
        if info["kind"] == "resistor" and value:
            vals.append(value)
        for n in info["neighbors"]:
            if n.get("kind") == "resistor" and n.get("value"):
                vals.append(n["value"])
        return (vals[0], vals[1]) if len(vals) >= 2 else None

    def _on_anchor(self, url):
        s = url.toString() if hasattr(url, "toString") else str(url)
        if s.startswith("des:"):
            self.component_clicked.emit(s[4:])
        elif s.startswith("div:"):
            body = s[4:]
            if "|" in body:
                a, b = body.split("|", 1)
                self.divider_requested.emit(a, b)

    def _on_node_clicked(self, des):
        if des:
            self.component_clicked.emit(des)
