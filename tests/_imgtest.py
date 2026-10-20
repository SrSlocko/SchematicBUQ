# -*- coding: utf-8 -*-
"""Prueba del OCR por recuadros en imágenes (sin tocar el índice real)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image, ImageDraw, ImageFont

tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_imgsch.png")
W, H = 3200, 2200
img = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("consola.ttf", 26)
except Exception:
    font = ImageFont.load_default()

labels = ["R10 10K", "C22 100uF", "D7 1N4002", "Q3 2N3904", "U5 TL072",
          "R141 4K7", "C305 22nF", "R58 1M", "D12 1N4148", "Q17 IRF540",
          "R200 220R", "C99 47uF"]
for i, t in enumerate(labels):
    x = 120 + (i % 4) * 780
    y = 140 + (i // 4) * 700
    dr.text((x, y), t, fill="black", font=font)
    dr.rectangle([x - 30, y - 40, x + 300, y + 500], outline="black", width=2)
img.save(tmp)

from utils.image_parser import ImageParser
from utils.search_index import SearchIndex
p = ImageParser(use_ocr=True)
print("OCR disponible:", p.ok)
idx = SearchIndex()
res = p.parse(tmp, idx)
print("componentes detectados:", len(res))
print(sorted(r.designator for r in res))
con_valor = [(r.designator, r.value) for r in res if r.value]
print("con valor:", con_valor)
os.remove(tmp)
print("FIN")
