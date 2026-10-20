# -*- coding: utf-8 -*-
"""Experimento 2: zooms altos, umbral bajo y tiling."""
import os, sys, io, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import fitz
from PIL import Image, ImageOps, ImageFilter
import pytesseract
from utils.config import Config
from utils.designators import is_designator

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs

PDF = r"D:\schematicbuq\schematics\Ampeg_B2R\descarga (2).pdf"
doc = fitz.open(PDF)
pg = doc[0]


def prep(img):
    g = ImageOps.grayscale(img)
    a = ImageOps.autocontrast(g).point(lambda p: 255 if p > 128 else 0)
    return a.filter(ImageFilter.MinFilter(3))


def scan(img, psms, conf):
    des = set()
    for psm in psms:
        try:
            d = pytesseract.image_to_data(img, lang=LANG, config=f"--psm {psm}",
                                          output_type=pytesseract.Output.DICT)
        except Exception:
            continue
        for i in range(len(d['text'])):
            t = (d['text'][i] or '').strip()
            if not t:
                continue
            try:
                c = float(d['conf'][i])
            except Exception:
                c = -1
            if c < conf:
                continue
            if is_designator(t):
                des.add(t.upper())
    return des


def tile(img, cols=3, rows=3, overlap=0.12):
    W, H = img.size
    out = []
    for r in range(rows):
        for c in range(cols):
            x0 = int(c * W / cols - (W / cols) * overlap if c else 0)
            y0 = int(r * H / rows - (H / rows) * overlap if r else 0)
            x1 = int((c + 1) * W / cols + (W / cols) * overlap)
            y1 = int((r + 1) * H / rows + (H / rows) * overlap)
            out.append(img.crop((max(0, x0), max(0, y0), min(W, x1), min(H, y1))))
    return out


# A) Zoom alto + umbral bajo, PSM combinados
print("=== A) Página completa, zoom alto, conf bajo ===")
for zoom in (8, 10, 12):
    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    base = Image.open(io.BytesIO(pix.tobytes("png")))
    img = prep(base)
    for conf in (45, 30, 20):
        t0 = time.time()
        des = scan(img, (11, 6, 3), conf)
        print(f"  zoom={zoom} conf={conf}: {len(des):>2} en {time.time()-t0:.1f}s")

# B) Tiling sobre zoom 8
print("\n=== B) Tiling (recuadros) sobre zoom 8 ===")
pix = pg.get_pixmap(matrix=fitz.Matrix(8, 8))
base = Image.open(io.BytesIO(pix.tobytes("png")))
for cols, rows in ((2, 2), (3, 3), (4, 4)):
    t0 = time.time()
    des = set()
    for part in tile(base, cols, rows):
        des |= scan(prep(part), (11, 6), 30)
    print(f"  tiles={cols}x{rows}: {len(des):>2} en {time.time()-t0:.1f}s")

# C) Combinación: zoom10 página + zoom8 tiles 3x3
print("\n=== C) Combinación final ===")
pix = pg.get_pixmap(matrix=fitz.Matrix(10, 10))
img10 = prep(Image.open(io.BytesIO(pix.tobytes("png"))))
des = scan(img10, (11, 6, 3), 30)
des2 = set()
for part in tile(base, 3, 3):
    des2 |= scan(prep(part), (11, 6), 30)
all_des = des | des2
print(f"  página sola: {len(des)}")
print(f"  tiles:       {len(des2)}")
print(f"  UNIÓN:       {len(all_des)} -> {sorted(all_des)}")
doc.close()
