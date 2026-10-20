#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from database.nomenclature_db import NomenclatureDB


class ConnectionsPanel(QWidget):
    """Muestra las conexiones del componente y permite navegar por la red del esquemático."""
    component_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nomen = NomenclatureDB()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("🔗 Seguimiento de la red del esquemático")
        f = QFont(); f.setBold(True); f.setPointSize(10)
        title.setFont(f)
        layout.addWidget(title)

        self.lbl_current = QLabel("Componente: -")
        layout.addWidget(self.lbl_current)

        grp_nets = QGroupBox("Nodos / Nets a los que pertenece")
        l1 = QVBoxLayout(grp_nets)
        self.list_nets = QListWidget()
        self.list_nets.setMaximumHeight(110)
        l1.addWidget(self.list_nets)
        layout.addWidget(grp_nets)

        grp_conn = QGroupBox("Componentes conectados (clic para seguir la línea)")
        l2 = QVBoxLayout(grp_conn)
        self.list_conn = QListWidget()
        self.list_conn.itemDoubleClicked.connect(self._on_item)
        l2.addWidget(self.list_conn)
        layout.addWidget(grp_conn)

        grp_note = QGroupBox("Análisis de la red")
        l3 = QVBoxLayout(grp_note)
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        l3.addWidget(self.txt)
        layout.addWidget(grp_note)

    def _on_item(self, item):
        self.component_clicked.emit(item.text())

    def show_component(self, designator, index):
        designator = (designator or '').upper()
        self.lbl_current.setText(f"Componente: {designator or '-'}")
        self.list_nets.clear()
        self.list_conn.clear()

        if not designator:
            self.txt.clear()
            return

        nets = index.nets_of(designator)
        for n in nets:
            self.list_nets.addItem(n)

        conns = index.connected_components(designator)
        for c in conns:
            item = QListWidgetItem(c)
            item.setToolTip("Doble clic para ver este componente")
            self.list_conn.addItem(item)

        info = self.nomen.get_info(designator)
        lines = []
        if info:
            lines.append(f"Tipo: {info.get('name', '-')}")
            if nets:
                lines.append(f"Conectado a {len(nets)} nodo(s) y {len(conns)} componente(s).")
            else:
                lines.append("Sin datos de netlist. Para ver conexiones, añade un archivo "
                             ".net/.cir o un netlist de KiCad del mismo circuito.")
            if info.get('troubleshooting'):
                lines.append("")
                lines.append("Diagnóstico: " + info['troubleshooting'])
        else:
            lines.append("Sin información en la base de conocimiento para este prefijo.")

        self.txt.setText("\n".join(lines))