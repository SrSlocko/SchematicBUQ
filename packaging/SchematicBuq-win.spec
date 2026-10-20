# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para Windows: un ÚNICO archivo .exe portable.

El usuario pidió expresamente que en Windows «no se instale en el disco C:»,
sino que sea «solo un programa, lo abres y carga». Por eso en Windows se
genera un ejecutable de UN SOLO archivo (``--onefile``): el usuario lo copia
donde quiera (memoria USB incluida) y funciona sin instalar nada.

Todos los datos configurables (configuración, caché, base de datos de
aparatos, esquemáticos, registros) se guardan en la carpeta del usuario
(``%LOCALAPPDATA%\\schematicbuq`` y ``%APPDATA%\\schematicbuq``), NUNCA junto
al .exe ni en ``C:\\``. El icono se incrusta en el propio ejecutable.
"""
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden = []
# Colección dirigida: evitamos submódulos pesados o problemáticos.
for pkg in ("cv2", "pdfminer", "PIL", "pytesseract", "pyqtgraph", "qdarkstyle"):
    try:
        hidden += collect_submodules(pkg)
    except Exception as exc:  # pragma: no cover - entorno de empaquetado
        print(f"Aviso: no se pudieron recopilar submódulos de {pkg}: {exc}")

# PyMuPDF: solo el paquete principal y su alias `fitz`
hidden += ["fitz", "pymupdf"]

excluded = [
    "pyqtgraph.examples", "pyqtgraph.opengl", "pyqtgraph.console",
    "pyqtgraph.flowchart", "pyqtgraph.jupyter",
    "tkinter", "matplotlib",
    "PyQt5.QtWebEngineWidgets", "PyQt5.QtQuick", "PyQt5.QtQml",
    "onnxruntime", "pymupdf.layout", "pymupdf4llm",
    "qdarkstyle.example", "qdarkstyle.utils",
]

datas = [
    ("resources", "resources"),
    ("data", "data"),
]
datas += collect_data_files("qdarkstyle")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=["packaging/hooks"],
    runtime_hooks=[],
    excludes=excluded,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# UN SOLO ARCHIVO: todo (scripts + binarios + datos) va dentro del .exe.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SchematicBuq",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon="resources/icons/app.ico" if os.path.exists("resources/icons/app.ico") else None,
)
