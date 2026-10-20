# Hook de PyInstaller: impide que se empaquete onnxruntime.
# PyMuPDF >= 1.26 puede arrastrar onnxruntime (para pymupdf.layout/pymupdf4llm),
# que es enorme y no lo usamos: además hace caer el subproceso aislado de
# PyInstaller en Windows. Aquí lo marcamos como excluido siempre.
excludedimports = [
    "onnxruntime",
    "onnxruntime.transformers",
    "onnxruntime.capi",
]
