# -*- coding: utf-8 -*-
"""Prueba con los esquemáticos reales del Ampeg B2R."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_index import SearchIndex
from utils.file_loader import FileLoader

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "schematics", "Ampeg_B2R")
if not os.path.isdir(folder):
    print("No existe la carpeta", folder)
    sys.exit(0)

t0 = time.time()
idx = SearchIndex()
loader = FileLoader(idx, device="Ampeg B2R")
loader.load_path(folder)
print(f"Indexado en {time.time()-t0:.1f}s — componentes: {len(idx.results)}")

from collections import Counter
c = Counter(r.designator[0] for r in idx.results)
print("Por prefijo:", dict(c.most_common(12)))

print("\n--- Búsqueda 'R46' ---")
for r in idx.search("R46"):
    print(f"  {r.designator} = {r.value!r} ({r.component_type}) "
          f"pág {r.page} — {os.path.basename(r.file_path)}")

print("\n--- Componentes con valor detectado (muestra) ---")
con_valor = [r for r in idx.results if r.value]
print(f"{len(con_valor)} de {len(idx.results)} tienen valor")
for r in con_valor[:15]:
    print(f"  {r.designator:<7} = {r.value:<10} {r.component_type}")
