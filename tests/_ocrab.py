# -*- coding: utf-8 -*-
"""¿Qué cambia respecto al OCR anterior? (preprocesado / PSM / expand)"""
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
from utils.ocr import ocr_words, prep_image, expand_designators, count_designators
from utils.designators import is_designator

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs

d = r"D:\schematicbuq\schematics\Ampeg_B2R"
files = ["descarga (5).pdf", "descarga (3).pdf", "descarga (6).pdf"]

for f in files:
    doc = fitz.open(os.path.join(d, f))
    pg = doc[0]
    pix = pg.get_pixmap(matrix=fitz.Matrix(4, 4))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    print(f"\n=== {f}  (rect {pg.rect.width:.0f}x{pg.rect.height:.0f} rot {pg.rotation}) ===")

    variants = [
        ("ANTES: sin prep, PSM 11+6", False, (11, 6), False),
        ("prep + PSM 11+6",            True,  (11, 6), False),
        ("prep + PSM 11+6+3",          True,  (11, 6, 3), False),
        ("sin prep + PSM 11+6+3",      False, (11, 6, 3), False),
        ("sin prep + PSM 11+6+3+expand", False, (11, 6, 3), True),
    ]
    for label, prep, psms, exp in variants:
        t0 = time.time()
        words = ocr_words(pytesseract, img, lang=LANG, psms=psms, prep=prep)
        if exp:
            words = expand_designators(words)
        n = count_designators(words)
        print(f"  {label:<34} -> {n:>3} des  ({time.time()-t0:.1f}s)")
    doc.close()
