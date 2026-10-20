#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rutas del programa y del usuario.

El programa puede instalarse en modo solo-lectura (``/usr/share/schematicbuq``
en Linux, ``C:\\Program Files`` en Windows). Por eso TODOS los datos que se
escriben (configuración, caché, base de datos de aparatos, esquemáticos,
registros) van a una carpeta del usuario siguiendo el estándar XDG, y los
recursos de solo-lectura (iconos, nomenclatura, tessdata) se leen del paquete
instalado.
"""
import os
import sys

# ``utils/paths.py`` -> raíz del paquete instalado.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Versión de la aplicación (única fuente de verdad).
APP_VERSION = "1.2.0"


def _base_home() -> str:
    """Carpeta raíz de datos del usuario (respetando SCHEMATICBUQ_HOME)."""
    override = os.environ.get("SCHEMATICBUQ_HOME")
    if override:
        return override
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "schematicbuq")
    xdg = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(xdg, "schematicbuq")


def _config_home() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "schematicbuq")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "schematicbuq")


DATA_HOME = _base_home()

# --- Datos escribibles (usuario) ---
CONFIG_DIR = _config_home()
CONFIG_FILE = os.environ.get("SCHEMATICBUQ_CONFIG") or os.path.join(
    CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(DATA_HOME, "cache")
PARSE_CACHE_FILE = os.path.join(CACHE_DIR, "parse_cache.json")
DATABASE_DIR = os.path.join(DATA_HOME, "database")
DEVICES_FILE = os.path.join(DATABASE_DIR, "devices.json")
SCHEMATICS_DIR = os.path.join(DATA_HOME, "esquematicos")
STORE_DIR = os.path.join(DATA_HOME, "esquematicos")
LOG_DIR = os.path.join(DATA_HOME, "logs")
INDEX_FILE = os.path.join(DATA_HOME, "index.json")

# --- Recursos de solo-lectura (paquete) ---
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
DATA_DIR = os.path.join(BASE_DIR, "data")
NOMENCLATURE_FILE = os.path.join(DATA_DIR, "nomenclature_es.json")

ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
ICON_ICO = os.path.join(ICONS_DIR, "app.ico")
ICON_PNG = os.path.join(ICONS_DIR, "app.png")


def best_icon_file() -> str:
    """Devuelve el archivo de icono más adecuado para el sistema.

    En Windows se prefiere ``.ico`` (multirresolución); en Linux/macOS se usa
    ``.png`` porque Qt5 no siempre trae el complemento para leer ``.ico`` y,
    cuando lo lee, suele verse pixelado al escalarlo.
    """
    if sys.platform.startswith("win"):
        order = (ICON_ICO, ICON_PNG)
    else:
        order = (ICON_PNG, ICON_ICO)
    for p in order:
        if os.path.exists(p):
            return p
    return ""


# Compatibilidad: nombre histórico usado por el resto del código.
ICON_FILE = best_icon_file() or ICON_ICO


def ensure_user_dirs() -> None:
    """Crea las carpetas de usuario que la app necesita para escribir."""
    for d in (DATA_HOME, CONFIG_DIR, CACHE_DIR, DATABASE_DIR,
              SCHEMATICS_DIR, LOG_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def is_windows_path(path: str) -> bool:
    """Detecta rutas absolutas de Windows (p. ej. ``C:\\...`` o ``D:/...``).

    Sirve para descartar rutas guardadas en la configuración o en la base de
    datos que no existen en Linux/macOS.
    """
    if not path:
        return False
    p = str(path).replace("\\", "/")
    return (len(p) >= 2 and p[1] == ":") or p.startswith("//")
