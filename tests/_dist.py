# -*- coding: utf-8 -*-
"""Distribución de designadores por archivo y prefijo (para filtrar outliers)."""
import os, sys, json, re
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(BASE, "tests", "_cache_ampeg.json"), encoding="utf-8"))

per = defaultdict(lambda: defaultdict(list))
for d in data:
    m = re.match(r'^([A-Z]+)(\d+)([A-D]?)$', d["designator"])
    f = os.path.basename(d["file_path"])
    if m:
        per[f][m.group(1)].append(int(m.group(2)))

for f in sorted(per):
    print("\n==", f)
    for p in sorted(per[f], key=lambda x: (-len(per[f][x]), x)):
        nums = sorted(per[f][p])
        mx = max(nums)
        print(f"   {p:<3} n={len(nums):<3} max={mx:<4} -> {nums}")
