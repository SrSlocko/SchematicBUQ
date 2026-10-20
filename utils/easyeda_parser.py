#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import os
from typing import List
from .search_index import ComponentResult
from .nomenclature import get_component_type

class EasyEDAParser:
    def __init__(self):
        pass
    
    def parse(self, filepath: str, index) -> List[ComponentResult]:
        results = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            # EasyEDA json tiene estructura con 'symbols', 'devices' etc.
            # Intentar buscar designators
            def search_obj(obj):
                if isinstance(obj, dict):
                    # Buscar campos comunes
                    ref = obj.get('reference') or obj.get('ref') or obj.get('designator') or obj.get('Reference')
                    val = obj.get('value') or obj.get('Value') or obj.get('name')
                    if ref and isinstance(ref, str):
                        # Extraer designador
                        m = re.match(r'([A-Z]{1,4}\d+[A-Z0-9]*)', ref.upper())
                        if m:
                            des_up = m.group(1)
                            comp_type = get_component_type(ref)
                            result = ComponentResult(
                                designator=des_up,
                                value=str(val).strip() if val else '',
                                component_type=comp_type,
                                file_path=filepath,
                                page=1,
                                location="EasyEDA",
                                connections=[],
                                source_type='easyeda'
                            )
                            results.append(result)
                    for v in obj.values():
                        search_obj(v)
                elif isinstance(obj, list):
                    for item in obj:
                        search_obj(item)
            search_obj(data)
        except Exception as e:
            print(f"Error parseando EasyEDA {filepath}: {e}")
        
        return results