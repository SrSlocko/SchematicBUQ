# -*- coding: utf-8 -*-
"""Verifica la geometría de rotación: compara rect sin rotar vs. rotado."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitz, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(BASE, "schematics", "Ampeg_B2R")

def crop_around(page, rect_display, zoom, tag, pad=120):
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    x0 = max(0, int(rect_display.x0 * zoom) - pad)
    y0 = max(0, int(rect_display.y0 * zoom) - pad)
    x1 = min(img.width, int(rect_display.x1 * zoom) + pad)
    y1 = min(img.height, int(rect_display.y1 * zoom) + pad)
    crop = img.crop((x0, y0, x1, y1))
    out = os.path.join(BASE, "tests", f"_rot_{tag}.png")
    crop.save(out)
    print("   guardado", out, crop.size, "img", img.size)
    return out

print("=== descarga (5).pdf (texto, rotation=90) ===")
doc = fitz.open(os.path.join(FOLDER, "descarga (5).pdf"))
page = doc[0]
print("page.rect:", page.rect, "rotation:", page.rotation)
print("mediabox:", page.mediabox)
hits = page.search_for("R21")
print("search_for R21 (sin rotar):", hits)
if hits:
    r = hits[0]
    print("rotation_matrix:", page.rotation_matrix)
    rr = r * page.rotation_matrix
    print("R21 rotado:", rr)
    print("-> crop SIN rotar (comportamiento actual):")
    crop_around(page, r, 6.0, "5_sin_rotar")
    print("-> crop CON rotacion aplicada:")
    crop_around(page, rr, 6.0, "5_rotado")
doc.close()

print("\n=== descarga (6).pdf (OCR, rotation=270) ===")
doc = fitz.open(os.path.join(FOLDER, "descarga (6).pdf"))
page = doc[0]
print("page.rect:", page.rect, "rotation:", page.rotation, "mediabox:", page.mediabox)
# rect OCR guardado (ya en coords display)
r_ocr = fitz.Rect(568.75, 110.5, 575.5, 113.75)
print("-> crop del rect OCR guardado (coords display):")
crop_around(page, r_ocr, 6.0, "6_ocr_display")
doc.close()
