# -*- coding: utf-8 -*-
"""Prueba de comportamiento del programa: indexa y busca componentes al azar."""
import os, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from utils.search_index import SearchIndex
from utils.file_loader import FileLoader

FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schematics")

t0 = time.time()
idx = SearchIndex()
loader = FileLoader(idx, device="")
loader.load_path(FOLDER)
print(f"[INDEXADO] {time.time()-t0:.1f}s, {len(idx.results)} componentes, "
      f"{len(idx.connections)} nets")

# Guardar para reuso
import json
with open("_idx_dump.json", "w", encoding="utf-8") as f:
    json.dump([r.to_dict() for r in idx.results], f, ensure_ascii=False)

from collections import Counter
c = Counter(r.designator[0] for r in idx.results)
print("[PREFIJOS]", dict(c.most_common(15)))

sin_valor = [r for r in idx.results if not r.value]
print(f"[VALORES] {len(idx.results)-len(sin_valor)}/{len(idx.results)} con valor")

# --- Búsquedas al azar ---
print("\n===== BÚSQUEDAS AL AZAR =====")
designadores = sorted(set(r.designator for r in idx.results))
muestra = random.sample(designadores, min(15, len(designadores)))
for d in muestra:
    res = idx.search(d)
    r = res[0]
    print(f"  {d:<6} -> {r.value:<10} {r.component_type:<24} "
          f"pág {r.page} ({os.path.basename(r.file_path)})")
