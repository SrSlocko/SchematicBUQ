# -*- coding: utf-8 -*-
"""Pasada 1 (sin prep, PSM 11+6) por archivo + comprobación de determinismo."""
import os, sys, io, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import fitz
from PIL import Image
import pytesseract
from utils.config import Config
from utils.ocr import ocr_words, expand_designators, count_designators, TARGET_WIDTH

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs

d = r"D:\schematicbuq\schematics\Ampeg_B2R"
files = sorted(f for f in os.listdir(d) if f.endswith(".pdf"))

print("=== Pasada 1: sin preprocesado, PSM 11+6 (lo rápido y fiable) ===")
for f in files:
    doc = fitz.open(os.path.join(d, f))
    total = 0
    for pg in doc:
        zoom = max(4.0, TARGET_WIDTH / max(1.0, pg.rect.width))
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w = expand_designators(
            ocr_words(pytesseract, img, lang=LANG, psms=(11, 6), prep=False))
        total += count_designators(w)
    print(f"  {f:<22} -> {total:>3} designadores")
    doc.close()

print("\n=== Determinismo (misma config 3 veces) ===")
doc = fitz.open(os.path.join(d, "descarga (5).pdf"))
pg = doc[0]
zoom = max(4.0, TARGET_WIDTH / max(1.0, pg.rect.width))
pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
img = Image.open(io.BytesIO(pix.tobytes("png")))
for i in range(3):
    w = expand_designators(
        ocr_words(pytesseract, img, lang=LANG, psms=(11, 6), prep=False))
    print(f"  intento {i+1}: {count_designators(w)} designadores")
doc.close()
