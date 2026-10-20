# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
d = json.load(open('data/nomenclature_es.json', encoding='utf-8'))
print('JSON valido. Designadores en BD:', len(d['designators']))

from utils.nomenclature import get_component_type
print("\n-- get_component_type --")
for t in ['R46', 'RN1', 'RP2', 'IC3', 'C12', 'U5', 'J7', 'BR1', 'LED2',
          'H1', 'T47', 'Y1', 'F1', 'Q3', 'D1', 'ZD1', 'SP1', 'M1']:
    print(f"  {t:<6} -> {get_component_type(t)}")

from database.nomenclature_db import NomenclatureDB
db = NomenclatureDB()
print("\n-- ficha de conocimiento --")
for t in ['R46', 'RN1', 'BR1', 'H1', 'SP1', 'M1', 'TH1', 'F1', 'Y1', 'X1']:
    info = db.get_info(t)
    print(f"  {t:<6} -> {info.get('name', '(sin info)')}")
