#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prueba sin GUI del motor de interacción (utils.interaction)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_index import SearchIndex, ComponentResult
from utils import interaction as I

idx = SearchIndex()
def add(des, val, typ, page, rect):
    idx.add_result(ComponentResult(designator=des, value=val, component_type=typ,
                                   file_path=r"D:\x\sch.pdf", page=page,
                                   location="", source_type="pdf", rects=[rect]))
# R46 en el centro, vecinos alrededor (misma fila => señal)
add("R46", "10k", "Resistencia", 1, [100, 100, 130, 110])
add("C10", "15k..", "Condensador", 1, [140, 100, 160, 110])
add("Q2", "", "Transistor", 1, [170, 100, 200, 115])
add("R47", "4k7", "Resistencia", 1, [140, 140, 170, 150])
add("LEJOS", "1k", "Resistencia", 1, [900, 900, 930, 910])

info = I.build(idx, "R46", value="10k", type_name="Resistencia",
               file_path=r"D:\x\sch.pdf", page=1)
print("kind:", info["kind"], "|", info["kind_name"], "| real_nets:", info["real_nets"])
print("vecinos:", [n["designator"] for n in info["neighbors"]])
print("rol:", info["role"][:60], "...")
print("subcircuitos:", [t for t, _ in info["subcircuits"]])
print("impacto:", len(info["impact"]), "escenarios")
print("relacion R46<->C10:", I.relation_text("resistor", "capacitor"))
print("relacion R46<->Q2 :", I.relation_text("resistor", "transistor"))

# Netlist real
idx2 = SearchIndex()
for d, v, t in [("R1", "10k", "Resistencia"), ("R2", "10k", "Resistencia"),
                ("C1", "100n", "Condensador"), ("U1", "", "Circuito integrado")]:
    idx2.add_result(ComponentResult(designator=d, value=v, component_type=t,
                                    file_path="proj.kicad_sch", page=1,
                                    location="", source_type="kicad"))
idx2.register_connection("VCC", "R1"); idx2.register_connection("VCC", "R2")
idx2.register_connection("NET_A", "R1"); idx2.register_connection("NET_A", "C1")
idx2.register_connection("NET_A", "U1")
info2 = I.build(idx2, "R1", value="10k", type_name="Resistencia",
                file_path="proj.kicad_sch", page=1)
print("--- netlist ---")
print("real_nets:", info2["real_nets"])
print("vecinos:", [(n["designator"], n["net"]) for n in info2["neighbors"]])
print("subcircuitos:", [t for t, _ in info2["subcircuits"]])
print("TODO OK")
