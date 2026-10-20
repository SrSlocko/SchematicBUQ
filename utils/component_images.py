#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Obtención de FOTOS REALES de componentes desde internet.

La única fuente libre y sin clave que funciona de forma fiable es
Wikimedia Commons. Las APIs de catálogo (Nexar/Octopart, Digi-Key, Mouser,
LCSC/EasyEDA) requieren clave o bloquean las peticiones sin autenticar.

Los símbolos de esquema NO se piden a internet: son estándar y se dibujan
localmente en utils/component_symbols.py.
"""
import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_USER_AGENT = "SchematicBuq/1.0 (herramienta de reparación educativa)"

# Términos de búsqueda en inglés (Wikimedia indexa mejor en inglés)
SEARCH_TERMS = {
    "resistor": "resistor electronic component",
    "resistor_network": "resistor network array",
    "potentiometer": "potentiometer trimmer",
    "thermistor": "thermistor",
    "varistor": "varistor MOV",
    "capacitor": "ceramic capacitor electronic",
    "electrolytic": "electrolytic capacitor",
    "inductor": "inductor coil electronic",
    "ferrite": "ferrite bead",
    "filter": "EMI filter electronic",
    "crystal": "crystal oscillator electronic",
    "diode": "diode electronic component",
    "zener": "zener diode",
    "tvs": "TVS diode",
    "led": "LED electronic component",
    "photodiode": "photodiode",
    "bridge": "bridge rectifier",
    "transistor": "transistor electronic component",
    "fet": "MOSFET transistor",
    "ic": "integrated circuit chip",
    "connector": "electrical connector",
    "switch": "push button switch electronic",
    "jumper": "jumper electrical",
    "fuse": "fuse electrical",
    "battery": "battery electrical",
    "motor": "electric motor",
    "solenoid": "solenoid",
    "speaker": "loudspeaker",
    "mic": "microphone",
    "transformer": "transformer electrical",
    "antenna": "antenna radio",
    "terminal": "terminal block electrical",
}


def _looks_like_part_number(value: str) -> bool:
    """True si el valor parece una referencia de fabricante (TL074, BC547, LM358)."""
    if not value:
        return False
    v = value.strip()
    if len(v) < 4 or len(v) > 22:
        return False
    has_alpha = any(c.isalpha() for c in v)
    has_digit = any(c.isdigit() for c in v)
    # Evitar valores de componente (4.7k, 10K, 100nF...)
    if not (has_alpha and has_digit):
        return False
    if any(u in v for u in ("Ω", "kΩ", "MΩ", "ohm")):
        return False
    # 'k'/'M'/'n'/'u'/'p' finales típicos de valores
    if v[-1] in "kKMGnNuUpP" and v[:-1].replace(".", "").isdigit():
        return False
    return True


def build_query(kind: str, value: str = "", designator: str = "") -> str:
    """Construye el mejor término de búsqueda para Wikimedia."""
    if _looks_like_part_number(value):
        return value.strip()
    return SEARCH_TERMS.get(kind, "electronic component")


def search_image(query: str, limit: int = 4):
    """Busca fotos en Wikimedia Commons. Devuelve lista de dicts."""
    query = (query or "").strip()
    if not query:
        return []
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 520,
        "format": "json",
    }
    r = requests.get(COMMONS_API, params=params, timeout=15,
                     headers={"User-Agent": _USER_AGENT})
    r.raise_for_status()
    data = r.json()
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        url = ii.get("thumburl") or ii.get("url")
        if not url:
            continue
        out.append({
            "title": (p.get("title") or "").replace("File:", ""),
            "url": url,
            "page": ii.get("descriptionurl") or "",
        })
    return out


def download_image(url: str, timeout: int = 20) -> bytes:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": _USER_AGENT})
    r.raise_for_status()
    return r.content
