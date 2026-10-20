#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extracción de palabras por OCR optimizada para esquemáticos.

Los esquemáticos tienen texto disperso y muy fino por toda la hoja. La
estrategia que mejor funciona (medida sobre hojas reales) es:

  * Dividir la hoja en RECUADROS superpuestos (tiling 3x3 con solape 0.25): en
    cada recuadro el texto es relativamente más grande y se recuperan muchos
    más designadores que en una única pasada de página completa.
  * Renderizar con bastante resolución (objetivo ~9000 px por recuadro).
  * Dos modos de segmentación (PSM 11 texto disperso, PSM 6 bloque), que se
    complementan: el PSM 11 solo pierde bastantes designadores.
  * Unión de los resultados y división de tokens fusionados ("S3Q7" -> S3, Q7).

Lo que se probó y NO se usa: la pasada de página completa (no aportaba ni un
componente de más y costaba ~25 s), el preprocesado con umbral/Otsu (irregular),
PSM 3 (lento sin ganancia), --oem 1 (sin diferencia) y recuadros 4x4 (peor).
"""
import re

from .designators import is_designator, split_designator_token

DEFAULT_PSMS = (11, 6)
DEFAULT_CONF = 45.0
OCR_ZOOM = 4.0          # zoom mínimo de render
MAX_ZOOM = 10.0         # tope de zoom (evita renders gigantescos)
TARGET_WIDTH = 6500.0   # ancho objetivo del render de página completa
TARGET_WIDTH_TILED = 9000.0   # ancho objetivo por recuadro (más detalle)
# Recuadros (tiling) en que se divide la hoja y modos de OCR que se usan.
TILE_COLS = 3
TILE_ROWS = 3
# Solape generoso: al cortar en recuadros, el texto del borde se perdería; con
# 0.25 se recupera bastante más (medido: 59 -> 67 y 86 -> 87 designadores).
TILE_OVERLAP = 0.25
TILE_PSMS = (11, 6)
# Fracción mínima de píxeles oscuros para considerar un recuadro con contenido.
TILE_MIN_INK = 0.004


def tile_has_content(tile, min_ink=TILE_MIN_INK):
    """True si el recuadro tiene dibujo/texto suficiente (si no, se salta)."""
    try:
        g = tile.convert("L")
        hist = g.histogram()
        dark = sum(hist[:200])
        total = tile.size[0] * tile.size[1]
        return total > 0 and (dark / float(total)) >= min_ink
    except Exception:
        return True


def prep_image(image):
    """Preprocesado para texto fino de esquemáticos (mejora muchísimo el OCR)."""
    try:
        from PIL import ImageOps, ImageFilter
        g = ImageOps.grayscale(image)
        a = ImageOps.autocontrast(g)
        b = a.point(lambda p: 255 if p > 128 else 0)
        return b.filter(ImageFilter.MinFilter(3))
    except Exception:
        return image


def tile_image(image, cols=3, rows=3, overlap=0.12):
    """Divide la imagen en recuadros superpuestos, devolviendo (imagen, dx, dy)."""
    W, H = image.size
    out = []
    for r in range(rows):
        for c in range(cols):
            x0 = int(c * W / cols - (W / cols) * overlap) if c else 0
            y0 = int(r * H / rows - (H / rows) * overlap) if r else 0
            x1 = int((c + 1) * W / cols + (W / cols) * overlap)
            y1 = int((r + 1) * H / rows + (H / rows) * overlap)
            box = (max(0, x0), max(0, y0), min(W, x1), min(H, y1))
            out.append((image.crop(box), box[0], box[1]))
    return out


def _run(pytesseract, image, lang, psm):
    cfg = f'--psm {psm}'
    try:
        return pytesseract.image_to_data(
            image, lang=lang, config=cfg,
            output_type=pytesseract.Output.DICT)
    except Exception:
        try:
            return pytesseract.image_to_data(
                image, config=cfg,
                output_type=pytesseract.Output.DICT)
        except Exception:
            return None


def ocr_words(pytesseract, image, lang='eng', psms=DEFAULT_PSMS,
              conf_min=DEFAULT_CONF, drop_lowercase=True,
              prep=False, offset=(0, 0)):
    """Devuelve palabras {'x0','y0','x1','y1','text','conf'} de la imagen.

    Combina varios PSM y filtra por confianza. `offset` desplaza las coordenadas
    (útil al procesar recuadros: el desplazamiento del recuadro en la imagen
    completa).
    """
    if prep:
        image = prep_image(image)
    dx, dy = offset
    words = []
    seen = set()
    for psm in psms:
        data = _run(pytesseract, image, lang, psm)
        if not data:
            continue
        texts = data.get('text', [])
        for i in range(len(texts)):
            txt = (texts[i] or '').strip()
            if not txt:
                continue
            try:
                conf = float(data['conf'][i])
            except Exception:
                conf = -1.0
            if conf < conf_min:
                continue
            if drop_lowercase and txt.islower() and is_designator(txt):
                continue
            try:
                x = float(data['left'][i]); y = float(data['top'][i])
                w = float(data['width'][i]); h = float(data['height'][i])
            except Exception:
                continue
            # Evitar duplicados exactos entre PSM (misma caja y texto)
            key = (txt.upper(), round((x + dx) / 5), round((y + dy) / 5))
            if key in seen:
                continue
            seen.add(key)
            words.append({'x0': x + dx, 'y0': y + dy,
                          'x1': x + dx + w, 'y1': y + dy + h,
                          'text': txt, 'conf': conf})
    return words


def expand_designators(words):
    """Divide tokens fusionados por OCR en designadores reales.

    P. ej. 'S3Q7' -> ['S3','Q7']; '12Q2' -> ['Q2']. Devuelve una lista NUEVA de
    palabras (los tokens fusionados se sustituyen por sus partes, conservando
    caja y confianza).
    """
    out = []
    for w in words:
        tok = (w['text'] or '').strip()
        if is_designator(tok):
            out.append(w)
            continue
        parts = split_designator_token(tok)
        if len(parts) > 1:
            # Repartir la caja entre las partes
            n = len(parts)
            total = max(1.0, w['x1'] - w['x0'])
            seg = total / n
            for k, p in enumerate(parts):
                out.append({'x0': w['x0'] + k * seg, 'y0': w['y0'],
                            'x1': w['x0'] + (k + 1) * seg, 'y1': w['y1'],
                            'text': p, 'conf': w.get('conf', 0.0)})
        else:
            out.append(w)
    return out


def count_designators(words):
    """Cuenta designadores válidos (útil para decidir si repetir a mayor zoom)."""
    return len({(w['text'] or '').strip().upper()
                for w in words if is_designator(w['text'])})
