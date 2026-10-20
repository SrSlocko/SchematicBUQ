# -*- coding: utf-8 -*-
"""Experimento: qué preprocesado + zoom + PSM da más designadores válidos."""
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


def prep(img, modo):
    if modo == "orig":
        return img
    g = ImageOps.grayscale(img)
    if modo == "gray":
        return g
    if modo == "otsu":
        return g.point(lambda p: 255 if p > 128 else 0)
    if modo == "auto+otsu":
        a = ImageOps.autocontrast(g)
        return a.point(lambda p: 255 if p > 128 else 0)
    if modo == "dilate":
        a = ImageOps.autocontrast(g).point(lambda p: 255 if p > 128 else 0)
        return a.filter(ImageFilter.MinFilter(3))
    return g


def scan(img, psms, conf=45):
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


print(f"{'zoom':>4} {'modo':<11} {'psms':<9} {'tiempo':>6}  designadores")
print("-" * 78)
for zoom in (4, 6, 8):
    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    base = Image.open(io.BytesIO(pix.tobytes("png")))
    for modo in ("orig", "gray", "otsu", "auto+otsu", "dilate"):
        img = prep(base, modo)
        t0 = time.time()
        des = scan(img, (11, 6))
        dt = time.time() - t0
        print(f"{zoom:>4} {modo:<11} {'11+6':<9} {dt:>5.1f}s  "
              f"{len(des):>2} -> {sorted(des)}")
doc.close()
