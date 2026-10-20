# -*- coding: utf-8 -*-
"""Renderiza la zona de R21 para ver si el resaltado cae en texto real."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitz, io
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(BASE, "schematics", "Ampeg_B2R")

cases = [
    ("descarga (5).pdf", 1, (87.9559097290039, 691.0558471679688, 95.62997436523438, 701.2800903320312)),
    ("descarga (6).pdf", 1, (568.75, 110.5, 575.5, 113.75)),
]

for fname, pageno, rect in cases:
    path = os.path.join(FOLDER, fname)
    doc = fitz.open(path)
    page = doc[pageno - 1]
    print(f"\n=== {fname} pag {pageno} ===")
    print("page.rect:", page.rect)
    print("rotation:", page.rotation)
    words = page.get_text("words")
    print("palabras:", len(words))
    # palabras cerca del rect
    cx = (rect[0] + rect[2]) / 2
    cy = (rect[1] + rect[3]) / 2
    near = []
    for w in words:
        wx = (w[0] + w[2]) / 2
        wy = (w[1] + w[3]) / 2
        if abs(wx - cx) < 40 and abs(wy - cy) < 20:
            near.append((round(w[0],1), round(w[1],1), round(w[2],1), round(w[3],1), w[4]))
    print("texto cerca:", near)

    # render a zoom 6 y recortar alrededor
    zoom = 6.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    x0 = max(0, int(rect[0] * zoom) - 160)
    y0 = max(0, int(rect[1] * zoom) - 120)
    x1 = min(img.width, int(rect[2] * zoom) + 160)
    y1 = min(img.height, int(rect[3] * zoom) + 120)
    crop = img.crop((x0, y0, x1, y1))
    out = os.path.join(BASE, "tests", f"_r21_{fname.split()[0].strip('().')}_{pageno}.png")
    crop.save(out)
    print("crop:", out, crop.size)
    doc.close()
