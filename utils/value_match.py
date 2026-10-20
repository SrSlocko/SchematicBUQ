#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Coincidencia de designador↔valor por proximidad espacial.

Funciona tanto con texto vectorial (PDF) como con OCR (imágenes/escaneos),
porque ambos producen palabras con coordenadas.
"""
import math
import re

from .designators import is_designator

# Tokens que parecen un valor de componente
VALUE_RE = re.compile(
    r'^(?:'
    r'\.?[0-9]+(?:[.,][0-9]+)?\s?[pnumkKMEGRTµ]?[FHRΩVWA]?[%]?'
    r'|[0-9]+[A-Z]+[0-9]+[A-Za-z]*'        # 1N914, 1N4007
    r'|[A-Z]{2,7}-?[0-9]{2,5}[A-Za-z]*'    # TLO-74, LM7805, BC547
    r')$'
)

STRIP_CHARS = ',;:()[]{}""\'\u201c\u201d\n\t'


def clean_token(tok):
    t = (tok or '').strip(STRIP_CHARS).strip()
    # Quitar puntos finales sobrantes, pero conservar decimales tipo .047
    while t.endswith('.'):
        t = t[:-1]
    if t.startswith('.') and not (len(t) > 1 and t[1].isdigit()):
        t = t.lstrip('.')
    return t


def looks_like_value(tok):
    tok = clean_token(tok)
    if not tok:
        return False
    if is_designator(tok):
        return False
    return bool(VALUE_RE.match(tok))


def _center(w):
    return ((w['x0'] + w['x1']) / 2.0, (w['y0'] + w['y1']) / 2.0)


_PURE_INT_RE = re.compile(r'^[0-9]+$')
# Tokens que son solo tensión (p. ej. 100V) → probable dato de tensión, no valor
_VOLTAGE_RE = re.compile(r'^[0-9]+(?:[.,][0-9]+)?\s?V$', re.IGNORECASE)
# Números de parte (empiezan por letras: LM7805, BC547, TLO-74; o dígito+letras+dígitos: 1N914, 2N5415)
_PARTNUM_RE = re.compile(r'^(?:[A-Za-z]{2,}-?[0-9]|[.]?[0-9]+[A-Z]{1,2}[0-9]{2,})')


def _is_part_number(tok):
    return bool(_PARTNUM_RE.match(tok))

# Pasivos: su valor es un número con unidad (10k, .047, 100uF).
# Nunca un modelo (BC547) ni una tensión (100V).
_PASSIVE_PREFIXES = {'R', 'RN', 'RP', 'RV', 'RT', 'C', 'CP', 'CX', 'CY', 'TC',
                     'L', 'FB', 'FL', 'CH', 'Y', 'X', 'XTAL', 'OSC', 'TH', 'PT'}
# Componentes que normalmente NO llevan "valor" (conectores, interruptores, etc.)
# → mejor dejarlo vacío que poner un valor equivocado.
_NO_VALUE_PREFIXES = {'J', 'P', 'CN', 'S', 'SW', 'SB', 'SA', 'K', 'TP', 'TEST',
                      'TB', 'JP', 'JW', 'W', 'H', 'EH', 'G', 'M', 'MG', 'SOL',
                      'LS', 'SP', 'MIC', 'ANT', 'PS', 'PWR'}


def _prefix_of(des):
    m = re.match(r'^([A-Za-z]+)', des)
    return m.group(1).upper() if m else ''


def match_values(words, max_dist=35.0, int_max_dist=14.0,
                 model_max_dist=28.0, int_penalty=12.0,
                 voltage_penalty=9.0, model_penalty=4.0, scale=1.0):
    """Dada una lista de palabras {'x0','y0','x1','y1','text'}, devuelve
    {índice_designador: valor} usando proximidad espacial.

    `scale` adapta las distancias cuando las coordenadas están en píxeles de
    OCR (p. ej. scale=4 para un render a 4x).

    Reglas:
      - Se acepta el token de valor más cercano.
        · número/decimal/unidad → hasta max_dist
        · modelo (LM7805, TLO-74) → hasta model_max_dist (con leve penalización)
        · entero puro (nº de pin) → solo si está muy cerca (int_max_dist)
      - En pasivos (R, C, L, Y…) se descarta cualquier modelo y toda lectura
        de tensión (p. ej. 100V), que no es el valor del componente.
      - En conectores, interruptores, etc. no se asigna valor.
    """
    scale = scale or 1.0
    max_dist *= scale
    int_max_dist *= scale
    model_max_dist *= scale
    int_penalty *= scale
    voltage_penalty *= scale
    model_penalty *= scale
    centers = [_center(w) for w in words]
    values = []  # (idx, token, is_int, is_model, is_voltage)
    for i, w in enumerate(words):
        tok = clean_token(w['text'])
        if not tok or is_designator(tok) or not VALUE_RE.match(tok):
            continue
        is_int = bool(_PURE_INT_RE.match(tok))
        is_model = tok[0].isalpha()
        is_voltage = bool(_VOLTAGE_RE.match(tok))
        values.append((i, tok, is_int, is_model, is_voltage))

    result = {}
    for di, w in enumerate(words):
        des_tok = clean_token(w['text'])
        if not des_tok or not is_designator(des_tok):
            continue
        prefix = _prefix_of(des_tok)
        if prefix in _NO_VALUE_PREFIXES:
            continue  # no le asignamos valor (evita valores erróneos)
        is_passive = prefix in _PASSIVE_PREFIXES
        cx, cy = centers[di]
        best = None
        for vi, vtok, is_int, is_model, is_voltage in values:
            if vi == di:
                continue
            if is_passive and (is_model or is_voltage or _is_part_number(vtok)):
                continue  # un pasivo nunca vale un modelo, nº de parte ni tensión
            vx, vy = centers[vi]
            d = math.hypot(vx - cx, vy - cy)
            penalty = 0.0
            if is_int:
                if d > int_max_dist:
                    continue
                penalty += int_penalty
            elif is_model:
                if d > model_max_dist:
                    continue
                penalty += model_penalty
            else:
                if d > max_dist:
                    continue
            if is_voltage and is_passive:
                penalty += voltage_penalty
            score = d + penalty
            if best is None or score < best[0]:
                best = (score, vtok)
        if best:
            result[di] = best[1]
    return result


def words_from_page(page, zoom=1.0):
    """Palabras con coordenadas de una página PDF, en coordenadas VISIBLES.

    PyMuPDF devuelve las cajas del texto sin rotar, pero ``get_pixmap()`` sí
    aplica ``page.rotation`` al dibujar. Si no rotamos aquí, el resaltado cae en
    otro sitio de la hoja (bug "R21 marca un vacío"). Al rotarlas, las cajas
    coinciden con el render y con las coordenadas del OCR.
    """
    import fitz
    rotated = getattr(page, 'rotation', 0) != 0
    m = page.rotation_matrix if rotated else None
    out = []
    for w in page.get_text("words"):
        x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
        if rotated:
            r = fitz.Rect(x0, y0, x1, y1) * m
            x0, y0, x1, y1 = r.x0, r.y0, r.x1, r.y1
        out.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'text': w[4]})
    return out