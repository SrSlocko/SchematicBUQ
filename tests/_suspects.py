# -*- coding: utf-8 -*-
"""Inspecciona designadores sospechosos: contexto, valor, rects."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fitz

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(BASE, "tests", "_cache_ampeg.json"), encoding="utf-8"))

SUSPECTS = {"F074", "J112", "J176", "S176", "LD17", "T47", "R54B", "H1", "H2"}
for d in data:
    if d["designator"].upper() in SUSPECTS:
        print(f"\n{d['designator']}: valor={d['value']!r} pag={d['page']} "
              f"archivo={os.path.basename(d['file_path'])} rects={d['rects']}")
        # contexto de texto (si el PDF tiene capa de texto)
        try:
            doc = fitz.open(d["file_path"])
            page = doc[page0 := d["page"] - 1]
            words = page.get_text("words")
            if words and d["rects"]:
                r = d["rects"][0]
                cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
                near = [w[4] for w in words
                        if abs((w[0] + w[2]) / 2 - cx) < 45 and abs((w[1] + w[3]) / 2 - cy) < 22]
                print("   texto cerca:", near)
            elif not words:
                print("   (página escaneada, sin capa de texto)")
            doc.close()
        except Exception as e:
            print("   err:", e)
