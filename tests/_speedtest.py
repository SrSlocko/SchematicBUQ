# -*- coding: utf-8 -*-
"""Prueba de velocidad (caché) + rotación (R21) + falsos positivos."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_index import SearchIndex
from utils.file_loader import FileLoader
from utils.parse_cache import ParseCache

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(BASE, "schematics", "Ampeg_B2R")
CACHE = os.path.join(BASE, "tests", "_parse_cache_test.json")
if os.path.exists(CACHE):
    os.remove(CACHE)


def run(tag):
    cache = ParseCache(CACHE)
    idx = SearchIndex()
    loader = FileLoader(idx, device="Ampeg_B2R", use_ocr=True, cache=cache,
                        progress=lambda m: None)
    t0 = time.time()
    loader.load_path(FOLDER)
    cache.save()
    dt = time.time() - t0
    print(f"[{tag}] {dt:.1f}s   componentes={len(idx.results)}")
    return idx, dt


idx1, t1 = run("1a pasada (OCR completo)")
idx2, t2 = run("2a pasada (desde caché)")

print(f"\nAceleración con caché: {t1 / t2:.0f}x  ({t1:.1f}s -> {t2:.1f}s)")

print("\n--- R21 ---")
for r in idx2.results:
    if r.designator.upper() == "R21":
        print(f"  {os.path.basename(r.file_path)} pag {r.page} "
              f"valor={r.value!r} rects={r.rects}")

print("\n--- Falsos positivos que deben haber desaparecido ---")
for bad in ("F074", "J112", "J176", "S176"):
    found = [r for r in idx2.results if r.designator.upper() == bad]
    print(f"  {bad}: {'AUN PRESENTE' if found else 'OK (eliminado)'}")

# Verificación de la rotación: renderizar el rect de R21 y comprobar con OCR
print("\n--- Verificación visual del rect de R21 (rotación) ---")
import fitz, io
from PIL import Image
from utils.config import Config
cfg = Config()
cfg.apply_tessdata()
import pytesseract
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path

for r in idx2.results:
    if r.designator.upper() == "R21" and r.rects:
        doc = fitz.open(r.file_path)
        page = doc[r.page - 1]
        rect = r.rects[0]
        zoom = 6.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        x0 = max(0, int(rect[0] * zoom) - 120)
        y0 = max(0, int(rect[1] * zoom) - 90)
        x1 = min(img.width, int(rect[2] * zoom) + 120)
        y1 = min(img.height, int(rect[3] * zoom) + 90)
        crop = img.crop((x0, y0, x1, y1))
        txt = pytesseract.image_to_string(crop, lang="eng").strip().replace("\n", " | ")
        print(f"  {os.path.basename(r.file_path)} -> OCR del recorte: {txt!r}")
        doc.close()
