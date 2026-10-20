#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Mapeo de prefijos a tipo de componente
COMPONENT_TYPES = {
    'R': 'Resistencia',
    'RN': 'Red de resistencias',
    'RP': 'Red de resistencias',
    'RV': 'Resistencia variable',
    'RT': 'Resistencia ajustable',
    'C': 'Condensador/Capacitor',
    'CP': 'Condensador polarizado',
    'CX': 'Condensador X (línea)',
    'CY': 'Condensador Y (línea)',
    'TC': 'Condensador de tantalio',
    'L': 'Bobina/Inductor',
    'FB': 'Ferrita/Bead',
    'D': 'Diodo',
    'ZD': 'Diodo Zener',
    'CR': 'Puente/Rectificador',
    'BR': 'Puente rectificador',
    'DB': 'Puente rectificador',
    'TVS': 'Protección TVS',
    'LED': 'LED',
    'Q': 'Transistor',
    'TR': 'Transistor',
    'FET': 'Transistor MOSFET',
    'T': 'Transformador',
    'U': 'Circuito Integrado',
    'IC': 'Circuito Integrado',
    'A': 'Subconjunto/Ensamblaje',
    'J': 'Conector',
    'P': 'Conector/Terminal',
    'CN': 'Conector',
    'K': 'Relé',
    'S': 'Interruptor',
    'SW': 'Interruptor',
    'F': 'Fusible',
    'FU': 'Fusible',
    'BT': 'Batería',
    'BAT': 'Batería',
    'Y': 'Cristal/Oscilador',
    'X': 'Cristal/Oscilador',
    'XTAL': 'Cristal/Oscilador',
    'OSC': 'Oscilador',
    'M': 'Motor',
    'TH': 'Termistor',
    'NTC': 'Termistor NTC',
    'PTC': 'Termistor PTC',
    'PT': 'Potenciómetro',
    'VR': 'Potenciómetro/Varistor',
    'V': 'Varistor',
    'TP': 'Punto de prueba',
    'TEST': 'Punto de prueba',
    'H': 'Soporte/Agujero de montaje',
    'G': 'Generador/Tierra',
    'SP': 'Altavoz',
    'LS': 'Altavoz',
    'MIC': 'Micrófono',
    'ANT': 'Antena',
}

# Ordenar por longitud descendente para que los prefijos específicos
# (p. ej. RN, IC, LED) tengan prioridad sobre los genéricos (R, I, L).
_PREFIXES_BY_LEN = sorted(COMPONENT_TYPES.keys(), key=len, reverse=True)


def get_component_type(designator):
    """Determina el tipo de componente desde su designador (R46, C12, U5, IC3...)."""
    if not designator:
        return 'Desconocido'

    des = str(designator).strip().upper()
    for prefix in _PREFIXES_BY_LEN:
        if des.startswith(prefix):
            return COMPONENT_TYPES[prefix]

    return 'Componente'