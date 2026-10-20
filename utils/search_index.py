#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any

@dataclass
class ComponentResult:
    designator: str
    value: str
    component_type: str
    file_path: str
    page: int
    location: str          # descripción aproximada
    connections: List[str] = field(default_factory=list)  # nets/pines
    source_type: str = ""  # pdf, image, netlist, kicad, easyeda, altium
    rects: List[List[float]] = field(default_factory=list)  # bbox por página [(x0,y0,x1,y1)]
    device: str = ""       # aparato/equipo al que pertenece

    def to_dict(self):
        return asdict(self)


class SearchIndex:
    def __init__(self):
        self.results = []          # lista de ComponentResult
        self.connections = {}      # {net_name: [designadores]}
        self.device_of_file = {}   # {file_path: device_name}

    def add_result(self, result: ComponentResult):
        # Evitar duplicados exactos (mismo designador, archivo, página y valor)
        for r in self.results:
            if (r.designator == result.designator and r.file_path == result.file_path
                    and r.page == result.page and r.value == result.value
                    and r.source_type == result.source_type):
                if result.rects and not r.rects:
                    r.rects = result.rects
                return
        self.results.append(result)

    def register_connection(self, net: str, designator: str):
        if not net:
            return
        self.connections.setdefault(net, [])
        if designator not in self.connections[net]:
            self.connections[net].append(designator)

    def register_file_device(self, file_path: str, device: str):
        if device:
            self.device_of_file[file_path] = device

    def get_device(self, file_path: str) -> str:
        return self.device_of_file.get(file_path, "")

    def clear(self):
        self.results.clear()
        self.connections.clear()
        self.device_of_file.clear()

    def search(self, query: str) -> List[ComponentResult]:
        if not query:
            return list(self.results)

        query = query.strip().upper()
        exact = []
        partial = []
        by_value = []

        for r in self.results:
            des_up = r.designator.upper()
            if des_up == query:
                exact.append(r)
            elif query in des_up:
                partial.append(r)
            elif query and query.lower() in (r.value or '').lower():
                by_value.append(r)

        return exact + partial + by_value

    def connected_components(self, designator: str) -> List[str]:
        """Devuelve designadores conectados al dado, siguiendo las nets."""
        designator = designator.upper()
        nets = set()
        for net, members in self.connections.items():
            if designator in [m.upper() for m in members]:
                nets.add(net)
        connected = set()
        for net in nets:
            for m in self.connections.get(net, []):
                if m.upper() != designator:
                    connected.add(m.upper())
        return sorted(connected)

    def nets_of(self, designator: str) -> List[str]:
        designator = designator.upper()
        return sorted([net for net, members in self.connections.items()
                       if designator in [m.upper() for m in members]])

    def devices(self) -> List[str]:
        return sorted(set(d for d in self.device_of_file.values() if d))

    def export_json(self, filepath: str):
        """Guarda índice completo (componentes + nets + aparato por archivo)."""
        data = {
            "results": [r.to_dict() for r in self.results],
            "connections": self.connections,
            "device_of_file": self.device_of_file,
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_json(self, filepath: str):
        """Carga un índice exportado (acepta también el formato antiguo: lista)."""
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):          # formato antiguo: solo componentes
            self.results = [ComponentResult(**d) for d in data]
            self.connections = {}
            self.device_of_file = {}
            return
        self.results = [ComponentResult(**d) for d in data.get("results", [])]
        self.connections = data.get("connections", {}) or {}
        self.device_of_file = data.get("device_of_file", {}) or {}