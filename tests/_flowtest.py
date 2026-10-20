# -*- coding: utf-8 -*-
"""Flujo real de la app: añadir carpeta -> indexar -> buscar -> doble clic -> visor."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.app import SchematicSearchApp
from utils.file_loader import FileLoader

w = SchematicSearchApp()
w.resize(1440, 860)

FOLDER = os.path.abspath(os.path.join("schematics", "Ampeg_B2R"))
PDF = os.path.join(FOLDER, "descarga (5).pdf")   # tiene capa de texto -> rápido

# 1) Simular "Añadir carpeta"
w.paths.append(PDF)
w.update_paths_label()
print("Cola de archivos:", w.paths)

# 2) Indexar (directamente, sin el hilo) con OCR off para ir rápido
w.chk_ocr.setChecked(False)
loader = FileLoader(w.index, device="Ampeg_B2R", use_ocr=False)
loader.load_path(PDF)
print("Componentes indexados:", len(w.index.results))

# Asignar device como lo haría el hilo
for r in w.index.results:
    r.device = "Ampeg_B2R"

# 3) Buscar
w.search_input.setText("R46")
w.search()
print("Filas de resultados:", w.table.rowCount())
if w.table.rowCount():
    w.table.selectRow(0)
    app.processEvents()

    # 4) Doble clic -> visor
    w.open_in_viewer(w.table.model().index(0, 0))
    app.processEvents()

    v = w.pdf_viewer
    print(f"\n--- VISOR ---")
    print("total_pages:", v.total_pages)
    print("pagina actual:", v.page + 1)
    print("zoom:", v.zoom)
    print("pestana activa:", w.tabs.currentIndex())
    pm = v.page_label.pixmap()
    print("page_label pixmap nulo?", None if pm is None else pm.isNull())
    if pm is not None and not pm.isNull():
        img = pm.toImage()
        # Contar pixeles no blancos para confirmar que hay contenido real
        non_white = 0
        for y in range(0, img.height(), 4):
            for x in range(0, img.width(), 4):
                c = img.pixelColor(x, y)
                if c.red() < 245 or c.green() < 245 or c.blue() < 245:
                    non_white += 1
        print(f"pixeles no blancos (muestreo): {non_white} / "
              f"{(img.width()//4)*(img.height()//4)}")
    print("page_label size:", v.page_label.width(), "x", v.page_label.height())
    print("scroll viewport:", v.scroll.viewport().width(), "x", v.scroll.viewport().height())
    print("highlight rects (pag actual):", len(v.highlight_rects.get(v.page + 1, [])))

    # 5) Captura del visor entero
    out = os.path.abspath("tests/_flujo_visor.png")
    w.grab().save(out)
    print("Captura app:", out)

print("\nFIN")
