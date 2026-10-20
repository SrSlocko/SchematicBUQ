# -*- coding: utf-8 -*-
"""¿Mejora al indicar el DPI real a Tesseract?"""
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
from utils.ocr import expand_designators, count_designators
from utils.designators import is_designator

cfg = Config()
pytesseract.pytesseract.tesseract_cmd = cfg.tesseract_path
cfg.apply_tessdata()
LANG = cfg.ocr_langs

d = r"D:\schematicbuq\schematics\Ampeg_B2R"


def scan(img, psms=(11, 6), config=""):
    des = set()
    for psm in psms:
        c = f"--psm {psm} {config}".strip()
        try:
            data = pytesseract.image_to_data(img, lang=LANG, config=c,
                                             output_type=pytesseract.Output.DICT)
        except Exception as e:
            print("   ERR", e)
            continue
        for i in range(len(data['text'])):
            t = (data['text'][i] or '').strip()
            if not t:
                continue
            try:
                conf = float(data['conf'][i])
            except Exception:
                conf = -1
            if conf < 45:
                continue
            if is_designator(t):
                des.add(t.upper())
            else:
                for p in expand_designators([{'text': t}]):
                    if is_designator(p['text']):
                        des.add(p['text'].upper())
    return des


for fn, pno in [("descarga (2).pdf", 0), ("descarga (3).pdf", 0), ("descarga (5).pdf", 0)]:
    doc = fitz.open(os.path.join(d, fn))
    pg = doc[pno]
    print(f"\n=== {fn} ===")
    for zoom in (4, 6, 8):
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        dpi = int(72 * zoom)
        t0 = time.time()
        a = scan(img, config="")
        b = scan(img, config=f"--dpi {dpi}")
        img.info['dpi'] = (dpi, dpi)
        c = scan(img, config="")
        print(f"  zoom={zoom} dpi={dpi}: sin dpi={len(a):>3} | --dpi={len(b):>3} "
              f"| info.dpi={len(c):>3}  ({time.time()-t0:.1f}s)")
    doc.close()
