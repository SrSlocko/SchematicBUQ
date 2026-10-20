# -*- coding: utf-8 -*-
"""Verificación final del OCR nuevo (una pasada, 3x3, solape 0.25, zoom<=10)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from utils.pdf_parser import PDFParser
from utils.search_index import SearchIndex
from utils import ocr as ocr_mod

D = r"D:\schematicbuq\schematics\Ampeg_B2R"
print(f"ajustes: {ocr_mod.TILE_COLS}x{ocr_mod.TILE_ROWS} solape {ocr_mod.TILE_OVERLAP} "
      f"zoom<= {ocr_mod.MAX_ZOOM} objetivo {ocr_mod.TARGET_WIDTH_TILED}")

p = PDFParser(use_ocr=True)
for fn in ("descarga (3).pdf", "descarga (2).pdf"):
    idx = SearchIndex()
    t0 = time.time()
    res = p.parse(os.path.join(D, fn), idx)
    dt = time.time() - t0
    des = sorted({r.designator for r in res})
    con_valor = sum(1 for r in res if r.value)
    print(f"  {fn}: {len(res)} componentes ({con_valor} con valor) en {dt:.1f}s")
    print(f"     muestra: {des[:12]}")
print("FIN")
