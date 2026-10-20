#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from .pdf_parser import PDFParser
from .image_parser import ImageParser
from .netlist_parser import NetlistParser
from .kicad_parser import KiCadParser
from .easyeda_parser import EasyEDAParser
from .altium_parser import AltiumParser
from .search_index import SearchIndex
from .cleanup import filter_false_positives, drop_implausible_values

SUPPORTED_EXTS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff',
    '.net', '.cir', '.txt', '.sp', '.kicad_sch', '.kicad_sym',
    '.json', '.schdoc', '.pcbdoc', '.sch'
}


class FileLoader:
    def __init__(self, index: SearchIndex, device: str = "", use_ocr: bool = True,
                 cache=None, progress=None):
        self.index = index
        self.device = device
        self.use_ocr = use_ocr
        self.cache = cache
        self.progress = progress      # callable(str) para el estado de la UI
        self.pdf_parser = PDFParser(use_ocr=use_ocr)
        self.image_parser = ImageParser(use_ocr=use_ocr)
        self.netlist_parser = NetlistParser()
        self.kicad_parser = KiCadParser()
        self.easyeda_parser = EasyEDAParser()
        self.altium_parser = AltiumParser()

    def _notify(self, msg):
        if self.progress:
            try:
                self.progress(msg)
            except Exception:
                pass

    def _register(self, results, filepath):
        for r in results:
            r.device = self.device
            # Ruta canónica para que las comparaciones por archivo coincidan
            # (la caché y os.walk pueden usar separadores distintos).
            try:
                r.file_path = os.path.normpath(os.path.abspath(r.file_path))
            except Exception:
                pass
            self.index.add_result(r)
        if self.device:
            self.index.register_file_device(filepath, self.device)

    def load_path(self, path: str):
        if os.path.isfile(path):
            self.load_file(path)
        elif os.path.isdir(path):
            for root, _dirs, files in os.walk(path):
                for fname in sorted(files):
                    self.load_file(os.path.join(root, fname))

    def _parse(self, filepath, ext):
        on_page = lambda pg, total: self._notify(
            f"{os.path.basename(filepath)} — página {pg}/{total}")
        if ext == '.pdf':
            return self.pdf_parser.parse(filepath, self.index, progress=on_page)
        if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'):
            return self.image_parser.parse(filepath, self.index)
        if ext in ('.net', '.cir', '.txt', '.sp'):
            return self.netlist_parser.parse(filepath, self.index)
        if ext in ('.kicad_sch', '.kicad_sym', '.sch'):
            return self.kicad_parser.parse(filepath, self.index)
        if ext == '.json':
            return self.easyeda_parser.parse(filepath, self.index)
        if ext in ('.schdoc', '.pcbdoc'):
            return self.altium_parser.parse(filepath, self.index)
        return None

    def load_file(self, filepath: str):
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in SUPPORTED_EXTS:
            return

        results = self.cache.get(filepath, self.use_ocr) if self.cache else None
        if results is not None:
            self._notify(f"{os.path.basename(filepath)} — en caché")
        else:
            try:
                results = self._parse(filepath, ext)
            except Exception as e:
                print(f"Error cargando {filepath}: {e}")
                return
            if results is None:
                return
            if self.cache:
                self.cache.put(filepath, self.use_ocr, results)

        results = filter_false_positives(results)
        results = drop_implausible_values(results)
        self._register(results, filepath)
