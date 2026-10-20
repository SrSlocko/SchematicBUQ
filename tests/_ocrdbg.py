# -*- coding: utf-8 -*-
"""Diagnóstico de OCR: qué saca de descarga (2).pdf y por qué sólo 1 componente."""
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
from utils.ocr import ocr_words, DEFAULT_CONF, OCR_ZOOM
from utils.designators import is_designator

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs
print("Tesseract:", cfg.tesseract_path, "| idioma:", LANG)

PDF = sys.argv[1] if len(sys.argv) > 1 else \
    r"D:\schematicbuq\schematics\Ampeg_B2R\descarga (2).pdf"

doc = fitz.open(PDF)
pg = doc[0]
print("\nPDF:", PDF, "| rect", pg.rect, "| rot", pg.rotation)

for zoom in (4, 6, 8):
    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    for psm in (11, 6, 12, 3):
        d = pytesseract.image_to_data(img, lang=LANG, config=f"--psm {psm}",
                                      output_type=pytesseract.Output.DICT)
        words = []
        des = []
        for i in range(len(d['text'])):
            t = (d['text'][i] or '').strip()
            if not t:
                continue
            try:
                c = float(d['conf'][i])
            except Exception:
                c = -1
            if c < 20:
                continue
            words.append(t)
            if is_designator(t):
                des.append(t.upper())
        print(f"zoom={zoom} psm={psm}: {len(words)} palabras, "
              f"{len(des)} designadores -> {sorted(set(des))}")
doc.close()
