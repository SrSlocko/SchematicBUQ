#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Restablece los datos locales del usuario (primer uso limpio).

Borra la configuración, la caché, la base de datos de aparatos y los
esquemáticos guardados. No toca nada fuera de la carpeta del usuario.
"""
import os
import shutil

from . import paths


def _rm(path: str, errors: list) -> None:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=False)
        elif os.path.exists(path):
            os.remove(path)
    except Exception as e:
        errors.append(f"{path}: {e}")


def reset_user_data() -> list:
    """Borra los datos del usuario. Devuelve la lista de errores (vacía = OK)."""
    errors = []
    for target in (paths.DATA_HOME, paths.CONFIG_DIR):
        _rm(target, errors)
    # Vuelve a crear las carpetas base para que la app siga funcionando.
    paths.ensure_user_dirs()
    return errors
