#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QGroupBox, QScrollArea, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database.nomenclature_db import NomenclatureDB

class NomenclaturePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = NomenclatureDB()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        title = QLabel("📚 Base de conocimiento de nomenclatura")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        title.setFont(font)
        layout.addWidget(title)

        # Todo el contenido va dentro de un área con scroll: en pantallas bajas
        # se puede desplazar en lugar de recortarse.
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 6, 0)
        inner = self.content_layout

        # Info general
        self.lbl_designator = QLabel("Designador: -")
        self.lbl_name = QLabel("Nombre: -")
        self.lbl_name.setWordWrap(True)
        self.lbl_unit = QLabel("Unidad: -")
        inner.addWidget(self.lbl_designator)
        inner.addWidget(self.lbl_name)
        inner.addWidget(self.lbl_unit)

        # Grupos
        self.grp_what = QGroupBox("¿Qué hace?")
        lay_what = QVBoxLayout(self.grp_what)
        self.txt_what = QTextEdit()
        self.txt_what.setReadOnly(True)
        self.txt_what.setMinimumHeight(70)
        lay_what.addWidget(self.txt_what)
        inner.addWidget(self.grp_what)

        self.grp_trouble = QGroupBox("Solución de fallos / Recomendaciones")
        lay_trouble = QVBoxLayout(self.grp_trouble)
        self.txt_trouble = QTextEdit()
        self.txt_trouble.setReadOnly(True)
        self.txt_trouble.setMinimumHeight(110)
        lay_trouble.addWidget(self.txt_trouble)
        inner.addWidget(self.grp_trouble)

        self.grp_symptoms = QGroupBox("Síntomas típicos")
        lay_sym = QVBoxLayout(self.grp_symptoms)
        self.txt_sym = QTextEdit()
        self.txt_sym.setReadOnly(True)
        self.txt_sym.setMinimumHeight(60)
        lay_sym.addWidget(self.txt_sym)
        inner.addWidget(self.grp_symptoms)

        # Tips generales
        self.grp_tips = QGroupBox("Consejos prácticos (real para reparación)")
        lay_tips = QVBoxLayout(self.grp_tips)
        self.txt_tips = QTextEdit()
        self.txt_tips.setReadOnly(True)
        self.txt_tips.setMinimumHeight(110)
        data = self.db.get_all()
        tips = "\n".join(["• " + t for t in data.get('tips', [])])
        self.txt_tips.setText(tips)
        lay_tips.addWidget(self.txt_tips)
        inner.addWidget(self.grp_tips)

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def clear(self):
        """Deja el panel en blanco (al vaciar el aparato o limpiar la búsqueda)."""
        self.lbl_designator.setText("Designador: -")
        self.lbl_name.setText("Nombre: -")
        self.lbl_unit.setText("Unidad: -")
        self.txt_what.clear()
        self.txt_trouble.clear()
        self.txt_sym.clear()

    def show_info(self, designator: str):
        info = self.db.get_info(designator)
        if not info:
            self.lbl_designator.setText(f"Designador: {designator.upper()}")
            self.lbl_name.setText("Nombre: No encontrado en base de conocimiento")
            self.lbl_unit.setText("Unidad: -")
            self.txt_what.clear()
            self.txt_trouble.clear()
            self.txt_sym.clear()
            return
        self.lbl_designator.setText(f"Designador: {designator.upper()}")
        self.lbl_name.setText(f"Nombre: {info.get('name','-')}")
        self.lbl_unit.setText(f"Unidad: {info.get('unit','-')}")
        self.txt_what.setText(info.get('what_it_does','-'))
        self.txt_trouble.setText(info.get('troubleshooting','-'))
        self.txt_sym.setText("\n".join(info.get('symptoms', [])) if info.get('symptoms') else "-")