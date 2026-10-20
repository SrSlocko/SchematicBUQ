#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Punto de entrada de SchematicBuq.

Además de arrancar la ventana, instala un manejador global de errores: en PyQt5
cualquier excepción no controlada dentro de un slot (un clic, un cambio de
pestaña, un temporizador…) provoca el aborto inmediato del programa sin avisar.
Con este manejador el error se registra en `logs/error.log`, se muestra un aviso
al usuario y la aplicación sigue funcionando en lugar de cerrarse sola.
"""
import os
import sys
import traceback
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QMessageBox

from gui.app import SchematicSearchApp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "error.log")

_last_error = {"key": None}


def _write_log(text: str) -> str:
    """Guarda el error en logs/error.log (o en la carpeta temporal si falla)."""
    candidates = [LOG_FILE, os.path.join(
        os.environ.get("TEMP", LOG_DIR), "schematicbuq_error.log")]
    for path in candidates:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
                f.write(text)
            return path
        except Exception:
            continue
    return ""


def _install_excepthook():
    def hook(exc_type, exc, tb):
        # Un fallo en el propio manejador no debe provocar un bucle.
        try:
            text = "".join(traceback.format_exception(exc_type, exc, tb))
        except Exception:
            text = f"{exc_type!r}: {exc!r}\n"
        try:
            sys.stderr.write(text)
        except Exception:
            pass
        path = _write_log(text)
        # Evita una avalancha de avisos si el mismo error se repite en bucle.
        key = (exc_type, str(exc))
        if key == _last_error["key"]:
            return
        _last_error["key"] = key
        try:
            detalle = f"\n\nSe guardó el detalle en:\n{path}" if path else ""
            QMessageBox.critical(
                None, "Error inesperado",
                "Ocurrió un error inesperado, pero la aplicación sigue abierta.\n\n"
                f"{exc_type.__name__}: {exc}\n\n"
                "Puedes seguir usándola. Si el fallo se repite, prueba a reanalizar "
                f"los esquemáticos.{detalle}")
        except Exception:
            pass

    sys.excepthook = hook


def main():
    _install_excepthook()
    app = QApplication(sys.argv)
    app.setApplicationName("SchematicBuq")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("SchematicBuq")
    window = SchematicSearchApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
