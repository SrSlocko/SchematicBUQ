# -*- coding: utf-8 -*-
"""2ª medición: ¿se pueden encontrar MÁS componentes sin perder velocidad?

Se comparan sólo variantes de recuadros (la pasada de página completa ya se
descartó porque no aportaba nada y costaba ~25 s).
"""
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


def ocr(img, psms, conf=45):
    des, words = set(), []
    for psm in psms:
        try:
            data = pytesseract.image_to_data(
                img, lang=LANG, config=f"--psm {psm}",
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


def tiles(img, cols, rows, overlap, psms):
    des, n, skipped = set(), 0, 0
    for part, dx, dy in tile_image(img, cols, rows, overlap=overlap):
        g = part.convert("L")
        hist = g.histogram()
        total = part.size[0] * part.size[1]
        if total and sum(hist[:200]) / total < 0.004:
            skipped += 1
            continue
        n += 1
        des |= ocr(part, psms)
    return des, n, skipped


CONFIGS = [
    ("3x3  sol.0.12 (11,6) [actual]", 3, 3, 0.12, (11, 6), 1.0),
    ("3x3  sol.0.25 (11,6)         ", 3, 3, 0.25, (11, 6), 1.0),
    ("2x2  sol.0.25 (11,6)         ", 2, 2, 0.25, (11, 6), 1.0),
    ("4x4  sol.0.12 (11,6)         ", 4, 4, 0.12, (11, 6), 1.0),
    ("3x3  sol.0.25 (11,6) +zoom   ", 3, 3, 0.25, (11, 6), 1.35),
]

for fn in ("descarga (3).pdf", "descarga (2).pdf"):
    doc = fitz.open(os.path.join(D, fn))
    pg = doc[0]
    pw = max(1.0, pg.rect.width)
    base_zoom = min(8.0, max(4.0, 6500.0 / pw))
    print(f"\n=== {fn} (zoom base {base_zoom:.2f}) ===")
    sets = {}
    for label, cols, rows, ov, psms, zf in CONFIGS:
        zoom = min(9.5, base_zoom * zf)
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        t0 = time.time()
        des, n, sk = tiles(img, cols, rows, ov, psms)
        dt = time.time() - t0
        sets[label] = des
        print(f"   {label} {dt:6.1f}s  {len(des):>3} des  "
              f"(recuadros {n}, saltados {sk}, zoom {zoom:.2f})")
    # Diferencias frente a la variante actual
    base = sets[CONFIGS[0][0]]
    for label, _, _, _, _, _ in CONFIGS[1:]:
        d = sets[label]
        extra = sorted(d - base)
        lost = sorted(base - d)
        print(f"   {label}: +{len(extra)} / -{len(lost)}  "
              f"nuevos={extra[:8]}  perdidos={lost[:8]}")
    doc.close()
