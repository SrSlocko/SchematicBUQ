# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para generar el ejecutable de SchematicBuq.

- En Windows produce `SchematicBuq.exe`.
- En Linux produce un binario `SchematicBuq`.
Los recursos de solo-lectura (iconos, nomenclatura, tessdata) se empaquetan
dentro del ejecutable; los datos del usuario se crean en su carpeta personal.
"""
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden = []
# Colección dirigida: evitamos `collect_submodules` en paquetes que arrastran
# submódulos pesados o problemáticos (p. ej. PyMuPDF -> onnxruntime/pymupdf4llm).
for pkg in ("cv2", "pdfminer", "PIL", "pytesseract", "pyqtgraph", "qdarkstyle"):
    try:
        hidden += collect_submodules(pkg)
    except Exception as exc:  # pragma: no cover - entorno de empaquetado
        print(f"Aviso: no se pudieron recopilar submódulos de {pkg}: {exc}")

# PyMuPDF: solo el paquete principal y su alias `fitz`
hidden += ["fitz", "pymupdf"]

# Submódulos que requieren pantalla, son de ejemplo o rompen el empaquetado.
excluded = [
    "pyqtgraph.examples", "pyqtgraph.opengl", "pyqtgraph.console",
    "pyqtgraph.flowchart", "pyqtgraph.jupyter",
    "tkinter", "matplotlib",
    "PyQt5.QtWebEngineWidgets", "PyQt5.QtQuick", "PyQt5.QtQml",
    # PyMuPDF moderno arrastra onnxruntime/pymupdf4llm que no usamos y que
    # hacen caer el subproceso aislado de PyInstaller.
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
