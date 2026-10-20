#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from typing import List

try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError:
    cv2 = None
    np = None
    pytesseract = None

from .search_index import ComponentResult
from .nomenclature import get_component_type
from .designators import is_designator
from .value_match import match_values
from .ocr import (ocr_words, expand_designators, tile_image, tile_has_content,
                  TILE_COLS, TILE_ROWS, TILE_OVERLAP, TILE_PSMS)
from .config import Config


class ImageParser:
    def __init__(self, use_ocr=True):
        self.config = Config()
        self.lang = self.config.ocr_langs
        self.ok = False
        if use_ocr and pytesseract and os.path.exists(self.config.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_path
            self.config.apply_tessdata()
            self.ok = True

    def preprocess_image(self, image_path):
        if not cv2 or not np:
            return image_path
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return image_path
        _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def _to_pil(self, image):
        """Convierte lo que devuelve el preprocesado (ruta, PIL o ndarray) a PIL."""
        from PIL import Image
        if isinstance(image, Image.Image):
            return image
        if isinstance(image, str):
            return Image.open(image)
        try:                      # ndarray de OpenCV (escala de grises)
            return Image.fromarray(image)
        except Exception:
            return None

    def _ocr_tiled(self, image):
        """OCR por recuadros superpuestos.

        En hojas grandes el texto es muy fino: ampliarlo por zonas recupera
        bastantes más designadores que una única pasada sobre toda la imagen.
        """
        img = self._to_pil(image)
        if img is None:
            return ocr_words(pytesseract, image, lang=self.lang)
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        W, H = img.size
        if W * H < 2_500_000:          # imagen pequeña: una sola pasada
            return ocr_words(pytesseract, img, lang=self.lang)
        out = []
        for part, dx, dy in tile_image(img, TILE_COLS, TILE_ROWS,
                                       overlap=TILE_OVERLAP):
            if not tile_has_content(part):
                continue
            out.extend(ocr_words(pytesseract, part, lang=self.lang,
                                 psms=TILE_PSMS, offset=(dx, dy)))
        return out

    def parse(self, filepath: str, index=None) -> List[ComponentResult]:
        results = []
        if not self.ok:
            print("OCR no disponible; se omite la imagen")
            return results

        words = []
        try:
            processed = self.preprocess_image(filepath)
            words = expand_designators(self._ocr_tiled(processed))
        except Exception as e:
            print(f"Error OCR en {filepath}: {e}")
            return results

        if not words:
            return results

        values = match_values(words)
        best = {}
        for i, w in enumerate(words):
            tok = (w['text'] or '').strip()
            if not tok or not is_designator(tok):
                continue
            des = tok.upper()
            value = values.get(i, '')
            conf = w.get('conf', 100.0)
            score = (1 if value else 0, conf)
            if des in best and best[des][0] >= score:
                continue
            best[des] = (score, ComponentResult(
                designator=des,
                value=value,
                component_type=get_component_type(des),
                file_path=filepath,
                page=1,
                location="Imagen (OCR)",
                connections=[],
                source_type='image',
                rects=[[w['x0'], w['y0'], w['x1'], w['y1']]],
            ))
        return [cr for _, cr in best.values()]