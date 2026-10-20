#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from typing import List
from .search_index import ComponentResult
from .nomenclature import get_component_type


class NetlistParser:
    def __init__(self):
        # SPICE: R1 N001 N002 10k
        self.spice_re = re.compile(r'^\s*([A-Za-z]{1,4}\d+[A-Za-z0-9]*)\b', re.MULTILINE)
        # KiCad netlist: (comp (ref R1) (value 10k) ...)
        self.kicad_comp_re = re.compile(
            r'\(comp\s*\(ref\s+"?([A-Za-z]{1,4}\d+[A-Za-z0-9]*)"?\)'
            r'(?:.*?\(value\s+"?([^"\)]*)"?\))?',
            re.IGNORECASE | re.DOTALL)
        # KiCad nets: (net (code 1) (name "GND") (node (ref R1) (pin 1)) ...)
        self.kicad_net_re = re.compile(
            r'\(net\s*\(code\s+\d+\)\s*\(name\s+"?([^"\)]+)"?\)(.*?)(?=\(net\s|\Z)',
            re.IGNORECASE | re.DOTALL)
        self.kicad_node_re = re.compile(r'\(node\s*\(ref\s+"?([A-Za-z0-9_]+)"?\)', re.IGNORECASE)

    def parse(self, filepath: str, index=None) -> List[ComponentResult]:
        results = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error leyendo netlist {filepath}: {e}")
            return results

        is_kicad = '(comp' in content or '(net ' in content

        if is_kicad:
            # Componentes con valor
            for des, val in self.kicad_comp_re.findall(content):
                des_up = des.strip().upper()
                if not re.match(r'^[A-Z]{1,4}\d', des_up):
                    continue
                results.append(ComponentResult(
                    designator=des_up,
                    value=(val or '').strip(),
                    component_type=get_component_type(des_up),
                    file_path=filepath, page=1, location="Netlist KiCad",
                    connections=[], source_type='netlist',
                ))
            # Conexiones
            if index is not None:
                for net_name, block in self.kicad_net_re.findall(content):
                    for ref in self.kicad_node_re.findall(block):
                        index.register_connection(net_name.strip().upper(), ref.strip().upper())
            return results

        # Formato SPICE (.cir/.net)
        for match in self.spice_re.finditer(content):
            des = match.group(1).strip().upper()
            if not re.match(r'^[A-Z]{1,4}\d', des):
                continue
            line_end = content.find('\n', match.start())
            if line_end == -1:
                line_end = len(content)
            line = content[match.start():line_end].strip()
            parts = line.split()
            if len(parts) < 3:
                continue
            nodes = parts[1:-1]
            value = parts[-1]
            if index is not None:
                for node in nodes:
                    index.register_connection(node.strip().upper(), des)
            results.append(ComponentResult(
                designator=des,
                value=value,
                component_type=get_component_type(des),
                file_path=filepath, page=1, location="Netlist SPICE",
                connections=nodes, source_type='netlist',
            ))
        return results