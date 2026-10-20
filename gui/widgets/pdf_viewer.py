#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Visor de esquemáticos cómodo (pensado para uso fácil).

Mejoras de "dinámica":
  * Zoom con botones ＋/－ y con Ctrl + rueda del ratón.
  * ARRASTRAR con el ratón para mover la hoja (mano).
  * Mini-mapa de la hoja: clic para saltar a cualquier zona.
  * Centrado automático en el componente buscado y etiqueta con su nombre.
  * Atajos: +, -, PageUp/PageDown, Home/End, Ctrl+0 (ajustar).
"""
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel,
    QScrollArea, QToolBar, QSizePolicy, QFrame, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QImage, QFont

import fitz  # PyMuPDF

MIN_ZOOM, MAX_ZOOM = 0.15, 6.0


class PageLabel(QLabel):
    """Dibuja la página, los resaltados y la etiqueta del componente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rects = []
        self._labels = []
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_page(self, pixmap, rects, labels=None):
        self._rects = rects or []
        self._labels = labels or []
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._rects:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for i, (x0, y0, x1, y1) in enumerate(self._rects):
            primary = (i == 0)
            pen = QPen(QColor(255, 45, 45) if primary else QColor(255, 140, 0),
                       4 if primary else 2)
            painter.setPen(pen)
            painter.setBrush(QColor(255, 235, 59, 110) if primary
                             else QColor(255, 200, 0, 55))
            painter.drawRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0))
        # Etiqueta con el designador, justo encima del primer recuadro
        if self._labels:
            text = self._labels[0]
            font = QFont(); font.setBold(True); font.setPointSize(10)
            painter.setFont(font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text) + 14
            th = fm.height() + 6
            x = int(self._rects[0][0])
            y = max(0, int(self._rects[0][1]) - th - 4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 45, 45, 220))
            painter.drawRoundedRect(x, y, tw, th, 4, 4)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x + 7, y + th - 7, text)
        painter.end()


class _PanScroll(QScrollArea):
    """Área con arrastre para mover y Ctrl+rueda para hacer zoom."""
    zoomWheel = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag = None
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.zoomWheel.emit(event.angleDelta().y())
            event.accept()
            return
        super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            d = event.pos() - self._drag
            self._drag = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - d.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag is not None:
            self._drag = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class MiniMap(QLabel):
    """Miniatura de la hoja con el recuadro de lo que se está viendo."""
    jump = pyqtSignal(float, float)      # fracciones 0..1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thumb = None
        self._view = (0.0, 0.0, 1.0, 1.0)
        self.setFixedWidth(170)
        self.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.setStyleSheet(
            "QLabel{background:#0e1218;border:1px solid #2b3444;border-radius:6px;}")
        self.setCursor(Qt.PointingHandCursor)

    def set_thumbnail(self, pm):
        self._thumb = pm
        self.setPixmap(pm)

    def set_view(self, x, y, w, h):
        self._view = (max(0.0, x), max(0.0, y), min(1.0, w), min(1.0, h))
        self.update()

    def _to_fraction(self, pos):
        if not self._thumb or self._thumb.width() <= 0:
            return None
        x = pos.x() / float(self._thumb.width())
        y = pos.y() / float(self._thumb.height())
        return (min(1.0, max(0.0, x)), min(1.0, max(0.0, y)))

    def mousePressEvent(self, event):
        f = self._to_fraction(event.pos())
        if f:
            self.jump.emit(*f)
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            f = self._to_fraction(event.pos())
            if f:
                self.jump.emit(*f)
        event.accept()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._thumb:
            return
        p = QPainter(self)
        x, y, w, h = self._view
        p.setPen(QPen(QColor(90, 170, 255), 2))
        p.setBrush(QColor(90, 170, 255, 45))
        p.drawRect(int(x * self._thumb.width()), int(y * self._thumb.height()),
                   int(w * self._thumb.width()), int(h * self._thumb.height()))
        p.end()


