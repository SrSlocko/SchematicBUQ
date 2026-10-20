# -*- coding: utf-8 -*-
"""Busca la mejor combinación (zoom x prep x tiles) en las hojas grandes."""
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
from utils.ocr import ocr_words, expand_designators, count_designators, tile_image

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs

d = r"D:\schematicbuq\schematics\Ampeg_B2R"


def run(img, prep, tiles):
    if not tiles:
        return count_designators(expand_designators(
            ocr_words(pytesseract, img, lang=LANG, psms=(11, 6), prep=prep)))
    des = set()
    for part, dx, dy in tile_image(img, 3, 3):
        w = expand_designators(ocr_words(pytesseract, part, lang=LANG,
                                         psms=(11, 6), prep=prep, offset=(dx, dy)))
        des |= {x['text'].strip().upper() for x in w
                if expand_designators([x])}
    # recuento correcto
    total = set()
    for part, dx, dy in []:
        pass
    return len(des)


for fn, pageno in [("descarga (5).pdf", 0), ("descarga (3).pdf", 0), ("descarga (2).pdf", 0)]:
    doc = fitz.open(os.path.join(d, fn))
    pg = doc[pageno]
    print(f"\n=== {fn} (rect {pg.rect.width:.0f}x{pg.rect.height:.0f} rot {pg.rotation}) ===")
    print(f"{'zoom':>4} {'prep':>6} {'tiles':>6} {'tiempo':>7}  des")
    for zoom in (4, 6):
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        for prep in (False, True):
            for tiles in (False, True):
                t0 = time.time()
                if tiles:
                    des = set()
                    for part, dx, dy in tile_image(img, 3, 3):
                        w = expand_designators(ocr_words(
                            pytesseract, part, lang=LANG, psms=(11, 6),
                            prep=prep, offset=(dx, dy)))
                        des |= {x['text'].strip().upper() for x in w}
                    n = len(des)
                else:
                    n = run(img, prep, False)
                print(f"{zoom:>4} {str(prep):>6} {str(tiles):>6} {time.time()-t0:>6.1f}s  {n}")
    doc.close()
