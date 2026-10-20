# -*- coding: utf-8 -*-
"""Optimización OCR: qué combinación da MÁS designadores en MENOS tiempo."""
import os, sys, io, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import fitz
from PIL import Image, ImageStat
import pytesseract
from utils.config import Config
from utils.ocr import expand_designators, tile_image
from utils.designators import is_designator

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs
D = r"D:\schematicbuq\schematics\Ampeg_B2R"


def ocr(img, psms, conf=45, extra=""):
    des = set()
    words = []
    for psm in psms:
        c = f"--psm {psm} {extra}".strip()
        try:
            data = pytesseract.image_to_data(img, lang=LANG, config=c,
                                             output_type=pytesseract.Output.DICT)
        except Exception:
            continue
        for i in range(len(data['text'])):
            t = (data['text'][i] or '').strip()
            if not t:
                continue
            try:
                cf = float(data['conf'][i])
            except Exception:
                cf = -1
            if cf < conf:
                continue
            words.append({'text': t, 'x0': data['left'][i], 'y0': data['top'][i],
                          'x1': data['left'][i] + data['width'][i],
                          'y1': data['top'][i] + data['height'][i], 'conf': cf})
    for w in expand_designators(words):
        if is_designator(w['text']):
            des.add(w['text'].strip().upper())
    return des


def ink_ratio(img):
    """Fracción de píxeles 'con tinta' (no fondo)."""
    g = img.convert("L")
    st = ImageStat.Stat(g)
    return st.mean[0] / 255.0


def run_tiles(img, cols, rows, psms, extra="", skip_empty=True):
    des = set()
    n_used = 0
    for part, dx, dy in tile_image(img, cols, rows):
        if skip_empty:
            g = part.convert("L")
            hist = g.histogram()
            dark = sum(hist[:200])
            total = part.size[0] * part.size[1]
            if total and dark / total < 0.004:      # recuadro casi vacío
                continue
        n_used += 1
        des |= ocr(part, psms, extra=extra)
    return des, n_used


for fn in ("descarga (3).pdf", "descarga (2).pdf"):
    doc = fitz.open(os.path.join(D, fn))
    pg = doc[0]
    pw = max(1.0, pg.rect.width)
    zoom = min(8.0, max(4.0, 6500.0 / pw))
    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    base = Image.open(io.BytesIO(pix.tobytes("png")))
    print(f"\n=== {fn}  ({base.size[0]}x{base.size[1]} px, zoom {zoom:.2f}) ===")

    tests = [
        ("pág. completa (11,6)          ", lambda: (ocr(base, (11, 6)), 1)),
        ("pág. completa (11)            ", lambda: (ocr(base, (11,)), 1)),
        ("tiles 3x3 (11,6)              ", lambda: run_tiles(base, 3, 3, (11, 6))),
        ("tiles 3x3 (11)                ", lambda: run_tiles(base, 3, 3, (11,))),
        ("tiles 2x2 (11,6)              ", lambda: run_tiles(base, 2, 2, (11, 6))),
        ("tiles 2x2 (11)                ", lambda: run_tiles(base, 2, 2, (11,))),
        ("tiles 4x3 (11)                ", lambda: run_tiles(base, 4, 3, (11,))),
        ("tiles 3x3 (11) --oem 1        ", lambda: run_tiles(base, 3, 3, (11,), " --oem 1")),
        ("tiles 2x2 (11) --oem 1        ", lambda: run_tiles(base, 2, 2, (11,), " --oem 1")),
    ]
    best = set()
    for label, fnc in tests:
        t0 = time.time()
        des, n = fnc()
        dt = time.time() - t0
        if len(des) > len(best):
            best = des
        print(f"   {label} {dt:6.1f}s  {len(des):>3} des  (recuadros usados: {n})")
    # recall de la página completa + el mejor tiling
    print(f"   -> referencia (unión de todo): {len(best)}")
    doc.close()
