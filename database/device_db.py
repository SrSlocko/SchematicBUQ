#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, List, Any, Optional

from utils import paths, migration


class DeviceDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or paths.DEVICES_FILE
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.devices = {}
        self.load()
        self._migrate_once()

    def _migrate_once(self):
        """Una sola vez: descarta aparatos con rutas de Windows o carpetas que
        ya no existen, para que una instalación nueva arranque vacía."""
        if migration.marker_exists("devices_cleaned"):
            return
        clean = {}
        for k, d in self.devices.items():
            folder = d.get("folder") or ""
            if paths.is_windows_path(folder):
                continue
            if folder and not os.path.isdir(folder):
                continue
            clean[k] = d
        if len(clean) != len(self.devices):
            self.devices = clean
            self.save()
        migration.mark_done("devices_cleaned")

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
            except Exception as e:
                print(f"Error cargando DB: {e}")
    
    def save(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.devices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando DB: {e}")
    
    def add_device(self, name: str, folder_path: str, files: List[str] = None, notes: str = ""):
        key = name.strip()
        existing = self.devices.get(key)
        if existing is not None:
            # Ya existe: actualizamos sin borrar los datos acumulados
            # (nº de componentes indexados, archivos, etiquetas...).
            if folder_path:
                existing["folder"] = folder_path
            if files:
                existing["files"] = files
            if notes:
                existing["notes"] = notes
            existing.setdefault("tags", [])
            existing.setdefault("components_indexed", 0)
        else:
            self.devices[key] = {
                "name": key,
                "folder": folder_path,
                "files": files or [],
                "notes": notes,
                "tags": [],
                "components_indexed": 0
            }
        self.save()
    
    def get_devices(self) -> List[Dict]:
        return list(self.devices.values())
    
    def find_device(self, name: str) -> Optional[Dict]:
        """Busca un aparato por su nombre EXACTO (sin distinguir mayúsculas).

        Antes se comparaba con `nombre in aparato`, de modo que «B2R» devolvía
        «Ampeg_B2R», se actualizaba el aparato equivocado y no se podían
        registrar aparatos cuyo nombre fuera subcadena de otro. Todos los
        llamados usan el nombre exacto (el del desplegable o el de la carpeta),
        así que la coincidencia exacta es la correcta y predecible.
        """
        if not name:
            return None
        key = name.strip().lower()
        for d in self.devices.values():
            if (d.get('name') or '').strip().lower() == key:
                return d
        # Compatibilidad: claves antiguas donde el nombre no coincidía con la clave.
        for k, d in self.devices.items():
            if k.strip().lower() == key:
                return d
        return None

    def has_device(self, name: str) -> bool:
        return self.find_device(name) is not None

    def set_components(self, name: str, count: int):
        d = self.find_device(name)
        if d is not None:
            d['components_indexed'] = count
            self.save()