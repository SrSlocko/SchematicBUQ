#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import fitz  # PyMuPDF

from .search_index import ComponentResult
from .nomenclature import get_component_type
from .designators import is_designator
from .value_match import match_values, words_from_page
from .ocr import (ocr_words, OCR_ZOOM, MAX_ZOOM, TARGET_WIDTH_TILED,
                  expand_designators, tile_image, tile_has_content,
                  TILE_COLS, TILE_ROWS, TILE_PSMS, TILE_OVERLAP)


class PDFParser:
    # El OCR es el paso lento: repartimos las páginas escaneadas entre varios
    # hilos (cada llamada a Tesseract es un subproceso independiente).
    MAX_OCR_WORKERS = 2

    def __init__(self, use_ocr=True):
        from .config import Config
        self.config = Config()
        self.use_ocr = use_ocr
        self.lang = self.config.ocr_langs
        self._ocr = None
        if use_ocr and self.config.ocr_available():
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_path
                self.config.apply_tessdata()
                self._ocr = pytesseract
            except Exception as e:
                print(f"OCR no disponible: {e}")

    def parse(self, filepath: str, index, progress=None) -> List[ComponentResult]:
        results = []
        try:
            doc = fitz.open(filepath)
        except Exception as e:
            print(f"Error abriendo PDF {filepath}: {e}")
            return results

        # 1) Extraer el texto de cada página (rápido) y ver cuáles son escaneos
        page_words = []      # [(palabras, escala)]
        need_ocr = []        # índices de páginas sin capa de texto
        try:
            total = len(doc)
            for i in range(total):
                w = words_from_page(doc[i])
                page_words.append((w, 1.0))
                if not w:
                    need_ocr.append(i)
        finally:
            doc.close()

        # 2) OCR de las páginas escaneadas (en paralelo si hay varias)
        if need_ocr and self._ocr is not None:
            if progress:
                progress(0, len(need_ocr))
            workers = max(1, min(self.MAX_OCR_WORKERS, len(need_ocr)))
            done = 0
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = {ex.submit(self._ocr_page_file, filepath, i + 1): i
                           for i in need_ocr}
                for fut in as_completed(futures):
                    i = futures[fut]
                    try:
                        # El OCR ya devuelve coordenadas en puntos del PDF
                        page_words[i] = (fut.result(), 1.0)
                    except Exception as e:
                        print(f"Error OCR página {i + 1}: {e}")
                    done += 1
                    if progress:
                        progress(done, len(need_ocr))

        # 3) Analizar designadores y valores
        for i, (words, scale) in enumerate(page_words):
            if words:
                results.extend(self._parse_words(words, filepath, i + 1, scale))
        return results

    def _ocr_page_file(self, filepath, page_num):
        """OCR de una página abriendo su propio documento.

        PyMuPDF no permite compartir un mismo documento entre hilos, así que
        cada hilo abre su propia copia (barato) para poder paralelizar.

        Estrategia: la hoja se reconoce por RECUADROS superpuestos (tiling). En
        los esquemáticos vectoriales el texto es fino y disperso, y ampliar cada
        zona es lo que recupera prácticamente todos los designadores.

        La antigua pasada de «página completa» se eliminó tras medirla: no
        aportaba ni un solo componente de más y costaba ~25 s por página.

        Devuelve las palabras ya convertidas a coordenadas del PDF (puntos).
        """
        try:
            from PIL import Image
            doc = fitz.open(filepath)
            try:
                page = doc[page_num - 1]
                pw = max(1.0, page.rect.width)

                zoom = max(OCR_ZOOM, min(MAX_ZOOM, TARGET_WIDTH_TILED / pw))
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                best = []
                seen = set()
                for part, dx, dy in tile_image(img, TILE_COLS, TILE_ROWS,
                                               overlap=TILE_OVERLAP):
                    if not tile_has_content(part):
                        continue      # recuadro casi vacío: no perdemos tiempo
                    tw = ocr_words(self._ocr, part, lang=self.lang,
                                   psms=TILE_PSMS, prep=False,
                                   offset=(dx, dy))
                    for p in self._to_points(expand_designators(tw), zoom):
                        key = (p['text'].strip().upper(),
                               round(p['x0']), round(p['y0']))
                        if key in seen:
                            continue
                        seen.add(key)
                        best.append(p)
                return best
            finally:
                doc.close()
        except Exception as e:
            print(f"Error OCR de página {page_num}: {e}")
            return []

    @staticmethod
    def _to_points(words, zoom):
        """Convierte coordenadas del render (píxeles) a coordenadas del PDF."""
        z = zoom or 1.0
        return [{'x0': w['x0'] / z, 'y0': w['y0'] / z,
                 'x1': w['x1'] / z, 'y1': w['y1'] / z,
                 'text': w['text'], 'conf': w.get('conf', 0.0)} for w in words]

    def _parse_words(self, words, filepath, page_num, scale):
        scale = scale or 1.0
        values = match_values(words, scale=scale)
        # Deduplicar por designador dentro de la misma página
        best = {}
        for i, w in enumerate(words):
            tok = (w['text'] or '').strip()
            if not tok or not is_designator(tok):
                continue
            des = tok.upper()
            value = values.get(i, '')
            conf = w.get('conf', 100.0)
            rect = [w['x0'] / scale, w['y0'] / scale, w['x1'] / scale, w['y1'] / scale]
            score = (1 if value else 0, conf)
            if des in best and best[des][0] >= score:
                continue
            best[des] = (score, ComponentResult(
                designator=des,
                value=value,
                component_type=get_component_type(des),
                file_path=filepath,
                page=page_num,
                location=f"Página {page_num}",
                connections=[],
                source_type='pdf',
                rects=[rect],
            ))
        return [cr for _, cr in best.values()]
