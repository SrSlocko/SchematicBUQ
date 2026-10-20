# -*- coding: utf-8 -*-
"""Captura ampliada alrededor del componente resaltado."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.widgets.pdf_viewer import PDFViewer
from utils.search_index import ComponentResult

dump = json.load(open("_idx_dump.json", encoding="utf-8"))
results = [ComponentResult(**d) for d in dump]

cand = [r for r in results if r.rects and "descarga (3).pdf" in r.file_path and r.value]
target = cand[0]
print("Ejemplo:", target.designator, "=", target.value, "pág", target.page)

hmap = {}
for r in results:
    if r.file_path == target.file_path and r.designator == target.designator:
        for rect in r.rects:
            hmap.setdefault(r.page, []).append(rect)

v = PDFViewer()
v.resize(1400, 900)
v.load_pdf(target.file_path, highlight_words=[target.designator], highlight_rects=hmap)
v.go_to_page(target.page)
v.zoom_slider.setValue(200)   # 200%
app.processEvents()

pix = v.page_label.grab()
out = os.path.abspath("tests/_visor_zoom.png")
pix.save(out)
print("Guardado:", out, pix.width(), "x", pix.height())

# Recorte alrededor del primer resaltado (coords en el pixmap = rects * zoom)
rect = hmap[target.page][0]
zx = 2.0  # zoom
cx = int((rect[0] + rect[2]) / 2 * zx)
cy = int((rect[1] + rect[3]) / 2 * zx)
half = 160
x0 = max(0, cx - half)
y0 = max(0, cy - half)
w = min(pix.width() - x0, 2 * half)
h = min(pix.height() - y0, 2 * half)
crop = pix.copy(x0, y0, w, h)
crop_out = os.path.abspath("tests/_visor_crop.png")
crop.save(crop_out)
print("Recorte:", crop_out, crop.width(), "x", crop.height())