class PDFViewer(QWidget):
    MAX_CACHE = 8

    # (ruta_archivo, nº de página 1-based) cuando se muestra otra hoja
    pageChanged = pyqtSignal(str, int)
    # designador pulsado en la lista «Componentes de esta hoja»
    componentClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_page_key = None
        self.doc = None
        self._doc_path = ""
        self._pix_cache = {}
        self._thumb_cache = {}
        self.page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.highlight_words = []
        self.highlight_rects = {}
        self._last_rects = []
        self._last_labels = []
        self._zoom_timer = QTimer(self)
        self._zoom_timer.setSingleShot(True)
        self._zoom_timer.setInterval(70)
        self._zoom_timer.timeout.connect(self.render)
        self._mini_timer = QTimer(self)
        self._mini_timer.setSingleShot(True)
        self._mini_timer.setInterval(60)
        self._mini_timer.timeout.connect(self._sync_minimap)
        self.init_ui()
        self.setFocusPolicy(Qt.StrongFocus)

    # ---------------- UI ----------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.btn_prev = QPushButton("◀  Página")
        self.btn_prev.setToolTip("Página anterior (PageUp)")
        self.btn_next = QPushButton("Página  ▶")
        self.btn_next.setToolTip("Página siguiente (PageDown)")
        self.lbl_page = QLabel("0/0")
        self.btn_zoom_out = QPushButton("－")
        self.btn_zoom_out.setToolTip("Alejar (tecla -)")
        self.btn_zoom_in = QPushButton("＋")
        self.btn_zoom_in.setToolTip("Acercar (tecla +)")
        self.btn_zoom_in.setFixedWidth(34)
        self.btn_zoom_out.setFixedWidth(34)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(int(MIN_ZOOM * 100), int(MAX_ZOOM * 100))
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(130)
        self.zoom_slider.setToolTip("Zoom")
        self.lbl_zoom = QLabel("100 %")
        self.lbl_zoom.setFixedWidth(56)
        self.btn_fit = QPushButton("Ancho")
        self.btn_fit.setToolTip("Ajustar el esquemático al ancho (Ctrl+0)")
        self.btn_fit_page = QPushButton("Hoja entera")
        self.btn_fit_page.setToolTip("Ver la hoja completa")
        self.btn_center = QPushButton("🎯  Ir al componente")
        self.btn_center.setToolTip("Centrar la vista en el componente buscado")
        self.lbl_shown = QLabel("")
        self.lbl_shown.setStyleSheet("color:#ffd166;font-weight:bold;")

        toolbar.addWidget(self.btn_prev)
        toolbar.addWidget(self.btn_next)
        toolbar.addWidget(self.lbl_page)
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_zoom_out)
        toolbar.addWidget(self.zoom_slider)
        toolbar.addWidget(self.btn_zoom_in)
        toolbar.addWidget(self.lbl_zoom)
        toolbar.addWidget(self.btn_fit)
        toolbar.addWidget(self.btn_fit_page)
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_center)
        toolbar.addWidget(self.lbl_shown)
        layout.addWidget(toolbar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        self.scroll = _PanScroll()
        self.page_label = PageLabel()
        self.scroll.setWidget(self.page_label)
        body.addWidget(self.scroll, 1)

        side = QVBoxLayout()
        side.setContentsMargins(4, 4, 4, 4)
        t = QLabel("🗺️ Mapa")
        t.setStyleSheet("color:#8fa3bf;font-size:10px;")
        t.setAlignment(Qt.AlignHCenter)
        side.addWidget(t)
        self.minimap = MiniMap()
        self.minimap.setToolTip("Clic en el mapa para saltar a esa zona de la hoja")
        side.addWidget(self.minimap)
        side.addSpacing(6)
        lbl_comp = QLabel("📋 Componentes de esta hoja")
        lbl_comp.setStyleSheet("color:#8fa3bf;font-size:10px;")
        lbl_comp.setWordWrap(True)
        lbl_comp.setAlignment(Qt.AlignHCenter)
        side.addWidget(lbl_comp)
        self.lst_page_components = QListWidget()
        self.lst_page_components.setFixedWidth(170)
        self.lst_page_components.setToolTip(
            "Componentes detectados en esta hoja.\n"
            "Pulsa uno para resaltarlo en el esquemático.")
        self.lst_page_components.itemClicked.connect(
            self._on_page_component_clicked)
        side.addWidget(self.lst_page_components, 1)
        hint = QLabel("Arrastra para\nmover · Ctrl+rueda\npara zoom")
        hint.setStyleSheet("color:#6d7f97;font-size:9px;")
        hint.setAlignment(Qt.AlignHCenter)
        side.addWidget(hint)
        body.addLayout(side)
        layout.addLayout(body, 1)

        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        self.zoom_slider.valueChanged.connect(self.set_zoom)
        self.btn_fit.clicked.connect(self.fit_width)
        self.btn_fit_page.clicked.connect(self.fit_page)
        self.btn_zoom_in.clicked.connect(lambda: self.step_zoom(+1))
        self.btn_zoom_out.clicked.connect(lambda: self.step_zoom(-1))
        self.btn_center.clicked.connect(self.center_on_highlight)
        self.scroll.zoomWheel.connect(self.on_wheel_zoom)
        self.minimap.jump.connect(self.jump_to_fraction)
        self.scroll.horizontalScrollBar().valueChanged.connect(self._schedule_minimap)
        self.scroll.verticalScrollBar().valueChanged.connect(self._schedule_minimap)

    # ---------------- Carga ----------------
    def load_pdf(self, path, highlight_words=None, highlight_rects=None, page=1):
        """Carga (o reutiliza) el PDF y muestra la página indicada."""
        try:
            ap = os.path.abspath(path)
            if self.doc is None or self._doc_path != ap:
                if self.doc:
                    self.doc.close()
                self.doc = fitz.open(path)
                self._doc_path = ap
                self._pix_cache.clear()
                self._thumb_cache.clear()
                self.total_pages = len(self.doc)
                self.page = max(0, min(self.total_pages - 1, (page or 1) - 1))
                self.zoom = self._fit_zoom()
                self._sync_zoom_widgets()
            self.total_pages = len(self.doc)
            self.highlight_words = highlight_words or []
            self.highlight_rects = highlight_rects or {}
            self.page = max(0, min(self.total_pages - 1, (page or 1) - 1))
            self.render()
            QTimer.singleShot(30, self.center_on_highlight)
            return True
        except Exception as e:
            print(f"Error cargando PDF: {e}")
            return False

    def close_pdf(self):
        if self.doc:
            self.doc.close()
            self.doc = None
        self._doc_path = ""
        self._pix_cache.clear()
        self._thumb_cache.clear()
        self.page_label.clear()
        self.page_label.setFixedSize(1, 1)
        self.minimap.set_thumbnail(QPixmap())
        self.lst_page_components.clear()
        self._last_page_key = None
        self.lbl_page.setText("0/0")
        self.lbl_shown.setText("")

    # ---------------- Render ----------------
    def _get_pixmap(self, page_index):
        key = (page_index, round(self.zoom, 3))
        cached = self._pix_cache.get(key)
        if cached is not None:
            return cached
        page = self.doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom), alpha=False)
        fmt = QImage.Format_RGB888 if pix.n == 3 else QImage.Format_RGBA8888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt).copy()
        pixmap = QPixmap.fromImage(qimg)
        if len(self._pix_cache) >= self.MAX_CACHE:
            self._pix_cache.clear()
        self._pix_cache[key] = pixmap
        return pixmap

    def _get_thumbnail(self, page_index):
        cached = self._thumb_cache.get(page_index)
        if cached is not None:
            return cached
        try:
            page = self.doc[page_index]
            w = max(1.0, page.rect.width)
            z = 160.0 / w
            pix = page.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
            fmt = QImage.Format_RGB888 if pix.n == 3 else QImage.Format_RGBA8888
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt).copy()
            pm = QPixmap.fromImage(qimg)
        except Exception:
            pm = QPixmap()
        self._thumb_cache[page_index] = pm
        return pm

    def render(self):
        if not self.doc or self.page < 0 or self.page >= self.total_pages:
            return
        page = self.doc[self.page]
        pixmap = self._get_pixmap(self.page)

        rects = []
        for r in self.highlight_rects.get(self.page + 1, []):
            try:
                rects.append((r[0] * self.zoom, r[1] * self.zoom,
                              r[2] * self.zoom, r[3] * self.zoom))
            except Exception:
                pass
        if not rects:
            rot = getattr(page, 'rotation', 0)
            m = page.rotation_matrix if rot else None
            for word in self.highlight_words:
                try:
                    for r in page.search_for(word):
                        if m is not None:
                            r = r * m
                        rects.append((r.x0 * self.zoom, r.y0 * self.zoom,
                                      r.x1 * self.zoom, r.y1 * self.zoom))
                except Exception:
                    pass

        labels = [self.highlight_words[0]] if (rects and self.highlight_words) else []
        self._last_rects = rects
        self._last_labels = labels
        self.page_label.set_page(pixmap, rects, labels)
        self.lbl_page.setText(f"{self.page + 1}/{self.total_pages}")

        if self.highlight_words:
            self.lbl_shown.setText(
                f"  Componente: {self.highlight_words[0]}"
                + ("" if rects else "  (no encontrado en esta hoja)"))
        else:
            self.lbl_shown.setText("")

        thumb = self._get_thumbnail(self.page)
        self.minimap.set_thumbnail(thumb)
        self._schedule_minimap()

        key = (self._doc_path, self.page + 1)
        if key != self._last_page_key:
            self._last_page_key = key
            self.pageChanged.emit(self._doc_path, self.page + 1)

    # ------------- Componentes de esta hoja -------------
    def set_page_components(self, items):
        """items: lista de (designador, valor) que hay en la hoja mostrada."""
        self.lst_page_components.clear()
        for des, value in (items or []):
            texto = des if not value else f"{des}   ·   {value}"
            it = QListWidgetItem(texto)
            it.setData(Qt.UserRole, des)
            if value:
                it.setToolTip(f"{des} — {value}")
            self.lst_page_components.addItem(it)

    def _on_page_component_clicked(self, item):
        des = item.data(Qt.UserRole) or (item.text() or "").split()[0]
        if des:
            self.componentClicked.emit(des)

    def _schedule_minimap(self, *_):
        self._mini_timer.start()

    def _sync_minimap(self):
        if not self.doc or self.page_label.width() <= 1:
            return
        pw = float(self.page_label.width())
        ph = float(self.page_label.height())
        vw = self.scroll.viewport().width()
        vh = self.scroll.viewport().height()
        x = self.scroll.horizontalScrollBar().value() / pw
        y = self.scroll.verticalScrollBar().value() / ph
        self.minimap.set_view(x, y, min(1.0, vw / pw), min(1.0, vh / ph))

    # ---------------- Acciones ----------------
    def set_highlight(self, words, rects=None):
        self.highlight_words = words or []
        self.highlight_rects = rects or {}
        self.render()
        self.center_on_highlight()

    def center_on_highlight(self):
        if not self._last_rects:
            return
        x0, y0, x1, y1 = self._last_rects[0]
        vw = self.scroll.viewport().width()
        vh = self.scroll.viewport().height()
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        self.scroll.horizontalScrollBar().setValue(int(cx - vw / 2.0))
        self.scroll.verticalScrollBar().setValue(int(cy - vh / 2.0))

    def jump_to_fraction(self, fx, fy):
        if self.page_label.width() <= 1:
            return
        vw = self.scroll.viewport().width()
        vh = self.scroll.viewport().height()
        self.scroll.horizontalScrollBar().setValue(
            int(fx * self.page_label.width() - vw / 2.0))
        self.scroll.verticalScrollBar().setValue(
            int(fy * self.page_label.height() - vh / 2.0))

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.render()
            self.center_on_highlight()

    def next_page(self):
        if self.page < self.total_pages - 1:
            self.page += 1
            self.render()
            self.center_on_highlight()

    def _sync_zoom_widgets(self):
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(self.zoom * 100))
        self.lbl_zoom.setText(f"{int(round(self.zoom * 100))} %")
        self.zoom_slider.blockSignals(False)

    def set_zoom(self, val):
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, val / 100.0))
        self.lbl_zoom.setText(f"{int(round(self.zoom * 100))} %")
        self._zoom_timer.start()

    def on_wheel_zoom(self, delta):
        factor = 1.15 if delta > 0 else 1 / 1.15
        step_zoom_value = int(round(self.zoom * 100 * factor))
        step_zoom_value = max(int(MIN_ZOOM * 100), min(int(MAX_ZOOM * 100),
                                                      step_zoom_value))
        self.zoom_slider.setValue(step_zoom_value)   # dispara set_zoom

    def step_zoom(self, direction):
        delta = 25 if direction > 0 else -25
        v = int(round(self.zoom * 100)) + delta
        self.zoom_slider.setValue(max(int(MIN_ZOOM * 100),
                                      min(int(MAX_ZOOM * 100), v)))

    def _fit_zoom(self):
        if not self.doc:
            return 1.0
        try:
            viewport = self.scroll.viewport().width() - 30
            if viewport < 100:
                return self.zoom or 1.0
            page_w = self.doc[self.page].rect.width
            if page_w <= 0:
                return 1.0
            return max(MIN_ZOOM, min(MAX_ZOOM, viewport / page_w))
        except Exception:
            return 1.0

    def fit_width(self):
        if not self.doc:
            return
        self.zoom_slider.setValue(int(self._fit_zoom() * 100))

    def fit_page(self):
        if not self.doc:
            return
        try:
            page = self.doc[self.page]
            vw = self.scroll.viewport().width() - 30
            vh = self.scroll.viewport().height() - 20
            z = min(vw / page.rect.width, vh / page.rect.height)
            self.zoom_slider.setValue(int(max(MIN_ZOOM, min(MAX_ZOOM, z)) * 100))
        except Exception:
            pass

    def go_to_page(self, num):
        if not self.doc:
            return
        self.page = max(0, min(self.total_pages - 1, num - 1))
        self.render()
        self.center_on_highlight()

    # ---------------- Atajos ----------------
    def keyPressEvent(self, event):
        k = event.key()
        if k in (Qt.Key_Plus, Qt.Key_Equal):
            self.step_zoom(+1)
        elif k in (Qt.Key_Minus, Qt.Key_Underscore):
            self.step_zoom(-1)
        elif k == Qt.Key_PageDown:
            self.next_page()
        elif k == Qt.Key_PageUp:
            self.prev_page()
        elif k == Qt.Key_Home:
            self.go_to_page(1)
        elif k == Qt.Key_End:
            self.go_to_page(self.total_pages)
        elif k == Qt.Key_0 and (event.modifiers() & Qt.ControlModifier):
            self.fit_width()
        else:
            super().keyPressEvent(event)
