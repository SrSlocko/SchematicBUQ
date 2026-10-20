# -*- coding: utf-8 -*-
"""El manejador global de errores evita que la app se cierre por un slot fallido."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["SCHEMATICBUQ_CONFIG"] = os.path.join(tempfile.mkdtemp(), "config.json")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

app = QApplication(sys.argv)

import main as sbuq_main

# Sin diálogo modal (para que la prueba no se quede esperando).
avisos = []
sbuq_main.QMessageBox.critical = lambda *a, **k: avisos.append(a)
sbuq_main._install_excepthook()

def slot_malo():
    raise ZeroDivisionError("fallo simulado dentro de un slot")

QTimer.singleShot(10, slot_malo)
QTimer.singleShot(80, lambda: None)
QTimer.singleShot(150, app.quit)

rc = app.exec_()
print("app.exec_() devolvió:", rc)
print("avisos mostrados:", len(avisos))
log_ok = os.path.exists(sbuq_main.LOG_FILE) or os.path.exists(
    os.path.join(os.environ.get("TEMP", ""), "schematicbuq_error.log"))
print("log de error escrito:", log_ok)

ok = (rc == 0 and len(avisos) == 1 and log_ok)
print("\nRESULTADO:", "TODO OK" if ok else "REVISAR")
sys.exit(0 if ok else 1)
