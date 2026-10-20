#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Panel gráfico del componente seleccionado.

Muestra el SÍMBOLO del componente (dibujado localmente, sin internet), su
valor y, en el caso de las resistencias, el CÓDIGO DE COLORES real calculado
a partir del valor. Opcionalmente puede buscar una FOTO REAL en internet
(Wikimedia Commons).
"""
import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QMessageBox, QSizePolicy
)

from utils.component_symbols import (
    component_kind, kind_name, resistor_color_code, capacitor_code,
    symbol_pixmap, parse_resistance, format_ohms, format_farads, parse_farads
)
import utils.component_images as images
from utils import diagnostics


class _PhotoFetcher(QThread):
    done = pyqtSignal(bytes, str, str)   # imagen, título, página
    fail = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            hits = images.search_image(self.query, limit=4)
            if not hits:
                self.fail.emit("No se encontraron fotos para «%s»." % self.query)
                return
            last_err = ""
            for hit in hits:
                try:
                    data = images.download_image(hit["url"])
                    self.done.emit(data, hit["title"], hit["page"])
                    return
                except Exception as e:            # probar el siguiente
                    last_err = str(e)
            self.fail.emit("No se pudo descargar la imagen: " + last_err)
        except Exception as e:
            self.fail.emit("Error de búsqueda: " + str(e))


class ComponentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._designator = ""
        self._kind = "generic"
        self._symbol_pm = None
        self._photo_pm = None
        self._thread = None
        self.init_ui()
        self.clear()

    # ---------------- UI ----------------
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.lbl_title = QLabel("🧩  Componente")
        f = QFont(); f.setBold(True); f.setPointSize(14)
        self.lbl_title.setFont(f)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_title)

        # Símbolo
        self.symbol_box = QFrame()
        self.symbol_box.setFrameShape(QFrame.StyledPanel)
        self.symbol_box.setStyleSheet(
            "QFrame{background:#171b22;border:1px solid #333c4a;border-radius:8px;}")
        sb = QVBoxLayout(self.symbol_box)
        self.lbl_symbol = QLabel()
        self.lbl_symbol.setAlignment(Qt.AlignCenter)
        self.lbl_symbol.setMinimumHeight(230)
        sb.addWidget(self.lbl_symbol)
        root.addWidget(self.symbol_box)

        self.lbl_kind = QLabel("")
        self.lbl_kind.setAlignment(Qt.AlignCenter)
        kf = QFont(); kf.setPointSize(11)
        self.lbl_kind.setFont(kf)
        root.addWidget(self.lbl_kind)

        self.lbl_value = QLabel("")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        vf = QFont(); vf.setBold(True); vf.setPointSize(13)
        self.lbl_value.setFont(vf)
        self.lbl_value.setStyleSheet("color:#7fd1a0;")
        root.addWidget(self.lbl_value)

        # Código de colores
        self.grp_code = QFrame()
        self.grp_code.setFrameShape(QFrame.StyledPanel)
        self.grp_code.setStyleSheet(
            "QFrame{background:#1c222b;border:1px solid #333c4a;border-radius:6px;}")
        gl = QVBoxLayout(self.grp_code)
        self.lbl_code = QLabel("")
        self.lbl_code.setWordWrap(True)
        self.lbl_code.setTextFormat(Qt.RichText)
        self.lbl_code.setAlignment(Qt.AlignCenter)
        gl.addWidget(self.lbl_code)
        root.addWidget(self.grp_code)

        self.lbl_extra = QLabel("")
        self.lbl_extra.setWordWrap(True)
        self.lbl_extra.setStyleSheet("color:#9fb0c7;")
        root.addWidget(self.lbl_extra)

        # Resumen de diagnóstico (usos + prueba rápida)
        self.grp_diag = QFrame()
        self.grp_diag.setFrameShape(QFrame.StyledPanel)
        self.grp_diag.setStyleSheet(
            "QFrame{background:#1c222b;border:1px solid #333c4a;border-radius:6px;}")
        dl = QVBoxLayout(self.grp_diag)
        self.lbl_diag = QLabel("")
        self.lbl_diag.setWordWrap(True)
        self.lbl_diag.setTextFormat(Qt.RichText)
        dl.addWidget(self.lbl_diag)
        root.addWidget(self.grp_diag)

        # Botones
        row = QHBoxLayout()
        self.btn_photo = QPushButton("🌐  Ver foto real")
        self.btn_photo.setToolTip("Busca una foto real del componente en Wikimedia Commons")
        self.btn_photo.clicked.connect(self.fetch_photo)
        self.btn_save = QPushButton("💾  Guardar imagen")
        self.btn_save.clicked.connect(self.save_image)
        row.addWidget(self.btn_photo)
        row.addWidget(self.btn_save)
        root.addLayout(row)

        # Foto real
        self.lbl_photo = QLabel()
        self.lbl_photo.setAlignment(Qt.AlignCenter)
        self.lbl_photo.setMinimumHeight(180)
        self.lbl_photo.setStyleSheet(
            "QLabel{background:#171b22;border:1px dashed #3a465a;border-radius:8px;color:#7b8798;}")
        self.lbl_photo.setText("Pulsa «Ver foto real» para buscar una imagen")
        root.addWidget(self.lbl_photo)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color:#c9a227;")
        root.addWidget(self.lbl_status)

        root.addStretch(1)

    # ---------------- Datos ----------------
    def clear(self):
        self._designator = ""
        self._kind = "generic"
        self._symbol_pm = None
        self._photo_pm = None
        self.lbl_title.setText("🧩  Componente")
        self.lbl_symbol.clear()
        self.lbl_symbol.setText("—")
        self.lbl_kind.setText("")
        self.lbl_value.setText("")
        self.grp_code.setVisible(False)
        self.lbl_extra.setText("")
        self.grp_diag.setVisible(False)
        self.lbl_diag.setText("")
        self.lbl_photo.clear()
        self.lbl_photo.setText("Pulsa «Ver foto real» para buscar una imagen")
        self.lbl_status.setText("")

    def show_component(self, designator, value="", component_type="", source=""):
        self._designator = (designator or "").upper()
        self._kind = component_kind(self._designator, component_type or "")
        name = kind_name(self._kind)

        self.lbl_title.setText(f"🧩  {self._designator}  —  {name}" if self._designator
                               else f"🧩  {name}")
        self.lbl_kind.setText(name)
        if value:
            self.lbl_value.setText(f"Valor:  {value}")
        else:
            self.lbl_value.setText("Valor: no determinado")

        # Símbolo (la etiqueta interna solo para CIs)
        label = value.strip() if (self._kind == "ic" and value) else ""
        self._symbol_pm = symbol_pixmap(self._kind, 250, label=label)
        self._set_symbol_pixmap()
        self.lbl_photo.clear()
        self.lbl_photo.setText("Pulsa «Ver foto real» para buscar una imagen")
        self._photo_pm = None
        self.lbl_status.setText("")

        self._fill_code(value, source)
        self._fill_diag(value, component_type)

    def _set_symbol_pixmap(self, pm=None):
        pm = pm or self._symbol_pm
        if pm is None:
            return
        self.lbl_symbol.setPixmap(pm)

    def _fill_code(self, value, source):
        html = []
        bands = None
        tol = None
        extra = []

        # Resistencia: código de colores
        if self._kind in ("resistor", "resistor_network", "thermistor", "varistor"):
            cc = resistor_color_code(value)
            if cc:
                bands = cc["value_bands"]
                tol = cc["tolerance"]
                sw = []
                for nm, hx in cc["value_bands"] + [cc["tolerance"]]:
                    sw.append(
                        '<span style="background:%s; border:1px solid #00000055;">'
                        '&nbsp;&nbsp;&nbsp;&nbsp;</span>&nbsp;%s' % (hx, nm))
                html.append("<b>Código de colores</b> (banda por banda):<br>"
                            + "<br>".join(sw))
                html.append(
                    f'<br><span style="color:#9fb0c7;">{cc["summary"]} &nbsp; '
                    f'{cc["tolerance_text"]}</span>')
                extra.append(f"Valor normalizado: {format_ohms(cc['ohms'])}")
            else:
                html.append("<b>Código de colores</b><br>"
                            "<span style='color:#9fb0c7'>"
                            "Valor no reconocido; no se puede calcular el código."
                            "</span>")

        # Condensador cerámico: marcaje de 3 dígitos
        elif self._kind == "capacitor":
            code = capacitor_code(value)
            f = parse_farads(value)
            if code:
                html.append(f"<b>Marcaje del condensador:</b> "
                            f"<span style='font-size:16pt;color:#7fd1a0'>{code}</span>")
                if f is not None:
                    html.append(f"<br><span style='color:#9fb0c7'>"
                                f"= {format_farads(f)}</span>")
                extra.append("El marcaje de 3 cifras: 2 significativas + nº de ceros "
                             "(p. ej. 104 = 10 × 10⁴ pF = 100 nF).")

        self.grp_code.setVisible(bool(html))
        self.lbl_code.setText("<br>".join(html) if html else "")

        # Reconstruir el símbolo ahora que ya tenemos las bandas
        label = value.strip() if (self._kind == "ic" and value) else ""
        self._symbol_pm = symbol_pixmap(self._kind, 250, bands=bands,
                                        tolerance=tol, label=label)
        self._set_symbol_pixmap()

        notes = list(extra)
        if source:
            notes.append(f"Fuente: {source}")
        self.lbl_extra.setText("\n".join(notes))

    def _fill_diag(self, value, component_type):
        """Resumen: usos + prueba rápida + detección de corto."""
        data = diagnostics.diagnose(self._kind, value, self._designator, component_type)
        html = []
        if data["uses"]:
            uses = " · ".join(data["uses"][:3])
            html.append("<b>🎯 Uso:</b> " + uses)
        test = data.get("test", {})
        if test.get("mode"):
            html.append(f"<b>🔧 Prueba:</b> <span style='color:#ffd166'>"
                        f"{test['mode']}</span>")
        # Lectura correcta y lectura en corto
        good = next((e for e in data["expected"]
                     if "BUENO" in e.upper() or "bueno" in e), None)
        rows = data.get("short", {}).get("rows", [])
        short_row = next((r for r in rows if r[0].lower().startswith("en corto")), None)
        if good:
            html.append(f"<b>✅ Bueno:</b> {good}")
        if short_row:
            html.append(f"<b>🔴 En corto:</b> <span style='color:#ff8a80'>"
                        f"{short_row[1]}</span> — {short_row[2]}")
        html.append("<span style='color:#9fb0c7'>Se abre la pestaña "
                    "<b>🔌 Multímetro</b> con el paso a paso. Más detalle en "
                    "<b>🔬 Diagnóstico y pruebas</b>.</span>")
        self.lbl_diag.setText("<br>".join(html))
        self.grp_diag.setVisible(bool(html))

    # ---------------- Foto real ----------------
    def fetch_photo(self):
        if not self._designator:
            return
        if self._thread is not None and self._thread.isRunning():
            return
        query = images.build_query(self._kind, self.lbl_value.text().replace("Valor:", "").strip(),
                                   self._designator)
        self.lbl_status.setText(f"🌐 Buscando «{query}»…")
        self.lbl_photo.setText("Cargando…")
        self._thread = _PhotoFetcher(query)
        self._thread.done.connect(self._on_photo)
        self._thread.fail.connect(self._on_photo_fail)
        self._thread.start()

    def _on_photo(self, data, title, page):
        pm = QPixmap()
        if not pm.loadFromData(data):
            self._on_photo_fail("Formato de imagen no soportado.")
            return
        if pm.width() > 420:
            pm = pm.scaledToWidth(420, Qt.SmoothTransformation)
        self._photo_pm = pm
        self.lbl_photo.setPixmap(pm)
        self.lbl_status.setText(f"📷 {title}")
        if page:
            self.lbl_status.setToolTip(page)

    def _on_photo_fail(self, msg):
        self.lbl_photo.clear()
        self.lbl_photo.setText("Sin imagen disponible")
        self.lbl_status.setText("⚠  " + msg)

    # ---------------- Guardar ----------------
    def save_image(self):
        pm = self._photo_pm or self._symbol_pm
        if pm is None:
            return
        base = self._designator or "componente"
        suggested = os.path.join(os.getcwd(), f"{base}_simbolo.png")
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen", suggested, "Imagen PNG (*.png)")
        if not path:
            return
        if not pm.save(path, "PNG"):
            QMessageBox.warning(self, "Error", "No se pudo guardar la imagen.")
        else:
            self.lbl_status.setText(f"💾 Guardado en {path}")
