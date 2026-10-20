#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
from typing import List
from .search_index import ComponentResult
from .nomenclature import get_component_type

class AltiumParser:
    def __init__(self):
        # Archivos .SchDoc son binarios o ASCII dependiendo; a veces texto
        self.ref_re = re.compile(r'Reference\s+([A-Z]{1,4}\d+[A-Z0-9]*)', re.IGNORECASE)
        self.val_re = re.compile(r'Value\s+([^\r\n]+)', re.IGNORECASE)
    
    def parse(self, filepath: str, index) -> List[ComponentResult]:
        results = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore', buffering=8192) as f:
                content = f.read()
            # Buscar referencias
            for m in self.ref_re.finditer(content):
                des = m.group(1).strip()
                des_up = des.upper()
                # Buscar valor cerca
                val_search_start = m.end()
                val_match = self.val_re.search(content[val_search_start:val_search_start+100])
                value = val_match.group(1).strip() if val_match else ''
                comp_type = get_component_type(des)
                result = ComponentResult(
                    designator=des_up,
                    value=value,
                    component_type=comp_type,
                    file_path=filepath,
                    page=1,
                    location="Altium",
                    connections=[],
                    source_type='altium'
                )
                results.append(result)
        except Exception as e:
            # Puede ser binario, lo intentamos leer parcialmente
            try:
                with open(filepath, 'rb') as f:
                    data = f.read(1024*1024)  # 1MB
                text = data.decode('latin-1', errors='ignore')
                for m in self.ref_re.finditer(text):
                    des = m.group(1).strip()
                    des_up = des.upper()
                    comp_type = get_component_type(des)
                    result = ComponentResult(
                        designator=des_up,
                        value='',
                        component_type=comp_type,
                        file_path=filepath,
                        page=1,
                        location="Altium",
                        connections=[],
                        source_type='altium'
                    )
                    results.append(result)
            except:
                pass
        return results