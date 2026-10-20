#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QTableWidget, QTableWidgetItem, QFileDialog, QProgressBar,
    QStatusBar, QMessageBox, QHeaderView, QSplitter, QTabWidget, QInputDialog,
    QComboBox, QFrame, QTextEdit, QGroupBox, QListWidget, QListWidgetItem,
    QCheckBox, QScrollArea, QMenu, QToolButton, QSizePolicy, QApplication,
    QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap

from utils.search_index import SearchIndex
from utils.file_loader import FileLoader, SUPPORTED_EXTS
from utils.config import Config
from utils.parse_cache import ParseCache
from database.device_db import DeviceDB
from gui.widgets.pdf_viewer import PDFViewer
from gui.widgets.nomenclature_panel import NomenclaturePanel
from gui.widgets.connections_panel import ConnectionsPanel
from gui.widgets.voltage_divider import VoltageDividerPanel
from gui.widgets.component_view import ComponentView
from gui.widgets.diagnostic_panel import DiagnosticPanel
from gui.widgets.multimeter_panel import MultimeterPanel
from gui.widgets.interaction_panel import InteractionPanel
from gui.widgets.help_panel import HelpPanel
from utils import translations
from utils.schematic_store import SchematicStore
from utils import paths
from utils import migration

import qdarkstyle

BASE_DIR = paths.BASE_DIR
ICON_PATH = paths.ICON_FILE
SCHEMATICS_DIR = paths.SCHEMATICS_DIR


def _app_icon() -> QIcon:
    """Icono de la aplicación (png preferido; si no, ico). Nunca vacío."""
    icon = QIcon()
    for p in (paths.ICON_PNG, paths.ICON_ICO):
        if p and os.path.exists(p):
            icon.addFile(p)
    return icon


def load_qdarkstyle() -> str:
    """Carga la hoja de estilo de qdarkstyle de forma compatible.

    qdarkstyle cambió de API entre versiones (``load_stylesheet_pyqt5`` quedó
    obsoleta). Se prueban las variantes por orden y, si ninguna existe, se
    devuelve una hoja vacía en lugar de romper el arranque.
    """
    try:
        if hasattr(qdarkstyle, "load_stylesheet"):
            return qdarkstyle.load_stylesheet(pyside=False)
    except Exception:
        pass
    try:
        return qdarkstyle.load_stylesheet_pyqt5()
    except Exception:
        pass
    return ""


def _norm_path(p):
    """Ruta canónica para comparar archivos sin depender del separador."""
    try:
        return os.path.normcase(os.path.normpath(os.path.abspath(p)))
    except Exception:
        return (p or "").lower()


class IndexerThread(QThread):
    progress = pyqtSignal(int, str)
    detail = pyqtSignal(str)
    index_done = pyqtSignal()

    def __init__(self, paths, index, device="", use_ocr=True, cache=None):
        super().__init__()
        self.paths = paths
        self.index = index
        self.device = device
        self.use_ocr = use_ocr
        self.cache = cache

    def run(self):
        loader = FileLoader(self.index, device=self.device, use_ocr=self.use_ocr,
                            cache=self.cache, progress=self.detail.emit)
        total = len(self.paths) or 1
        for i, p in enumerate(self.paths, 1):
            self.progress.emit(int(i * 100 / total), os.path.basename(p))
            try:
                loader.load_path(p)
            except Exception as e:
                print(e)
        if self.cache:
            self.cache.save()
        self.index_done.emit()


class SchematicSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        translations.set_language()
        self.setWindowTitle(translations.tr('app_title'))
        self.setWindowIcon(_app_icon())

        self.index = SearchIndex()
        self.config = Config()
        self.device_db = DeviceDB()
        self.parse_cache = ParseCache()
        self.store = SchematicStore()
        self.paths = []
        self.current_device = ""
        self._indexing = False
        self._auto_index = False
        self._pending_search = None
        self._restart_index = False
        self._nav_history = []         # componentes visitados (para «Volver»)
        self._compact = False          # modo compacto para pantallas pequeñas
        self._ui_ready = False         # evita que resizeEvent actúe antes de tiempo

        paths.ensure_user_dirs()
        os.makedirs(SCHEMATICS_DIR, exist_ok=True)
        self.setStyleSheet(self._stylesheet())
        self.init_ui()
        self._ui_ready = True
        self._apply_adaptive_layout()
        self.reload_devices()
        self._show_system_status()
        # Aviso de instalación limpia (una sola vez por equipo).
        QTimer.singleShot(300, self._maybe_first_run_message)

    # ---------------- Adaptación a la pantalla ----------------
    @staticmethod
    def _screen_geometry():
        """Geometría útil de la pantalla (descontando barras/dock)."""
        screen = QApplication.primaryScreen()
        if screen is None:
            from PyQt5.QtWidgets import QDesktopWidget
            return QDesktopWidget().availableGeometry()
        return screen.availableGeometry()

    def _set_compact(self, compact: bool):
        """Aplica el modo compacto de forma idempotente.

        En modo compacto las acciones secundarias (compartir/importar/
        restablecer) se esconden en un menú «⋯ Más» para que la barra de
        botones quepa en pantallas estrechas.
        """
        compact = bool(compact)
        changed = compact != self._compact
        self._compact = compact
        if not self._ui_ready:
            return
        # Solo toca la interfaz si el estado cambió: así el redimensionado no
        # repinta la hoja de estilo en cada píxel (importante en PCs modestos).
        if changed:
            for b in (self.btn_share, self.btn_import_pkg, self.btn_reset):
                b.setVisible(not compact)
            self.btn_more.setVisible(compact)
            self.setStyleSheet(self._stylesheet())

    def _apply_adaptive_layout(self):
        """Ajusta tamaño, modo compacto y splitter según la pantalla actual."""
        geo = self._screen_geometry()
        sw, sh = geo.width(), geo.height()

        # Tamaño objetivo: 1280x820 como máximo, encogido a la pantalla real.
        max_w, max_h = max(640, sw - 30), max(480, sh - 70)
        target_w = max(640, min(1280, max_w))
        target_h = max(480, min(820, max_h))
        x = geo.x() + max(0, (sw - target_w) // 2)
        y = geo.y() + max(0, (sh - target_h) // 3)
        self.setGeometry(x, y, target_w, target_h)

        # Mínimos realistas: la ventana puede encogerse sin desbordar porque
        # los paneles ahora tienen scroll.
        self.setMinimumSize(min(680, target_w), min(480, target_h))

        self._set_compact(sw < 1366 or sh < 768)

        # Reparto inicial del splitter (damos algo más al panel de pestañas).
        try:
            self.splitter.setSizes([int(target_w * 0.44), int(target_w * 0.56)])
        except Exception:
            pass

    def resizeEvent(self, event):
        """Reacciona a cambios de tamaño de la ventana (redimensionado)."""
        super().resizeEvent(event)
        if not self._ui_ready:
            return
        # Al encoger la ventana por debajo de ese ancho/alto, activamos el modo
        # compacto para que los botones no se salgan de la pantalla.
        self._set_compact(self.width() < 1100 or self.height() < 640)

    def _maybe_first_run_message(self):
        """Muestra un aviso de instalación limpia la primera vez."""
        if not migration.is_first_run():
            return
        migration.mark_first_run_done()
        try:
            QMessageBox.information(
                self, translations.tr('first_run_title'),
                translations.tr('first_run_msg', home=paths.DATA_HOME))
        except Exception:
            pass

    def _show_system_status(self):
        ocr = self.config.ocr_available()
        if ocr:
            msg = translations.tr('system_ready_ocr', langs=self.config.ocr_langs, path=self.config.tesseract_path)
        else:
            msg = translations.tr('system_ready_noocr')
        self.status_bar.showMessage(msg)

    # ---------------- Estilo ----------------
    def _stylesheet(self):
        base = load_qdarkstyle()
        compact = self._compact if hasattr(self, '_compact') else False
        pad = "5px 9px" if compact else "7px 12px"
        extra = """
        QPushButton {
            padding: %s; border-radius: 6px; font-weight: 600;
        }
        QPushButton:hover { background-color: #2d6cdf; }
        QLineEdit {
            padding: %s; border-radius: 6px; font-size: 14px;
        }
        QTableWidget { gridline-color: #2a2f3a; }
        QHeaderView::section {
            padding: 4px; font-weight: 700; background-color: #232a36;
            border: none; border-right: 1px solid #2a2f3a;
        }
        QGroupBox {
            font-weight: 700; border: 1px solid #2f3a4c; border-radius: 6px;
            margin-top: 12px; padding-top: 8px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        QTabWidget::pane { border: 1px solid #2f3a4c; }
        """ % (pad, "6px 9px" if compact else "8px 10px")
        return base + extra


    # ---------------- UI ----------------
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 6)
        root.setSpacing(6)

        # --- Barra de título propia ---
        header = QHBoxLayout()
        logo = QLabel()
        icon = _app_icon()
        if not icon.isNull():
            logo.setPixmap(icon.pixmap(40, 40))
        title = QLabel("SchematicBuq")
        tf = QFont(); tf.setPointSize(17); tf.setBold(True)
        title.setFont(tf)
        self.lbl_subtitle = QLabel(translations.tr('subtitle'))
        self.lbl_subtitle.setStyleSheet("color:#8fa3bf; font-size:12px;")
        self.lbl_subtitle.setWordWrap(True)
        header.addWidget(logo)
        header.addWidget(title)
        header.addWidget(self.lbl_subtitle)
        header.addStretch()
        root.addLayout(header)

        # --- Barra de acciones (responsive) ---
        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.btn_add_files = QPushButton(translations.tr('add_files'))
        self.btn_add_files.setToolTip(translations.tr('add_files_tooltip'))
        self.btn_add_folder = QPushButton(translations.tr('add_folder'))
        self.btn_add_folder.setToolTip(translations.tr('add_folder_tooltip'))
        self.btn_add_url = QPushButton(translations.tr('add_url'))
        self.btn_add_url.setToolTip(translations.tr('add_url_tooltip'))
        self.btn_new_device = QPushButton(translations.tr('new_device'))
        self.btn_new_device.setToolTip(translations.tr('new_device_tooltip'))
        self.btn_assign_device = QPushButton(translations.tr('assign_device'))
        self.btn_assign_device.setToolTip(translations.tr('assign_device_tooltip'))
        self.btn_help = QPushButton(translations.tr('help'))
        self.btn_help.setToolTip(translations.tr('help_tooltip'))
        self.btn_clear = QPushButton(translations.tr('clear'))
        self.btn_clear.setToolTip(translations.tr('clear_tooltip'))
        self.btn_index = QPushButton(translations.tr('analyze'))
        self.btn_index.setToolTip(translations.tr('analyze_tooltip'))
        self.btn_index.setStyleSheet("background-color:#2563eb;color:white;")
        self.btn_share = QPushButton(translations.tr('share'))
        self.btn_share.setToolTip(translations.tr('share_tooltip'))
        self.btn_import_pkg = QPushButton(translations.tr('import_pkg'))
        self.btn_import_pkg.setToolTip(translations.tr('import_pkg_tooltip'))
        self.btn_reset = QPushButton(translations.tr('reset'))
        self.btn_reset.setToolTip(translations.tr('reset_tooltip'))

        # Botón "⋯ Más" que agrupa acciones secundarias en pantallas pequeñas.
        self.btn_more = QToolButton()
        self.btn_more.setText("⋯")
        self.btn_more.setToolTip(translations.tr('more_actions'))
        self.btn_more.setPopupMode(QToolButton.InstantPopup)
        self.menu_more = QMenu(self.btn_more)
        self.act_more_share = self.menu_more.addAction(translations.tr('share'))
        self.act_more_import = self.menu_more.addAction(translations.tr('import_pkg'))
        self.act_more_reset = self.menu_more.addAction(translations.tr('reset'))
        self.btn_more.setMenu(self.menu_more)
        self.btn_more.setVisible(False)

        for b in (self.btn_add_files, self.btn_add_folder, self.btn_add_url,
                  self.btn_new_device, self.btn_assign_device, self.btn_share,
                  self.btn_import_pkg, self.btn_help, self.btn_reset,
                  self.btn_clear, self.btn_more):
            b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            actions.addWidget(b)
        actions.addStretch()
        actions.addWidget(self.btn_index)
        root.addLayout(actions)

        # --- Selección de aparato + estado ---
        dev_row = QHBoxLayout()
        dev_row.setSpacing(6)
        dev_row.addWidget(QLabel(translations.tr('active_device')))
        self.cmb_devices = QComboBox()
        self.cmb_devices.setMinimumWidth(180)
        self.cmb_devices.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        dev_row.addWidget(self.cmb_devices)
        self.btn_open_device = QPushButton(translations.tr('open_folder'))
        dev_row.addWidget(self.btn_open_device)
        dev_row.addStretch()
        self.chk_ocr = QCheckBox(translations.tr('ocr_scan'))
        self.chk_ocr.setChecked(True)
        self.chk_ocr.setToolTip(translations.tr('ocr_tooltip'))
        dev_row.addWidget(self.chk_ocr)
        self.lbl_files = QLabel(translations.tr('files_in_queue', n=0))
        dev_row.addWidget(self.lbl_files)
        root.addLayout(dev_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        root.addWidget(self.progress_bar)

        # --- Búsqueda ---
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(translations.tr('search_placeholder'))
        self.btn_search = QPushButton(translations.tr('search'))
        self.search_input.setMinimumHeight(32)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.btn_search)
        self.btn_back = QPushButton("↩")
        self.btn_back.setToolTip(translations.tr('back_tooltip'))
        search_row.addWidget(self.btn_back)
        self.lbl_on_select = QLabel(translations.tr('on_select'))
        search_row.addWidget(self.lbl_on_select)
        self.cmb_auto = QComboBox()
        self.cmb_auto.addItems([translations.tr('multimeter'),
                                translations.tr('interaction'),
                                translations.tr('diagnostic'),
                                translations.tr('no_change')])
        self.cmb_auto.setToolTip(translations.tr('auto_tab_tooltip'))
        self.cmb_auto.setCurrentText(self.config.auto_tab or translations.tr('multimeter'))
        search_row.addWidget(self.cmb_auto)
        root.addLayout(search_row)

        self.lbl_hint = QLabel(translations.tr('hint'))
        self.lbl_hint.setStyleSheet("color:#8fa3bf; font-size:11px;")
        self.lbl_hint.setWordWrap(True)
        root.addWidget(self.lbl_hint)

        # --- Splitter (se guarda para ajuste adaptativo) ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setHandleWidth(6)

        # Izquierda: esquemáticos del aparato + resultados
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0)

        self.files_box = QGroupBox(translations.tr('device_files'))
        fl = QVBoxLayout(self.files_box)
        self.lst_files = QListWidget()
        self.lst_files.setMaximumHeight(96)
        self.lst_files.setToolTip(translations.tr('device_files_tooltip'))
        self.lst_files.itemClicked.connect(self.on_file_clicked)
        self.lst_files.itemDoubleClicked.connect(self.open_file_in_viewer)
        fl.addWidget(self.lst_files)
        self.files_box.setVisible(False)
        ll.addWidget(self.files_box)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            translations.tr('col_designator'), translations.tr('col_value'),
            translations.tr('col_type'), translations.tr('col_file'),
            translations.tr('col_page'), translations.tr('col_source'),
            translations.tr('col_device')])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setWordWrap(False)
        ll.addWidget(self.table, 1)
        self.splitter.addWidget(left)

        # Derecha: pestañas
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)     # flechas si no caben las pestañas
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.setDocumentMode(True)
        # Evita que rellenar la tabla abra sola la pestaña Multímetro.
        self._suppress_auto_tab = False
        self.pdf_viewer = PDFViewer()
        self.conn_panel = ConnectionsPanel()
        self.nomen_panel = NomenclaturePanel()
        self.divider_panel = VoltageDividerPanel()
        self.component_view = ComponentView()
        self.diag_panel = DiagnosticPanel()
        self.multi_panel = MultimeterPanel()
        self.inter_panel = InteractionPanel()
        self.help_panel = HelpPanel()
        self.tabs.addTab(self.pdf_viewer, translations.tr('tab_viewer'))
        self.tabs.addTab(self.component_view, translations.tr('tab_component'))
        self.tabs.addTab(self.inter_panel, translations.tr('tab_interaction'))
        self.tabs.addTab(self.multi_panel, translations.tr('tab_multimeter'))
        self.tabs.addTab(self.diag_panel, translations.tr('tab_diagnostic'))
        self.tabs.addTab(self.conn_panel, translations.tr('tab_connections'))
        self.tabs.addTab(self.nomen_panel, translations.tr('tab_nomenclature'))
        self.tabs.addTab(self.divider_panel, translations.tr('tab_divider'))
        self.tabs.addTab(self.help_panel, translations.tr('tab_help'))
        rl.addWidget(self.tabs)
        self.splitter.addWidget(right)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 4)
        root.addWidget(self.splitter, 1)

        # --- Status ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(translations.tr('status_ready'))

        # --- Conexiones de señales ---
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_url.clicked.connect(self.add_from_url)
        self.btn_new_device.clicked.connect(self.new_device)
        self.btn_assign_device.clicked.connect(self.assign_device_folder)
        self.btn_share.clicked.connect(self.share_schematics)
        self.btn_import_pkg.clicked.connect(self.import_package)
        self.btn_reset.clicked.connect(self.reset_all_data)
        self.act_more_share.triggered.connect(self.share_schematics)
        self.act_more_import.triggered.connect(self.import_package)
        self.act_more_reset.triggered.connect(self.reset_all_data)
        self.btn_open_device.clicked.connect(self.open_device_folder)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_help.clicked.connect(self.show_help)
        self.help_panel.action.connect(self.on_help_action)
        self.btn_index.clicked.connect(self.start_indexing)
        self.btn_search.clicked.connect(self.search)
        self.search_input.returnPressed.connect(self.search)
        self.table.itemSelectionChanged.connect(self.on_select_item)
        self.table.doubleClicked.connect(self.open_in_viewer)
        self.pdf_viewer.pageChanged.connect(self.on_viewer_page_changed)
        self.pdf_viewer.componentClicked.connect(self.on_viewer_component_clicked)
        self.cmb_devices.currentIndexChanged.connect(self.on_device_changed)
        self.conn_panel.component_clicked.connect(self.jump_to_component)
        self.inter_panel.component_clicked.connect(self.navigate_to_component)
        self.inter_panel.open_requested.connect(self.open_component_in_viewer)
        self.inter_panel.tab_requested.connect(self.on_interaction_tab)
        self.inter_panel.back_requested.connect(self.go_back)
        self.inter_panel.divider_requested.connect(self.on_divider_requested)
        self.btn_back.clicked.connect(self.go_back)
        self.cmb_auto.currentTextChanged.connect(self.on_auto_tab_changed)


    # ---------------- Aparatos ----------------
    def reload_devices(self):
        self.cmb_devices.blockSignals(True)
        self.cmb_devices.clear()
        self.cmb_devices.addItem(translations.tr('none'))
        names = []
        for d in self.device_db.get_devices():
            self.cmb_devices.addItem(d['name'])
            names.append(d['name'])
        self.cmb_devices.blockSignals(False)

        # Por defecto, al abrir la app se selecciona el último aparato analizado
        # (o el único existente) y se cargan sus esquemáticos automáticamente.
        target = self.config.last_device if self.config.last_device in names else ""
        if not target and len(names) == 1:
            target = names[0]
        if target:
            i = self.cmb_devices.findText(target)
            if i > 0:
                self.cmb_devices.setCurrentIndex(i)   # dispara on_device_changed
                return
        self.current_device = ""
        # Si no hay ningún aparato todavía, mostramos la guía de inicio.
        if not names:
            self.tabs.setCurrentWidget(self.help_panel)

    def on_device_changed(self, idx):
        # "Ninguno": se vacía la cola de archivos, el índice y el visor.
        if idx <= 0:
            self.current_device = ""
            self.config.last_device = ""
            self.config.save()
            self._reset_workspace(translations.tr('no_device_selected'))
            return

        self.current_device = self.cmb_devices.currentText()
        self.config.last_device = self.current_device
        self.config.save()

        # Al elegir un aparato se cargan sus esquemáticos automáticamente y se
        # indexan (instantáneo si ya están en la caché de análisis).
        if self._load_device_paths():
            self.refresh_device_files()
            self.files_box.setVisible(True)
            self.status_bar.showMessage(
                f"Aparato activo: {self.current_device} — cargando esquemáticos…")
            self.start_indexing(auto=True)
        else:
            # El aparato elegido no tiene carpeta: no debemos dejar el índice
            # del aparato anterior (la tabla mostraría componentes ajenos).
            # Solo limpiamos el índice y los paneles; la cola de archivos se
            # respeta por si el usuario la añadió a mano.
            if any((r.device or "") != self.current_device for r in self.index.results):
                self.index.clear()
                self.table.setRowCount(0)
                self.pdf_viewer.close_pdf()
                self.component_view.clear()
                self.diag_panel.clear()
                self.multi_panel.clear()
                self.inter_panel.clear()
                self.nomen_panel.clear()
                self.conn_panel.show_component("", self.index)
                self._nav_history = []
            self.refresh_device_files()
            self.files_box.setVisible(bool(self.lst_files.count()))
            self.status_bar.showMessage(
                f"Aparato activo: {self.current_device} — sin carpeta definida")

    def _reset_workspace(self, message=""):
        """Vacía cola, índice, tabla, lista de archivos y visor."""
        self.paths = []
        self.index.clear()
        self.table.setRowCount(0)
        self.lst_files.clear()
        self.files_box.setVisible(False)
        self.pdf_viewer.close_pdf()
        self.component_view.clear()
        self.diag_panel.clear()
        self.multi_panel.clear()
        self.inter_panel.clear()
        self.nomen_panel.clear()
        self.conn_panel.show_component("", self.index)
        self._nav_history = []
        self.update_paths_label()
        if message:
            self.status_bar.showMessage(message)

    # ---------------- Ayuda ----------------
    def show_help(self):
        self.tabs.setCurrentWidget(self.help_panel)

    def on_help_action(self, action):
        if action == "index":
            self.start_indexing()
            self.tabs.setCurrentWidget(self.pdf_viewer)
        elif action == "search":
            self.tabs.setCurrentWidget(self.pdf_viewer)
            self.search_input.setFocus()
            self.search_input.selectAll()
        elif action == "device":
            self.cmb_devices.setFocus()
            self.cmb_devices.showPopup()

    def _load_device_paths(self):
        """Rellena self.paths con la carpeta guardada del aparato activo."""
        if not self.current_device:
            return False
        dev = self.device_db.find_device(self.current_device)
        if not dev:
            return False
        folder = dev.get('folder', '')
        if folder and os.path.isdir(folder):
            self.paths = [folder]
            self.update_paths_label()
            return True
        return False

    @staticmethod
    def _scan_files(paths):
        """Lista los esquemáticos soportados de una cola de archivos/carpetas."""
        files = []
        for p in paths:
            if os.path.isfile(p):
                if os.path.splitext(p)[1].lower() in SUPPORTED_EXTS:
                    files.append(os.path.normpath(p))
            elif os.path.isdir(p):
                for root, _dirs, names in os.walk(p):
                    for f in sorted(names):
                        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS:
                            files.append(os.path.normpath(os.path.join(root, f)))
        return list(dict.fromkeys(files))   # deduplicar conservando el orden

    def refresh_device_files(self):
        """Muestra los esquemáticos del aparato con su nº de componentes."""
        self.lst_files.clear()
        files = self._scan_files(self.paths)
        counts = {}
        for r in self.index.results:
            k = _norm_path(r.file_path)
            counts[k] = counts.get(k, 0) + 1
        for p in files:
            n = counts.get(_norm_path(p), 0)
            label = os.path.basename(p) + (f"   —   {n} comp." if n else "")
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, p)
            it.setToolTip(p)
            self.lst_files.addItem(it)
        if self.current_device:
            self.files_box.setTitle(
                f"📄 Esquemáticos de {self.current_device} ({len(files)})")
        else:
            self.files_box.setTitle(f"📄 Esquemáticos en cola ({len(files)})")
        return files

    def on_file_clicked(self, item):
        """Clic en un esquemático: muestra todos sus componentes en la tabla."""
        path = item.data(Qt.UserRole) if item else None
        if not path:
            return
        target = _norm_path(path)
        results = [r for r in self.index.results if _norm_path(r.file_path) == target]
        self.populate_table(results, "")
        self.status_bar.showMessage(
            f"{os.path.basename(path)} — {len(results)} componente(s)")

    def open_file_in_viewer(self, item):
        """Doble clic en un esquemático: lo abre en el visor."""
        path = item.data(Qt.UserRole) if item else None
        if not path or not os.path.exists(path):
            return
        ext = os.path.splitext(path)[1].lower()
        if ext == '.pdf':
            self.pdf_viewer.load_pdf(path, highlight_words=[], highlight_rects={}, page=1)
            self.tabs.setCurrentIndex(0)
            self.status_bar.showMessage(f"Abierto {os.path.basename(path)}")
        else:
            self.open_external(path)

    def new_device(self):
        name, ok = QInputDialog.getText(
            self, translations.tr('new_device'),
            translations.tr('device_name_prompt'))
        if not (ok and name.strip()):
            return
        name = name.strip()
        folder = os.path.join(SCHEMATICS_DIR, self._safe_name(name))
        os.makedirs(folder, exist_ok=True)
        self.device_db.add_device(name, folder)
        self.config.last_device = name
        self.config.save()
        self.reload_devices()
        QMessageBox.information(
            self, translations.tr('device_created'),
            translations.tr('device_created_msg', name=name, folder=folder))

    @staticmethod
    def _safe_name(name):
        bad = '<>:"/\\|?*'
        for c in bad:
            name = name.replace(c, '_')
        return name.strip() or "aparato"

    def open_device_folder(self):
        if not self.current_device:
            QMessageBox.information(self, translations.tr('no_device'),
                                    translations.tr('select_device_first'))
            return
        dev = self.device_db.find_device(self.current_device)
        if not dev:
            return
        folder = dev['folder']
        os.makedirs(folder, exist_ok=True)
        try:
            self._open_path(folder)
        except Exception as e:
            QMessageBox.warning(self, translations.tr('error'), str(e))

    def assign_device_folder(self):
        """Copia los archivos en cola a la carpeta del aparato activo."""
        if not self.current_device:
            QMessageBox.information(self, translations.tr('no_device'),
                                    translations.tr('create_device_first'))
            return
        dev = self.device_db.find_device(self.current_device)
        if not dev:
            return
        folder = dev['folder']
        os.makedirs(folder, exist_ok=True)
        moved = []
        for p in list(self.paths):
            if os.path.isfile(p):
                try:
                    dest = os.path.join(folder, os.path.basename(p))
                    shutil.copy2(p, dest)
                    moved.append(dest)
                    self.paths.remove(p)
                    self.paths.append(dest)
                except Exception as e:
                    print("Error copiando", p, e)
        self.update_paths_label()
        QMessageBox.information(
            self, translations.tr('saved'),
            translations.tr('saved_msg', n=len(moved), folder=folder))

    # ---------------- Compartir / base de datos local ----------------
    def _store_current_files(self):
        """Copia los esquemáticos en cola al almacén local (por aparato)."""
        device = self.current_device or "General"
        for p in list(self.paths):
            if os.path.isfile(p):
                try:
                    self.store.save_file(p, device)
                except Exception:
                    pass

    def share_schematics(self):
        """Exporta un paquete .sbq seguro (solo esquemáticos, sin ejecutables)."""
        self._store_current_files()
        device = self.current_device or None
        default = os.path.join(
            os.path.expanduser("~"),
            f"schematicbuq_{device or 'todos'}.sbq")
        dest, _ = QFileDialog.getSaveFileName(
            self, translations.tr('share'), default,
            "Paquete SchematicBuq (*.sbq)")
        if not dest:
            return
        if not dest.lower().endswith(".sbq"):
            dest += ".sbq"
        try:
            self.store.export_package(dest, device=device, index=self.index)
        except Exception as e:
            QMessageBox.warning(self, translations.tr('error'), str(e))
            return
        QMessageBox.information(
            self, translations.tr('share'),
            translations.tr('share_done', path=dest))

    def import_package(self):
        """Importa un paquete .sbq validando que solo traiga esquemáticos."""
        src, _ = QFileDialog.getOpenFileName(
            self, translations.tr('import_pkg'), "",
            "Paquete SchematicBuq (*.sbq *.zip)")
        if not src:
            return
        try:
            imported, skipped = self.store.import_package(src)
        except Exception as e:
            QMessageBox.warning(self, translations.tr('error'),
                                translations.tr('import_failed', err=e))
            return
        # Añade los esquemáticos importados a la cola e índice
        for p in imported:
            if p not in self.paths:
                self.paths.append(p)
        self.update_paths_label()
        msg = translations.tr('import_done', n=len(imported))
        if skipped:
            msg += "\n\n" + translations.tr('import_skipped', n=len(skipped))
        QMessageBox.information(self, translations.tr('import_pkg'), msg)

    # ---------------- Archivos ----------------
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, translations.tr('select_schematics'), "",
            "Soportados (*.pdf *.png *.jpg *.jpeg *.bmp *.tif *.tiff *.net *.cir *.txt *.sp "
            "*.kicad_sch *.kicad_sym *.sch *.json *.schdoc *.pcbdoc);;"
            "PDF (*.pdf);;Imágenes (*.png *.jpg *.jpeg *.bmp);;"
            "Netlists (*.net *.cir *.txt *.sp);;KiCad (*.kicad_sch *.sch);;"
            "EasyEDA (*.json);;Altium (*.schdoc *.pcbdoc)")
        for f in files:
            if f not in self.paths:
                self.paths.append(f)
        self.update_paths_label()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, translations.tr('select_folder'))
        if not folder:
            return
        if folder not in self.paths:
            self.paths.append(folder)
        # Auto-registrar el aparato con el nombre de la carpeta
        name = os.path.basename(os.path.normpath(folder))
        if name and not self.device_db.find_device(name):
            self.device_db.add_device(name, folder)
            self.config.last_device = name
            self.config.save()
            self.reload_devices()
            self.status_bar.showMessage(translations.tr('device_registered', name=name))
        self.update_paths_label()

    def add_from_url(self):
        url, ok = QInputDialog.getText(
            self, translations.tr('import_url'),
            translations.tr('import_url_prompt'))
        if not (ok and url.strip()):
            return
        self.status_bar.showMessage(translations.tr('downloading_pdf'))
        from utils.pdf_online import PDFOnlineFetcher
        dest_dir = SCHEMATICS_DIR
        if self.current_device:
            dev = self.device_db.find_device(self.current_device)
            if dev:
                dest_dir = dev['folder']
        filepath = PDFOnlineFetcher.fetch_pdf(url.strip(), save_dir=dest_dir)
        if filepath:
            if filepath not in self.paths:
                self.paths.append(filepath)
            self.update_paths_label()
            self.status_bar.showMessage(f"Descargado: {os.path.basename(filepath)}")
            QMessageBox.information(self, "Descargado",
                                    f"PDF guardado en:\n{filepath}")
        else:
            QMessageBox.warning(self, "Error",
                                "No se pudo descargar el PDF. Verifica la URL.")

    def update_paths_label(self):
        n = len(self._scan_files(self.paths))
        self.lbl_files.setText(f"{n} esquemático(s)")

    def clear_all(self):
        self._reset_workspace(translations.tr('cleared'))

    # ---------------- Restablecer / primer uso ----------------
    def reset_all_data(self):
        """Borra TODOS los datos locales (aparatos, caché, esquemáticos)."""
        resp = QMessageBox.question(
            self, translations.tr('reset_title'),
            translations.tr('reset_confirm'),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        from utils import reset as reset_mod
        errors = reset_mod.reset_user_data()
        # Vuelve a crear las carpetas base por si el borrado las eliminó.
        paths.ensure_user_dirs()
        os.makedirs(SCHEMATICS_DIR, exist_ok=True)
        # Reinicia el estado en memoria
        self.paths = []
        self.current_device = ""
        self.index.clear()
        self.table.setRowCount(0)
        self.device_db = DeviceDB()
        self.config.last_device = ""
        self.config.save()
        self.reload_devices()
        self._reset_workspace(translations.tr('reset_done'))
        if errors:
            QMessageBox.warning(self, translations.tr('error'),
                                "\n".join(errors))

    # ---------------- Indexado ----------------
    def start_indexing(self, auto=False):
        if self._indexing:
            # Si se cambia de aparato mientras se indexa, se reindexará al
            # terminar para no quedarnos con el índice del aparato anterior.
            self._restart_index = True
            return
        if not self.paths:
            if not auto:
                QMessageBox.warning(self, "Sin archivos",
                                    "Añade al menos un archivo o carpeta.")
            return
        self._auto_index = auto
        self._indexing = True
        self._restart_index = False
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_index.setEnabled(False)
        self.index.clear()
        self.table.setRowCount(0)
        files = self.refresh_device_files()
        self.files_box.setVisible(bool(files))
        self.thread = IndexerThread(self.paths, self.index, device=self.current_device,
                                    use_ocr=self.chk_ocr.isChecked(),
                                    cache=self.parse_cache)
        self.thread.progress.connect(self.on_progress)
        self.thread.detail.connect(self.on_detail)
        self.thread.index_done.connect(self.on_index_finished)
        self.thread.start()

    def on_detail(self, msg):
        self.status_bar.showMessage(msg)

    def on_progress(self, val, fname):
        self.progress_bar.setValue(val)
        self.status_bar.showMessage(f"Indexando... {fname}")

    def on_index_finished(self):
        self._indexing = False
        self.progress_bar.setVisible(False)
        self.btn_index.setEnabled(True)
        total = len(self.index.results)
        nets = len(self.index.connections)
        self.refresh_device_files()
        if self.current_device:
            self.device_db.set_components(self.current_device, total)
        self.status_bar.showMessage(
            f"Indexado completo: {total} componentes, {nets} nodos/nets detectados")
        if not self._auto_index:
            QMessageBox.information(
                self, "Indexado completado",
                f"Componentes encontrados: {total}\nNodos/nets detectados: {nets}\n\n"
                "Ya puedes buscar (ej. R46).")
        self._auto_index = False
        # Si se cambió de aparato mientras se indexaba, reindexar el correcto.
        if self._restart_index:
            self._restart_index = False
            if self.paths:
                self.start_indexing(auto=True)
                return
        # Si el usuario buscó mientras indexaba, lanzamos esa búsqueda ahora.
        if self._pending_search is not None:
            query, self._pending_search = self._pending_search, None
            self.search_input.setText(query)
            self.search()

    # ---------------- Búsqueda ----------------
    def _device_filter(self):
        return "" if not self.current_device else self.current_device

    def search(self):
        query = self.search_input.text()
        # Si todavía no hay índice pero sí archivos, indexamos y buscamos al
        # terminar (auto-indexado transparente "en caso de una búsqueda").
        if not self.index.results and not self._indexing:
            if not self.paths:
                self._load_device_paths()
            if self.paths:
                self._pending_search = query
                self.start_indexing(auto=True)
                return
        # Si hay aparato activo y hay resultados para ese aparato, filtramos
        results = self.index.search(query)
        dev = self._device_filter()
        if dev:
            filtered = [r for r in results if (r.device or "") == dev]
            if filtered:
                results = filtered
        self.populate_table(results, query)

    def populate_table(self, results, query=""):
        self._suppress_auto_tab = True
        try:
            self._fill_table(results)
        finally:
            self._suppress_auto_tab = False
        self.status_bar.showMessage(f"{len(results)} resultado(s)")

    def _fill_table(self, results):
        # Bloqueamos señales mientras rellenamos y limpiamos la selección: así,
        # al seleccionar después la fila 0, SIEMPRE se refrescan los paneles
        # (antes, si la fila 0 ya estaba seleccionada, no se actualizaba nada).
        self.table.blockSignals(True)
        try:
            self.table.clearSelection()
            self.table.setRowCount(len(results))
            for i, r in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(r.designator))
                self.table.setItem(i, 1, QTableWidgetItem(r.value))
                self.table.setItem(i, 2, QTableWidgetItem(r.component_type))
                it_file = QTableWidgetItem(os.path.basename(r.file_path))
                it_file.setToolTip(r.file_path)
                self.table.setItem(i, 3, it_file)
                self.table.setItem(i, 4, QTableWidgetItem(str(r.page)))
                self.table.setItem(i, 5, QTableWidgetItem(r.source_type))
                self.table.setItem(i, 6, QTableWidgetItem(r.device or ""))
                self.table.item(i, 0).setData(Qt.UserRole, r.designator)
                self.table.item(i, 3).setData(Qt.UserRole, r.file_path)
                self.table.item(i, 4).setData(Qt.UserRole, r.page)
                self.table.item(i, 0).setData(Qt.UserRole + 1, r.rects)
        finally:
            self.table.blockSignals(False)

    def current_row_data(self):
        return self.row_data(self.table.currentRow())

    def row_data(self, row):
        if row is None or row < 0 or row >= self.table.rowCount():
            return None
        c0 = self.table.item(row, 0)
        c1 = self.table.item(row, 1)
        c2 = self.table.item(row, 2)
        c3 = self.table.item(row, 3)
        c4 = self.table.item(row, 4)
        c5 = self.table.item(row, 5)
        return {
            'designator': c0.data(Qt.UserRole) if c0 else "",
            'value': c1.text() if c1 else "",
            'type': c2.text() if c2 else "",
            'file': c3.data(Qt.UserRole) if c3 else "",
            'page': c4.data(Qt.UserRole) if c4 else 1,
            'source': c5.text() if c5 else "",
            'rects': c0.data(Qt.UserRole + 1) if c0 else [],
        }

    def on_select_item(self):
        data = self.current_row_data()
        if not data:
            return
        des = data['designator']
        self._update_component_panels(
            des, data.get('value', ''), data.get('type', ''), data.get('source', ''),
            file_path=data.get('file', ''), page=data.get('page') or 1)
        # La pestaña que se abre al seleccionar es configurable («Al seleccionar»).
        if not getattr(self, "_suppress_auto_tab", False):
            self._auto_open_tab()

    def _auto_open_tab(self):
        """Abre la pestaña elegida en «Al seleccionar:»."""
        w = {
            "Multímetro": self.multi_panel,
            "Interacción": self.inter_panel,
            "Diagnóstico": self.diag_panel,
        }.get(self.cmb_auto.currentText())
        if w is not None:
            self.tabs.setCurrentWidget(w)

    def on_auto_tab_changed(self, text):
        self.config.auto_tab = text
        self.config.save()

    def _update_component_panels(self, des, value="", ctype="", source="",
                                 file_path="", page=0):
        """Refresca todas las pestañas que describen un componente."""
        self.nomen_panel.show_info(des)
        self.conn_panel.show_component(des, self.index)
        self.component_view.show_component(des, value, ctype, source)
        self.diag_panel.show_component(des, value, ctype)
        self.multi_panel.show_component(des, value, ctype)
        self.inter_panel.show_component(des, value, ctype, source, self.index,
                                        file_path=file_path, page=page)

    def open_in_viewer(self, index=None):
        row = index.row() if index is not None and hasattr(index, 'row') else -1
        data = self.row_data(row)
        if data is None:
            data = self.current_row_data()
        if not data:
            return
        filepath = data['file']
        page = data['page'] or 1
        des = data['designator']
        if not filepath or not os.path.exists(filepath):
            return
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            rects_map = self._highlight_map_for(filepath, des)
            # Renderizamos directamente la página pedida (una sola vez).
            self.pdf_viewer.load_pdf(filepath, highlight_words=[des] if des else [],
                                     highlight_rects=rects_map, page=page)
            self.tabs.setCurrentIndex(0)
            self.status_bar.showMessage(
                f"{os.path.basename(filepath)} — página {page} — componente {des} resaltado")
        elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'):
            self.show_image(filepath, des)
        else:
            self.open_external(filepath)

    def _highlight_map_for(self, filepath, designator):
        """Construye {nº_página: [rects...]} con todos los rectángulos
        conocidos para ese designador en ese archivo (útil en escaneos/OCR)."""
        rects_map = {}
        if not designator:
            return rects_map
        des_up = designator.upper()
        target = _norm_path(filepath)
        for r in self.index.results:
            if _norm_path(r.file_path) != target or r.designator.upper() != des_up:
                continue
            for rect in (r.rects or []):
                rects_map.setdefault(r.page, []).append(rect)
        return rects_map

    def on_viewer_page_changed(self, filepath, page):
        """Rellena «Componentes de esta hoja» con lo detectado en esa página."""
        if not filepath:
            self.pdf_viewer.set_page_components([])
            return
        target = _norm_path(filepath)
        items, seen = [], set()
        for r in self.index.results:
            if _norm_path(r.file_path) != target or r.page != page:
                continue
            k = (r.designator.upper(), r.value or "")
            if k in seen:
                continue
            seen.add(k)
            items.append((r.designator, r.value or ""))
        items.sort(key=lambda t: t[0].upper())
        self.pdf_viewer.set_page_components(items)

    def on_viewer_component_clicked(self, des):
        """El usuario pulsó un componente en la lista del visor."""
        filepath = self.pdf_viewer._doc_path
        page = self.pdf_viewer.page + 1
        target = _norm_path(filepath)
        chosen = None
        for r in self.index.results:
            if (_norm_path(r.file_path) == target and r.page == page
                    and r.designator.upper() == des.upper()):
                chosen = r
                break
        # Refrescamos TODAS las pestañas con los datos de ese componente.
        self._update_component_panels(
            des,
            chosen.value if chosen else "",
            chosen.component_type if chosen else "",
            chosen.source_type if chosen else "",
            file_path=filepath, page=page)
        # Si su fila está en la tabla, la marcamos SIN saltar de pestaña.
        for i in range(self.table.rowCount()):
            d = self.row_data(i)
            if (d and _norm_path(d['file']) == target and (d['page'] or 1) == page
                    and d['designator'].upper() == des.upper()):
                self._suppress_auto_tab = True
                try:
                    self.table.setCurrentCell(i, 0)
                finally:
                    self._suppress_auto_tab = False
                break
        self.pdf_viewer.set_highlight([des], self._highlight_map_for(filepath, des))
        self.status_bar.showMessage(f"🔎 {des} resaltado en el esquemático")

    def show_image(self, filepath, des=""):
        """Muestra una imagen en un diálogo que se adapta a la pantalla."""
        dlg = QMessageBox(self)
        dlg.setWindowTitle(f"Imagen — {des}" if des else "Imagen")
        pix = QPixmap(filepath)
        if not pix.isNull():
            geo = self._screen_geometry()
            max_w = max(320, int(geo.width() * 0.7))
            max_h = max(240, int(geo.height() * 0.7))
            dlg.setIconPixmap(pix.scaled(max_w, max_h,
                                         Qt.KeepAspectRatio, Qt.SmoothTransformation))
        dlg.setText(os.path.basename(filepath))
        dlg.exec_()

    def open_external(self, filepath):
        self._open_path(filepath)

    def _open_path(self, filepath):
        """Abre un archivo/carpeta con la aplicación del sistema.

        Usa QDesktopServices (la forma segura y multiplataforma) y, si falla,
        recurre a un subproceso con lista de argumentos — nunca a un shell con
        la ruta interpolada, que se rompería con espacios o sería inyectable.
        """
        try:
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            if QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(filepath))):
                return
        except Exception:
            pass
        try:
            if sys.platform.startswith('win'):
                os.startfile(filepath)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', filepath])
            else:
                subprocess.Popen(['xdg-open', filepath])
        except Exception as e:
            QMessageBox.warning(self, translations.tr('error'),
                                translations.tr('open_failed', err=e))


    def _search_and_select(self, designator, push_history=False):
        """Busca un designador, rellena la tabla y selecciona su primera fila."""
        des = (designator or "").upper()
        if not des:
            return False
        self.search_input.setText(des)
        results = self.index.search(des)
        exact = [r for r in results if r.designator.upper() == des]
        if exact:
            results = exact
        if not results:
            return False
        if push_history:
            cur = self.current_row_data()
            cur_des = (cur.get('designator') or '').upper() if cur else ""
            if cur_des and cur_des != des:
                self._nav_history.append(cur_des)
                self._nav_history = self._nav_history[-40:]
        self.populate_table(results, des)
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
        return True

    def jump_to_component(self, designator):
        """Ir a un componente conectado y mostrarlo en el esquemático."""
        if self._search_and_select(designator, push_history=True):
            self.open_in_viewer()

    def navigate_to_component(self, designator):
        """Explorar otro componente SIN salir del panel de interacción."""
        self._suppress_auto_tab = True
        try:
            self._search_and_select(designator, push_history=True)
        finally:
            self._suppress_auto_tab = False

    def open_component_in_viewer(self, designator):
        """Abre en el visor el componente indicado (desde el mapa de interacción)."""
        des = (designator or "").upper()
        cur = self.current_row_data()
        if not cur or (cur.get('designator') or '').upper() != des:
            self._suppress_auto_tab = True
            try:
                ok = self._search_and_select(des)
            finally:
                self._suppress_auto_tab = False
            if not ok:
                return
        self.open_in_viewer()

    def go_back(self):
        """Vuelve al componente anterior de la navegación."""
        while self._nav_history:
            des = self._nav_history.pop()
            if self._search_and_select(des):
                self.status_bar.showMessage(f"↩ Volver a {des}")
                return
        self.status_bar.showMessage("No hay componente anterior")

    def on_interaction_tab(self, action):
        if action == "multimetro":
            self.tabs.setCurrentWidget(self.multi_panel)
        elif action == "diagnostico":
            self.tabs.setCurrentWidget(self.diag_panel)
        elif action == "esquematico":
            self.open_in_viewer()

    def on_divider_requested(self, r1, r2):
        """Lleva dos resistencias del mapa de interacción a la calculadora."""
        self.divider_panel.prefill(r1, r2)
        self.tabs.setCurrentWidget(self.divider_panel)
        self.status_bar.showMessage(f"🧮 Divisor de tensión: {r1} / {r2}")