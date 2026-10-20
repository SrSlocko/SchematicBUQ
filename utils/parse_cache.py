#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Caché persistente de resultados de análisis por archivo.

Guardar el resultado del análisis (incluido el OCR, que es lo lento) permite
reindexar un aparato en milisegundos mientras el archivo no cambie. La caché se
invalida automáticamente si cambia la fecha de modificación o el tamaño del
archivo, o si cambia la versión del analizador (VERSION).
"""
import json
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(BASE_DIR, "data", "parse_cache.json")

# Sube esta versión cuando cambie el modo de calcular rects/designadores/valores
# para forzar reindexado (por ejemplo, tras corregir la rotación de páginas).
VERSION = 6


class ParseCache:
    def __init__(self, path=DEFAULT_PATH):
        self.path = path
        self.data = {}
        self.dirty = False
        self.load()

    # ---------- Persistencia ----------
    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if raw.get('version') == VERSION:
                self.data = raw.get('files', {})
        except Exception as e:
            print(f"Caché de análisis no válida, se ignora: {e}")
            self.data = {}

    def save(self):
        if not self.dirty:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump({'version': VERSION, 'files': self.data}, f,
                          ensure_ascii=False)
            os.replace(tmp, self.path)
            self.dirty = False
        except Exception as e:
            print(f"No se pudo guardar la caché de análisis: {e}")

    # ---------- API ----------
    @staticmethod
    def _key(filepath):
        return os.path.abspath(filepath).replace('\\', '/')

    def get(self, filepath, use_ocr):
        """Devuelve la lista de ComponentResult cacheada, o None si no vale."""
        entry = self.data.get(self._key(filepath))
        if not entry:
            return None
        try:
            st = os.stat(filepath)
        except OSError:
            return None
        if entry.get('mtime') != st.st_mtime or entry.get('size') != st.st_size:
            return None
        if bool(entry.get('use_ocr')) != bool(use_ocr):
            return None
        from .search_index import ComponentResult
        try:
            return [ComponentResult(**d) for d in entry.get('results', [])]
        except Exception:
            return None

    def put(self, filepath, use_ocr, results):
        try:
            st = os.stat(filepath)
        except OSError:
            return
        self.data[self._key(filepath)] = {
            'mtime': st.st_mtime,
            'size': st.st_size,
            'use_ocr': bool(use_ocr),
            'results': [r.to_dict() for r in results],
        }
        self.dirty = True

    def invalidate(self, filepath):
        if self.data.pop(self._key(filepath), None) is not None:
            self.dirty = True
