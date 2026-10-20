# -*- coding: utf-8 -*-
"""Prueba de integración de aparatos: Ninguno vacía, seleccionar carga y lista."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp

w = SchematicSearchApp()
w.resize(1440, 860)
w.show()
app.processEvents()


def pump(limit=120):
    t0 = time.time()
    while w._indexing and time.time() - t0 < limit:
        app.processEvents()
        time.sleep(0.05)
    for _ in range(5):
        app.processEvents()


def dump(tag):
    print(f"\n[{tag}]")
    print("  combo        :", repr(w.cmb_devices.currentText()))
    print("  current_dev  :", repr(w.current_device))
    print("  paths        :", w.paths)
    print("  nº esquemáticos:", len(w._scan_files(w.paths)))
    print("  índice       :", len(w.index.results), "componentes")
    print("  tabla        :", w.table.rowCount(), "filas")
    print("  caja archivos visible:", w.files_box.isVisible(),
          "| items:", w.lst_files.count())
    for i in range(w.lst_files.count()):
        print("      ·", w.lst_files.item(i).text())
    print("  visor doc    :", w.pdf_viewer.doc is not None)


# 1) Arranque: debe autoseleccionar el último aparato y cargarlo
pump()
dump("ARRANQUE (último aparato)")

# 2) Seleccionar "Ninguno" (índice 0) -> debe vaciarlo todo
w.cmb_devices.setCurrentIndex(0)
app.processEvents()
dump("TRAS ELEGIR (Ninguno)")
assert w.paths == [], "paths debería estar vacío"
assert len(w.index.results) == 0, "el índice debería estar vacío"
assert w.table.rowCount() == 0, "la tabla debería estar vacía"
assert w.lst_files.count() == 0, "la lista de archivos debería estar vacía"
assert not w.files_box.isVisible(), "la caja de archivos debería ocultarse"
assert w.pdf_viewer.doc is None, "el visor debería cerrarse"
print("  -> OK: (Ninguno) vació la cola")

# 3) Volver a seleccionar el aparato -> debe recargar e indexar
i_dev = w.cmb_devices.findText("Ampeg_B2R")
if i_dev < 0:
    i_dev = 1
w.cmb_devices.setCurrentIndex(i_dev)
app.processEvents()
pump()
dump("TRAS RESELECCIONAR Ampeg_B2R")
assert len(w.index.results) > 0, "debería haber componentes"
assert w.lst_files.count() > 0, "debería listar los esquemáticos"
print("  -> OK: el aparato recargó sus esquemáticos")

# 4) Clic en el primer archivo -> muestra sus componentes
if w.lst_files.count():
    it = w.lst_files.item(0)
    w.on_file_clicked(it)
    app.processEvents()
    print(f"\n[CLIC EN '{it.text()}'] -> {w.table.rowCount()} componentes en tabla")
    assert w.table.rowCount() > 0, "debería mostrar componentes del archivo"
    print("  -> OK: clic en archivo muestra sus componentes")

# 5) Doble clic abre el visor
if w.lst_files.count():
    w.open_file_in_viewer(w.lst_files.item(0))
    app.processEvents()
    pm = w.pdf_viewer.page_label.pixmap()
    print("\n[Doble clic archivo] visor pixmap válido:",
          pm is not None and not pm.isNull())
    assert pm is not None and not pm.isNull()

print("\nTODO OK")
