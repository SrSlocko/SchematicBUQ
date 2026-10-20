#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reglas de reconocimiento de designadores electrónicos estándar."""
import re

# Prefijos de designador más usados (norma IEC 60617 / práctica común)
VALID_PREFIXES = {
    # Pasivos
    'R', 'RN', 'RP', 'RV', 'RT', 'TH', 'NTC', 'PTC', 'PT', 'VR', 'VDR', 'MOV',
    'C', 'CP', 'CX', 'CY', 'TC', 'VC',
    'L', 'FB', 'FL', 'CH', 'BEAD',
    'Y', 'X', 'XTAL', 'OSC',
    # Semiconductores
    'D', 'ZD', 'TVS', 'LED', 'IR', 'LD', 'PD', 'VD',
    'Q', 'T', 'TR', 'FET', 'MOS', 'U', 'IC', 'A',
    'BR', 'CR', 'B', 'DB',
    # Conexión / varios
    'J', 'P', 'CN', 'K', 'S', 'SW', 'SB', 'SA',
    'F', 'FU', 'BT', 'BAT', 'G', 'M', 'MG', 'SOL', 'LS', 'SP', 'MIC', 'ANT',
    'TP', 'TEST', 'TB', 'JP', 'JW', 'W', 'H', 'EH', 'PS', 'PWR',
}

# Un designador = prefijo válido + número + (opcional) subunidad A-D (U1A, R5B)
_DES_RE = re.compile(r'^([A-Z]{1,4})(\d{1,4})([A-D]?)$')
_FIND_RE = re.compile(r'\b([A-Za-z]{1,4}\d{1,4}[A-Da-d]?)\b')


def is_designator(token: str) -> bool:
    """Devuelve True si el token parece un designador de componente real."""
    token = (token or '').strip().upper()
    m = _DES_RE.match(token)
    if not m:
        return False
    return m.group(1) in VALID_PREFIXES


# Tokens fusionados por OCR: letras+dígitos repetidos ("S3Q7", "R17R18")
_MERGE_RE = re.compile(r'([A-Za-z]{1,4}\d{1,4}[A-D]?)')
_LEAD_NUM_RE = re.compile(r'^\d+([A-Za-z]{1,4}\d{1,4}[A-D]?)$')


def split_designator_token(token: str):
    """Divide tokens que el OCR pegó entre dos designadores.

    "S3Q7" -> ['S3','Q7'] · "12Q2" -> ['Q2'] · "R17R18" -> ['R17','R18'].
    Devuelve [] si no se puede extraer nada fiable (se descarta el token).
    """
    t = (token or '').strip().upper()
    if is_designator(t):
        return [t]
    parts = [p.upper() for p in _MERGE_RE.findall(t) if is_designator(p)]
    if len(parts) > 1:
        return parts
    m = _LEAD_NUM_RE.match(t)
    if m and is_designator(m.group(1)):
        return [m.group(1)]
    return []


def find_designators(text: str):
    """Itera tokens candidatos a designador en un texto."""
    for m in _FIND_RE.finditer(text):
        tok = m.group(1)
        if is_designator(tok):
            yield m.start(), m.end(), tok.upper()