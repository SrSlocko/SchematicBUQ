#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Marcadores de "migración" para que la primera ejecución sea limpia.

La versión original del programa distribuía, dentro del paquete, la
configuración y las bases de datos del autor (con rutas de Windows y un aparato
de ejemplo). Al instalar en un equipo nuevo eso hacía que el usuario viera datos
que nunca creó. Aquí llevamos un registro de las tareas de limpieza ya
ejecutadas, en el directorio del usuario.
"""
import os

from . import paths

_MARKERS_DIR = os.path.join(paths.DATA_HOME, ".migrations")


def marker_exists(name: str) -> bool:
    return os.path.exists(os.path.join(_MARKERS_DIR, name))


def mark_done(name: str) -> None:
    try:
        os.makedirs(_MARKERS_DIR, exist_ok=True)
        with open(os.path.join(_MARKERS_DIR, name), "w", encoding="utf-8") as f:
            f.write("ok\n")
    except Exception:
        pass


def is_first_run() -> bool:
    """¿Es la primera vez que se ejecuta el programa en este equipo?

    Se considera primer arranque si todavía no existe la marca
    ``first_run_done``. Sirve para mostrar un mensaje de bienvenida e
    informar al usuario de dónde se guardan sus datos.
    """
    return not marker_exists("first_run_done")


def mark_first_run_done() -> None:
    mark_done("first_run_done")
