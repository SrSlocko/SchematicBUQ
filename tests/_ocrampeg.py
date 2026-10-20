# -*- coding: utf-8 -*-
"""Prueba: cuántos componentes reconoce el parser en cada PDF de Ampeg."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from utils.pdf_parser import PDFParser
from utils.search_index import SearchIndex
from utils.cleanup import filter_false_positives
from utils.config import Config

d = r"D:\schematicbuq\schematics\Ampeg_B2R"
cfg = Config()
print("OCR disponible:", cfg.ocr_available(), "| langs:", cfg.ocr_langs)

parser = PDFParser(use_ocr=True)
index = SearchIndex()

files = sorted(f for f in os.listdir(d) if f.endswith(".pdf"))
grand = 0
for f in files:
    t0 = time.time()
    res = parser.parse(os.path.join(d, f), index)
    des = sorted({r.designator for r in res})
    antes = len(des)
    # limpieza de falsos positivos (solo PDF/imagen)
    res2 = filter_false_positives(res)
    des2 = sorted({r.designator for r in res2})
    grand += len(des2)
    print(f"\n--- {f}  ({time.time()-t0:.1f}s)")
    print(f"    {antes} designadores -> {len(des2)} tras limpiar")
    print(f"    {des2}")
print(f"\nTOTAL final: {grand} designadores")
