#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import shutil
from . import system_utils
from . import paths

BASE_DIR = paths.BASE_DIR
# Configuración en el directorio del usuario (nunca en /usr/share).
CONFIG_FILE = paths.CONFIG_FILE
LOCAL_TESSDATA = os.path.join(BASE_DIR, "data", "tessdata")


class Config:
    def __init__(self):
        self.tesseract_path = self._autodetect_tesseract()
        self.poppler_path = self._autodetect_poppler()
        self.ocr_langs = self._autodetect_langs()
        self.last_device = ""      # último aparato usado (para autoselección)
        self.auto_tab = "Multímetro"   # pestaña que se abre al seleccionar
        self.low_resource_mode = system_utils.SYSTEM_INFO.get('low_resource_mode', False)
        self.max_workers = system_utils.SYSTEM_INFO.get('max_workers', 1)
        self.load()

    def _autodetect_langs(self):
        """Idiomas OCR disponibles: usa spa+eng si existen, si no eng, si no ''.

        Busca primero en la carpeta local del paquete (`data/tessdata`) y, si no,
        en las rutas habituales del Tesseract del sistema (Linux/Windows/macOS).
        """
        candidates = [LOCAL_TESSDATA]
        tp = self.tesseract_path
        if tp:
            # tessdata suele estar junto al binario o en ../share/tessdata
            bindir = os.path.dirname(tp)
            candidates += [
                os.path.join(bindir, "tessdata"),
                os.path.join(bindir, "..", "share", "tessdata"),
                os.path.join(bindir, "..", "share", "tesseract-ocr", "tessdata"),
                "/usr/share/tessdata",
                "/usr/share/tesseract-ocr/5/tessdata",
                "/usr/share/tesseract-ocr/4.00/tessdata",
                "/usr/local/share/tessdata",
            ]
        have = set()
        for d in candidates:
            try:
                if not os.path.isdir(d):
                    continue
                for f in os.listdir(d):
                    if f.endswith(".traineddata"):
                        have.add(f[:-len(".traineddata")])
            except Exception:
                continue
        langs = []
        if "spa" in have:
            langs.append("spa")
        if "eng" in have:
            langs.append("eng")
        return "+".join(langs) if langs else "eng"

    def apply_tessdata(self):
        """Apunta Tesseract a la carpeta local de idiomas si existe (spa+eng)."""
        if os.path.isdir(LOCAL_TESSDATA) and os.listdir(LOCAL_TESSDATA):
            os.environ['TESSDATA_PREFIX'] = LOCAL_TESSDATA

    @staticmethod
    def _autodetect_tesseract():
        found = shutil.which("tesseract")
        if found:
            return found
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return ""

    @staticmethod
    def _autodetect_poppler():
        found = shutil.which("pdftoppm")
        if found:
            return os.path.dirname(found)
        candidates = [
            r"C:\poppler\Library\bin",
            r"C:\Program Files\poppler\Library\bin",
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c
        return ""

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Se ignoran rutas guardadas de otro sistema operativo
                # (p. ej. C:\Program Files\... en un equipo Linux).
                tp = data.get('tesseract_path')
                if tp and not paths.is_windows_path(tp) and os.path.exists(tp):
                    self.tesseract_path = tp
                pp = data.get('poppler_path')
                if pp and not paths.is_windows_path(pp) and os.path.isdir(pp):
                    self.poppler_path = pp
                if data.get('last_device'):
                    self.last_device = data['last_device']
                if data.get('auto_tab'):
                    self.auto_tab = data['auto_tab']
            except Exception as e:
                print(f"Error cargando config: {e}")

    def save(self):
        data = {
            'tesseract_path': self.tesseract_path,
            'poppler_path': self.poppler_path,
            'last_device': self.last_device,
            'auto_tab': self.auto_tab,
        }
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def ocr_available(self):
        return bool(self.tesseract_path and os.path.exists(self.tesseract_path))
    def get_ocr_config(self):
        return {
            'tesseract_path': self.tesseract_path,
            'langs': self.ocr_langs,
            'low_resource': self.low_resource_mode,
            'max_workers': self.max_workers
        }
