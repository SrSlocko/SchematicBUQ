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
for pkg in ("cv2", "fitz", "pymupdf", "pdfminer", "PIL", "pytesseract",
            "pyqtgraph", "qdarkstyle"):
    hidden += collect_submodules(pkg)

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
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests", "numpy.tests"],
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
