#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import os
from urllib.parse import urlparse
from typing import Optional

from . import paths

class PDFOnlineFetcher:
    @staticmethod
    def fetch_pdf(url: str, save_dir: str = None) -> Optional[str]:
        save_dir = save_dir or paths.SCHEMATICS_DIR
        try:
            os.makedirs(save_dir, exist_ok=True)
            response = requests.get(url, stream=True, timeout=60, headers={
                'User-Agent': 'SchematicBuq/1.0'
            })
            response.raise_for_status()
            # Obtener nombre
            parsed = urlparse(url)
            fname = os.path.basename(parsed.path) or 'descarga.pdf'
            if not fname.endswith('.pdf'):
                fname += '.pdf'
            filepath = os.path.join(save_dir, fname)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception as e:
            print(f"Error descargando PDF: {e}")
            return None