#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any

class NomenclatureDB:
    def __init__(self, db_path="data/nomenclature_es.json"):
        self.db_path = db_path
        self.data = {}
        self.load()
    
    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error cargando nomenclatura: {e}")
    
    def get_info(self, designator: str) -> Dict:
        if not designator:
            return {}
        import re
        des = designator.upper()
        designators = self.data.get('designators', {})
        # Prefijos ordenados de más largo a más corto (RN antes que R, IC antes que I)
        for prefix in sorted(designators.keys(), key=len, reverse=True):
            if des.startswith(prefix.upper()):
                return designators[prefix]
        # Intentar con las letras iniciales
        m = re.match(r'^([A-Z]+)', des)
        if m:
            return designators.get(m.group(1), {})
        return {}
    
    def get_all(self) -> Dict:
        return self.data