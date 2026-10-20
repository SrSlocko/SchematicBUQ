# -*- coding: utf-8 -*-
"""Compara designadores de la pasada completa vs tiling y muestra el solapamiento."""
import os, sys, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import fitz
from PIL import Image
import pytesseract
from utils.config import Config
from utils.ocr import ocr_words, expand_designators, tile_image
from utils.designators import is_designator

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs

d = r"D:\schematicbuq\schematics\Ampeg_B2R"
fn = sys.argv[1] if len(sys.argv) > 1 else "descarga (3).pdf"
Zoom = 6

doc = fitz.open(os.path.join(d, fn))
pg = doc[0]
pix = pg.get_pixmap(matrix=fitz.Matrix(Zoom, Zoom))
img = Image.open(io.BytesIO(pix.tobytes("png")))

full = expand_designators(ocr_words(pytesseract, img, lang=LANG, psms=(11, 6), prep=False))
full_des = sorted({w['text'].strip().upper() for w in full if is_designator(w['text'])})

tiled = []
for part, dx, dy in tile_image(img, 3, 3):
    tiled += ocr_words(pytesseract, part, lang=LANG, psms=(11, 6), prep=False, offset=(dx, dy))
tiled = expand_designators(tiled)
tile_des = sorted({w['text'].strip().upper() for w in tiled if is_designator(w['text'])})

inter = sorted(set(full_des) & set(tile_des))
only_tile = sorted(set(tile_des) - set(full_des))

print(f"{fn}  zoom {Zoom}")
print(f"  completa: {len(full_des)}")
print(f"  tiling:   {len(tile_des)}")
print(f"  comunes:  {len(inter)}")
print(f"  solo tiling: {len(only_tile)}")
print("\n  --- comunes ---")
print("  ", inter)
print("\n  --- SOLO en tiling (primeros 120) ---")
print("  ", only_tile[:120])
doc.close()
