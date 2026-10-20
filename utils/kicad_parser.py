#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
from typing import List
from .search_index import ComponentResult
from .nomenclature import get_component_type

class KiCadParser:
    def __init__(self):
        # Formato .kicad_sch: (symbol (lib_id ...) (at x y) (unit 1) (in_bom yes) (on_board yes)
        # designator suele estar como (property "Reference" "R46" ...)
        self.ref_re = re.compile(r'\(property\s+"Reference"\s+"?([A-Z]{1,4}\d+[A-Z0-9]*)"?', re.IGNORECASE)
        self.val_re = re.compile(r'\(property\s+"Value"\s+"?([^"]*)"?', re.IGNORECASE)
        self.foot_re = re.compile(r'\(property\s+"Footprint"\s+"?([^"]*)"?', re.IGNORECASE)
    
    def parse(self, filepath: str, index) -> List[ComponentResult]:
        results = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Cada símbolo puede tener varias propiedades
            # Buscar por referencias
            for m in self.ref_re.finditer(content):
                des = m.group(1).strip()
                des_up = des.upper()
                # Buscar valor cerca
                # buscar siguiente property Value tras esta referencia
                val_search_start = m.end()
                val_match = self.val_re.search(content[val_search_start:val_search_start+200])
                value = val_match.group(1).strip() if val_match else ''
                comp_type = get_component_type(des)
                result = ComponentResult(
                    designator=des_up,
                    value=value.strip().strip('"'),
                    component_type=comp_type,
                    file_path=filepath,
                    page=1,
                    location="KiCad Schematic",
                    connections=[],
                    source_type='kicad_sch'
                )
                results.append(result)
        except Exception as e:
            print(f"Error parseando KiCad {filepath}: {e}")
        
        return results