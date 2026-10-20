# -*- coding: utf-8 -*-
"""Reconstruye el índice del aparato Ampeg_B2R con el OCR nuevo y deja la
caché lista (para que la app abra al instante)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from utils.file_loader import FileLoader
from utils.search_index import SearchIndex
from utils.parse_cache import ParseCache
from utils.cleanup import filter_false_positives

D = r"D:\schematicbuq\schematics\Ampeg_B2R"
cache = ParseCache()
idx = SearchIndex()
loader = FileLoader(idx, device="Ampeg_B2R", use_ocr=True, cache=cache)
t0 = time.time()
total_raw = 0
for f in sorted(os.listdir(D)):
    p = os.path.join(D, f)
    if not os.path.isfile(p):
        continue
    t1 = time.time()
    n0 = len(idx.results)
    loader.load_path(p)
    raw = cache.get(p, True)
    if raw is not None:
        total_raw += len(raw)
    print(f"  {f}: {len(idx.results)-n0} componentes filtrados "
          f"(brutos {len(raw) if raw else 0}) en {time.time()-t1:.1f}s")
cache.save()
print(f"TOTAL filtrados={len(idx.results)}  brutos={total_raw}  "
      f"tiempo={time.time()-t0:.1f}s")

# Revisar designadores dudosos (los que más se repiten / raros)
from collections import Counter
c = Counter(r.designator for r in idx.results)
raros = [d for d in sorted(c) if len(d) > 6 or not d[0].isalpha()]
print("designadores raros:", raros[:40])
print("sin valor:", sum(1 for r in idx.results if not r.value))
print("FIN")
