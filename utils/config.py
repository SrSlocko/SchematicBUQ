#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Permite aislar la configuración (pruebas, perfiles alternativos) sin tocar la
# del usuario: basta con definir la variable de entorno SCHEMATICBUQ_CONFIG.
CONFIG_FILE = (os.environ.get("SCHEMATICBUQ_CONFIG")
               or os.path.join(BASE_DIR, "config.json"))
LOCAL_TESSDATA = os.path.join(BASE_DIR, "data", "tessdata")


class Config:
    def __init__(self):
        self.tesseract_path = self._autodetect_tesseract()
        self.poppler_path = self._autodetect_poppler()
        self.ocr_langs = 'spa+eng' if os.path.exists(
            os.path.join(LOCAL_TESSDATA, 'spa.traineddata')) else 'eng'
        self.last_device = ""      # último aparato usado (para autoselección)
        self.auto_tab = "Multímetro"   # pestaña que se abre al seleccionar
        self.load()

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
                if data.get('tesseract_path'):
                    self.tesseract_path = data['tesseract_path']
                if data.get('poppler_path'):
                    self.poppler_path = data['poppler_path']
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
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def ocr_available(self):
        return bool(self.tesseract_path and os.path.exists(self.tesseract_path))