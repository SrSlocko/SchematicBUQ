# -*- coding: utf-8 -*-
"""Diagnóstico: indexa Ampeg, guarda cache JSON y muestra R21 + posibles falsos positivos."""
import os, sys, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_index import SearchIndex
from utils.file_loader import FileLoader

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(BASE, "schematics", "Ampeg_B2R")

t0 = time.time()
idx = SearchIndex()
loader = FileLoader(idx, device="Ampeg_B2R")
loader.load_path(FOLDER)
print(f"[INDEXADO] {time.time()-t0:.1f}s  componentes={len(idx.results)}")

out = os.path.join(BASE, "tests", "_cache_ampeg.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump([r.to_dict() for r in idx.results], f, ensure_ascii=False)
print("[CACHE]", out)

print("\n===== R21 =====")
for r in idx.results:
    if r.designator.upper() == "R21":
        print(os.path.basename(r.file_path), "pag", r.page,
              "valor=", repr(r.value), "rects=", r.rects,
              "origen=", r.source_type)

print("\n===== TODOS LOS DESIGNADORES =====")
des = {}
for r in idx.results:
    des.setdefault(r.designator.upper(), []).append(r)
print("únicos:", len(des))
print(sorted(des))

print("\n===== POSIBLES FALSOS POSITIVOS (patrones raros) =====")
# prefijos de 1 letra seguidos de números muy altos, o sufijos raros
for d in sorted(des):
    m = re.match(r'^([A-Z]+)(\d+)([A-D]?)$', d)
    if not m:
        print("  formato raro:", d)
        continue
    prefix, num, suf = m.group(1), int(m.group(2)), m.group(3)
    if len(prefix) == 1 and prefix in "AEH" and num > 50:
        print("  num alto en prefijo raro:", d)
    if prefix in ("S", "T", "E") and num > 200:
        print("  posible ruido:", d)
