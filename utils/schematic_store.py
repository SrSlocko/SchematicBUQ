#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Almacén local de esquemáticos y exportación/importación segura (paquetes .sbq).

Guarda los esquemáticos en una carpeta del usuario y permite intercambiarlos
con otros usuarios mediante paquetes .sbq: solo se empaquetan los archivos de
esquemático (PDF, imágenes, netlists), metadatos y miniaturas; nunca ejecutables
ni scripts, para que no pueda viajar ningún "virus".
"""
import os
import json
import hashlib
import shutil
import zipfile
import tempfile

from . import paths

# Extensiones que SÍ se pueden empaquetar (esquemáticos y metadatos).
SAFE_EXTS = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff',
             '.net', '.cir', '.sp', '.txt', '.kicad_sch', '.kicad_sym',
             '.sch', '.json', '.schdoc', '.pcbdoc'}
# Extensiones que NUNCA se empaquetan (ejecutables/scripts).
BLOCKED_EXTS = {'.exe', '.dll', '.bat', '.cmd', '.sh', '.ps1', '.py', '.pyc',
                '.msi', '.scr', '.com', '.vbs', '.js', '.jar', '.apk', '.app',
                '.bin', '.so', '.dylib', '.zip', '.rar', '.7z'}
MAX_SIZE_MB = 500  # límite de un paquete


def default_store_dir():
    """Carpeta de almacén de esquemáticos (estilo Linux, por aparato)."""
    base = os.environ.get("SCHEMATICBUQ_HOME")
    if base:
        return os.path.join(base, "esquematicos")
    return paths.STORE_DIR


class SchematicStore:
    def __init__(self, root=None):
        self.root = root or default_store_dir()
        os.makedirs(self.root, exist_ok=True)

    # ---------- almacenamiento ----------
    def device_dir(self, device: str) -> str:
        safe = "".join(c for c in (device or "General")
                       if c.isalnum() or c in " -_().").strip() or "General"
        path = os.path.join(self.root, safe)
        os.makedirs(path, exist_ok=True)
        return path

    def save_file(self, src_path: str, device: str = "General") -> str:
        """Copia un esquemático al almacén. Devuelve la ruta destino."""
        if not os.path.isfile(src_path):
            raise FileNotFoundError(src_path)
        ext = os.path.splitext(src_path)[1].lower()
        if ext in BLOCKED_EXTS or ext not in SAFE_EXTS:
            raise ValueError(f"Extensión no permitida: {ext}")
        dst = os.path.join(self.device_dir(device), os.path.basename(src_path))
        shutil.copy2(src_path, dst)
        return dst

    def list_files(self, device: str = None):
        if device:
            d = self.device_dir(device)
            return sorted(os.path.join(d, f) for f in os.listdir(d))
        out = []
        for root, _dirs, files in os.walk(self.root):
            out.extend(os.path.join(root, f) for f in files)
        return sorted(out)

    def devices(self):
        return sorted(d for d in os.listdir(self.root)
                      if os.path.isdir(os.path.join(self.root, d)))

    # ---------- exportar paquete seguro ----------
    def export_package(self, dest_zip: str, device: str = None, index=None):
        """Crea un .sbq (zip) con esquemáticos + metadatos, sin ejecutables."""
        files = self.list_files(device)
        total = 0
        manifest = {"format": "schematicbuq-package", "version": 1,
                    "device": device or "all", "files": []}
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in BLOCKED_EXTS or ext not in SAFE_EXTS:
                    continue
                size = os.path.getsize(f)
                total += size
                if total > MAX_SIZE_MB * 1024 * 1024:
                    break
                arc = os.path.relpath(f, self.root).replace(os.sep, "/")
                z.write(f, arcname=f"schematicos/{arc}")
                manifest["files"].append({
                    "path": arc,
                    "size": size,
                    "sha256": self._sha256(f),
                })
            if index is not None:
                idx_tmp = os.path.join(tempfile.gettempdir(), "sbq_index.json")
                index.export_json(idx_tmp)
                z.write(idx_tmp, arcname="index.json")
            z.writestr("manifest.json",
                       json.dumps(manifest, ensure_ascii=False, indent=2))
        return dest_zip

    # ---------- importar paquete seguro ----------
    def import_package(self, zip_path: str, progress=None):
        """Importa un .sbq validando que solo contenga esquemáticos seguros."""
        imported, skipped = [], []
        with zipfile.ZipFile(zip_path) as z:
            try:
                manifest = json.loads(z.read("manifest.json").decode("utf-8"))
                if manifest.get("format") != "schematicbuq-package":
                    raise ValueError("No es un paquete SchematicBuq válido")
            except Exception as e:
                raise ValueError(f"Paquete inválido: {e}")
            names = z.namelist()
            total = len(names)
            for i, name in enumerate(names, 1):
                if name.endswith("/"):
                    continue
                base = os.path.basename(name)
                ext = os.path.splitext(base)[1].lower()
                if base == "manifest.json":
                    continue
                # Seguridad: bloquea rutas absolutas/traversal y extensiones peligrosas
                if name.startswith("/") or ".." in name.split("/"):
                    skipped.append((name, "ruta insegura"))
                    continue
                if ext in BLOCKED_EXTS or ext not in SAFE_EXTS:
                    if name != "index.json":
                        skipped.append((name, "extensión no permitida"))
                        continue
                if name == "index.json":
                    continue
                dest = os.path.join(self.root, name)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with z.open(name) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
                imported.append(dest)
                if progress:
                    progress(i, total)
        return imported, skipped

    @staticmethod
    def _sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
