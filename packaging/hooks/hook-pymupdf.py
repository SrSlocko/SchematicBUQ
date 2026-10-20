# Hook de PyInstaller para PyMuPDF: fuerza el alias `fitz` y evita que se
# analicen los submódulos opcionales pesados (layout/onnx, pymupdf4llm).
hiddenimports = ["fitz", "pymupdf"]
excludedimports = [
    "pymupdf.layout",
    "pymupdf.layout.onnx",
    "pymupdf4llm",
    "onnxruntime",
]
