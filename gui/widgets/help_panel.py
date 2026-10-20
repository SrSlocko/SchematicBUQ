#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pestaña de AYUDA: guía paso a paso y glosario para quien empieza.

Está pensada para que alguien sin experiencia sepa qué hacer: los pasos
numerados llevan botones que ejecutan la acción directamente.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser,
    QGroupBox, QGridLayout
)


class HelpPanel(QWidget):
    """Guía de uso. Emite `action` con la acción pedida por el usuario."""
    action = pyqtSignal(str)

    STEPS = [
        ("1", "Elige tu aparato",
         "En «Aparato/equipo activo» selecciona el equipo que vas a reparar "
         "(por ejemplo Ampeg_B2R). Si aún no existe, pulsa «Nuevo aparato» y "
         "guarda ahí sus esquemáticos.",
         "device"),
        ("2", "Analiza los esquemáticos",
         "Pulsa «Analizar». El programa lee los PDF y guarda todos los "
         "componentes. La primera vez puede tardar unos minutos; después es "
         "instantáneo porque queda guardado.",
         "index"),
        ("3", "Busca el componente",
         "Escribe su nombre (R46, C12, U5…) o un valor (10k, 100uF) y pulsa "
         "Buscar. Abajo aparecen todos los que coinciden.",
         "search"),
        ("4", "Míralo y mídelo",
         "Haz clic en un resultado: se abre la pestaña MULTÍMETRO con el paso "
         "a paso para medirlo y saber si está en corto. En «Componente» ves su "
         "símbolo y, en «Diagnóstico», todo el análisis.",
         "none"),
        ("5", "Entiende cómo interactúa",
         "En «🔄 Interacción y comportamiento» ves para qué sirve el componente, "
         "cómo se comporta, con qué otros componentes se relaciona (mapa "
         "pulsable) y qué pasa en el circuito si falla. Pulsa los nodos del mapa "
         "para «pasear» por el circuito y «◀ Volver» para regresar.",
         "none"),
        ("6", "Localízalo en la hoja",
         "Haz DOBLE clic en el resultado y se abre el esquemático con el "
         "componente resaltado en rojo. Arrastra para moverte, usa Ctrl+rueda "
         "para acercar y el mapa de la derecha para saltar.",
         "none"),
    ]

    GLOSSARY = [
        ("Designador", "El nombre corto del componente: R = resistencia, "
                       "C = condensador, D = diodo, Q = transistor, "
                       "U/IC = circuito integrado, J = conector, F = fusible."),
        ("Ω (ohmios)", "Unidad de resistencia. 1 kΩ = 1000 Ω, 1 MΩ = 1 000 000 Ω."),
        ("O.L. / ∞", "«Circuito abierto»: no hay continuidad (el multímetro no "
                     "pita). Normal en diodos al revés o en un componente roto."),
        ("Continuidad", "Modo que pita cuando dos puntos están unidos (0 Ω). "
                        "Sirve para comprobar cables, fusibles y cortos."),
        ("En corto", "Dos puntos que no deberían estar unidos lo están (0 Ω). "
                     "Es la avería más común."),
        ("Modo diodo", "Posición del multímetro (→|) para probar diodos, LEDs y "
                       "transistores: mide la caída de tensión."),
        ("ESR", "Resistencia interna de un condensador electrolítico. Si sube "
                "mucho, el condensador está «seco» y hay que cambiarlo."),
        ("VCC / GND", "Alimentación (+) y masa (–) de un circuito integrado."),
        ("Soldadura fría", "Soldadura mal hecha que hace mal contacto: falla al "
                           "mover la placa. Se arregla resoldando."),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        title = QLabel("🆘  Cómo usar el programa (en 6 pasos)")
        f = QFont(); f.setBold(True); f.setPointSize(13)
        title.setFont(f)
        root.addWidget(title)

        steps_box = QGroupBox("Pasos")
        grid = QGridLayout(steps_box)
        grid.setColumnStretch(2, 1)
        for i, (num, titulo, texto, accion) in enumerate(self.STEPS):
            badge = QLabel(num)
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                "QLabel{background:#2563eb;color:white;border-radius:14px;"
                "font-weight:bold;font-size:13px;}")
            grid.addWidget(badge, i, 0, Qt.AlignTop)
            lbl = QLabel()
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            lbl.setText(f"<b style='font-size:12px'>{titulo}</b><br>"
                        f"<span style='color:#c7d2e0'>{texto}</span>")
            grid.addWidget(lbl, i, 1)
            if accion and accion != "none":
                btn = QPushButton({
                    "device": "Ir al aparato",
                    "index": "⚙️  Analizar ahora",
                    "search": "🔎  Ir a buscar",
                }.get(accion, "Hacer"))
                btn.clicked.connect(lambda _=False, a=accion: self.action.emit(a))
                grid.addWidget(btn, i, 2, Qt.AlignTop)
        root.addWidget(steps_box)

        glos = QGroupBox("Diccionario para principiantes")
        gl = QVBoxLayout(glos)
        view = QTextBrowser()
        view.setOpenExternalLinks(False)
        view.setStyleSheet("QTextBrowser{background:#12161d;border:1px solid #2b3444;}")
        html = ["<div style='font-family:Segoe UI;color:#dbe3ee;'>"]
        for term, desc in self.GLOSSARY:
            html.append(f"<p style='margin:4px 0'><b style='color:#7ec8ff'>"
                        f"{term}</b><br><span style='color:#c7d2e0'>{desc}</span></p>")
        html.append("<p style='margin-top:10px'><b style='color:#7fd1a0'>Consejo de "
                    "seguridad</b><br><span style='color:#c7d2e0'>Antes de medir "
                    "resistencia, continuidad o diodos, DESENCHUFA el equipo y "
                    "descarga los condensadores grandes. Para medir tensiones (V) "
                    "sí debe estar encendido, con mucho cuidado.</span></p>")
        html.append("</div>")
        view.setHtml("".join(html))
        gl.addWidget(view)
        root.addWidget(glos, 1)

    def on_show(self):
        pass
