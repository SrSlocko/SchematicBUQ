#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Filtrado de falsos positivos detectados por OCR / extracción de texto.

En esquemáticos escaneados el OCR a veces lee números de parte como si fueran
designadores (p. ej. el JFET ``J112`` junto a ``Q1``, o ``TL074`` leído como
``F074``). Este módulo aplica reglas conservadoras sobre el conjunto de
resultados de UN archivo para descartar esos casos sin perder componentes reales.
"""
import re
from collections import defaultdict

_DES_RE = re.compile(r'^([A-Z]+)(\d+)([A-D]?)$')
# Números de parte: empiezan por letras (LM7805, TL074) o dígito+letras+dígitos (1N914)
_PARTNUM_RE = re.compile(r'^(?:[A-Za-z]{2,}-?[0-9]|[.]?[0-9]+[A-Z]{1,2}[0-9]{2,})')

# --- Plausibilidad del VALOR según el tipo de componente -------------------
# Un condensador nunca vale "10K"; una resistencia nunca vale "100nF".
_CAP_PREFIXES = {'C', 'CP', 'CX', 'CY', 'CB', 'CE', 'CT', 'TC'}
_RES_PREFIXES = {'R', 'RN', 'RP', 'RV', 'RT'}
# Valor con magnitud de resistencia (k, M, G, R, Ω...)
_RES_MAGNITUDE_RE = re.compile(
    r'(?i)^[0-9]+(?:\.[0-9]+)?\s?(k|meg|m|g|r|kohm|kΩ|ohm|Ω)$')
# Código de condensador cerámico "104K"/"224J" (3 cifras + tolerancia):
# NO se toca, porque ahí "K"/"J"/"M" es la tolerancia, no la magnitud.
_CERAMIC_CODE_RE = re.compile(r'^[0-9]{3}[A-Za-z]$')
# Valor con unidad de capacidad (F, uF, nF, pF...)
_CAP_UNIT_RE = re.compile(r'(?i)^[0-9]+(?:\.[0-9]+)?\s?(p|n|u|µ)?f$|^[0-9]+(?:\.[0-9]+)?\s?(p|n|u|µ)$')


def _prefix_of(designator):
    m = re.match(r'^([A-Za-z]+)', designator or '')
    return m.group(1).upper() if m else ''


def drop_implausible_values(results):
    """Devuelve la lista con valores imposibles para el tipo ya vaciados.

    P. ej. ``C26 = 100K`` (magnitud de resistencia en un condensador) o
    ``R12 = 100nF``. Se deja el valor vacío en vez de uno equivocado.

    No modifica los objetos originales (la caché guarda los datos brutos), sino
    que devuelve una copia solo de los que hay que corregir.
    """
    from dataclasses import replace
    out = []
    for r in results:
        if (r.source_type or '') not in ('pdf', 'image'):
            out.append(r)
            continue
        v = (r.value or '').strip()
        if not v:
            out.append(r)
            continue
        pre = _prefix_of(r.designator)
        bad = False
        if pre in _CAP_PREFIXES:
            bad = bool(_RES_MAGNITUDE_RE.match(v)) and not _CERAMIC_CODE_RE.match(v)
        elif pre in _RES_PREFIXES:
            bad = bool(_CAP_UNIT_RE.match(v))
        out.append(replace(r, value='') if bad else r)
    return out


def _is_part_number(tok):
    return bool(_PARTNUM_RE.match((tok or '').strip()))


def filter_false_positives(results):
    """Devuelve la lista sin designadores que son casi seguro ruido.

    Solo se aplica a resultados de PDF/imagen (OCR o texto); los netlists y
    proyectos CAD traen designadores fiables y no se tocan.
    """
    if not results:
        return results

    # Agrupar instancias por prefijo alfabético
    by_prefix = defaultdict(list)
    for r in results:
        if (r.source_type or '') not in ('pdf', 'image'):
            continue
        m = _DES_RE.match((r.designator or '').upper())
        if m:
            by_prefix[m.group(1)].append((int(m.group(2)), m.group(2), r))

    drop = set()

    for prefix, items in by_prefix.items():
        distinct = sorted({n for n, _d, _ in items})
        low = [n for n in distinct if n < 100]

        # 1) Número de parte con forma de designador: J112, J176...
        #    número >= 100, hay >= 2 hermanos < 100, sin valor y es >= 5x el
        #    mayor hermano bajo. Los conectores reales (J1..J17) no se tocan.
        if len(low) >= 2 and len(distinct) > len(low):
            max_low = max(low)
            for n, _d, r in items:
                if n >= 100 and not (r.value or '').strip() and n >= 5 * max_low:
                    drop.add(id(r))

        # 1b) Prefijo 'J' con número >= 100 y sin valor: en electrónica son
        #     transistores JFET (J112, J176, J113...) leídos como conectores.
        for n, _d, r in items:
            if prefix == 'J' and n >= 100 and not (r.value or '').strip():
                drop.add(id(r))

        # 1c) Número con ceros a la izquierda y sin valor: ruido de OCR
        #     (A06, SA06, T0033, D012...). Un designador real no suele
        #     numerarse con ceros delante.
        for _n, digits, r in items:
            if len(digits) >= 2 and digits.startswith('0') \
                    and not (r.value or '').strip():
                drop.add(id(r))

        # 2) Designador aislado (un único número en el archivo), sin valor y
        #    con número alto: casi siempre ruido (p. ej. S176).
        if len(distinct) == 1:
            n = distinct[0]
            if n > 50 and not any((r.value or '').strip() for _, _d, r in items):
                for _, _d, r in items:
                    drop.add(id(r))

    # 3) Fusible cuyo "valor" es un número de parte (F074 = TL074 mal leído).
    for r in results:
        if (r.source_type or '') not in ('pdf', 'image'):
            continue
        m = _DES_RE.match((r.designator or '').upper())
        v = (r.value or '').strip()
        if m and m.group(1) in ('F', 'FU') and v and _is_part_number(v):
            drop.add(id(r))

    return [r for r in results if id(r) not in drop]
