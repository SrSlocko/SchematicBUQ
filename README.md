# SchematicBuq 🔎🧩

Buscador inteligente de esquemáticos con **visor integrado**, **base de conocimiento de electrónica**
y **organización por aparato**. Hecho para reparación y estudio: busca un componente, entiende qué
hace, sigue sus conexiones y recibe recomendaciones prácticas.

---

## ✨ ¿Qué hace?

- **Busca cualquier componente** por su designador: `R46`, `C12`, `U5`, `Q3`, `D1`, `F1`…
  También por valor: `10k`, `100uF`, `4.7k`, `1N4007`.
- **Te dice el valor** aunque el esquemático sea un PDF escaneado, una foto o un netlist.
- **Te dice el tipo**: reconoce la nomenclatura electrónica (R = resistencia, C = condensador,
  L = bobina, D = diodo, Q = transistor, U/IC = circuito integrado, F = fusible, Y = cristal…).
- **Te explica la función** de cada tipo, sus síntomas típicos y cómo diagnosticarlo.
- **Visor integrado del esquemático** que abre el PDF en la página exacta y **resalta en rojo**
  dónde está el componente que buscaste.
- **Sigue la línea del esquemático**: si cargas un netlist, muestra a qué nodos pertenece el
  componente y qué otros componentes están conectados (con un clic saltas a ellos).
- **Organiza tus esquemáticos** en una carpeta con el nombre del aparato (p. ej. `Ampeg B2R`,
  `Fuente ATX 500W`) para búsquedas más rápidas.
- **Importa PDF desde una URL** directamente.
- **Recomendaciones reales de reparación**, p. ej.: si se quema un fusible, no basta cambiarlo —
  hay que encontrar la causa aguas abajo.

## 🗂️ Formatos soportados

| Formato | Extensiones | Detección |
|---|---|---|
| PDF con texto | `.pdf` | alta precisión |
| PDF escaneado | `.pdf` | OCR automático (Tesseract) |
| Imágenes | `.png .jpg .jpeg .bmp .tif .tiff` | OCR |
| Netlists SPICE | `.net .cir .sp .txt` | precisión total (incluye conexiones) |
| Netlist KiCad | `.net` | precisión total (incluye conexiones) |
| KiCad | `.kicad_sch .kicad_sym .sch` | esquemáticos |
| EasyEDA | `.json` | esquemáticos |
| Altium | `.schdoc .pcbdoc` | esquemáticos |

## 🚀 Instalación

### 1) Dependencias de Python
```bash
pip install -r requirements.txt
```

### 2) OCR (para escaneos e imágenes)
Instala **Tesseract** y el programa lo detecta solo:
- Windows: `winget install UB-Mannheim.TesseractOCR`
- Linux: `sudo apt install tesseract-ocr`
- macOS: `brew install tesseract`

> Los idiomas `spa` y `eng` ya se incluyen en `data/tessdata` (186 MB aprox. no, son ~6 MB).
> Si instalas Tesseract en otra ruta, edita `config.json` (se crea al primer arranque).

## ▶️ Uso

```bash
python main.py
```
o doble clic en **`run.bat`** (Windows).

### Flujo típico
1. **Añadir carpeta o archivos** con tus esquemáticos. Si añades una carpeta, se registra
   automáticamente un aparato con el nombre de esa carpeta.
2. Pulsa **⚙️ Indexar**. (Con muchos PDF escaneados puede tardar: el OCR es lento.)
3. Escribe el componente, p. ej. `R46`, y pulsa **Buscar**.
4. Selecciona el resultado:
   - Pestaña **🔗 Conexiones**: a qué nodos y componentes está conectado.
   - Pestaña **📚 Nomenclatura y diagnóstico**: qué hace y cómo revisarlo.
5. **Doble clic** en el resultado → se abre el **visor** en la página exacta con el componente
   **resaltado**.

### Importar desde internet
Botón **🌐 Importar PDF (URL)** → pega el enlace directo a un PDF.

## 🧠 Ejemplos de recomendaciones incluidas
- **F (fusible) quemado**: no lo cambies sin buscar la causa (diodos, transistores,
  condensadores electrolíticos aguas abajo).
- **C (electrolítico) hinchado o con fuga**: causa muy común de fallos en fuentes conmutadas.
- **Fuente que no arranca**: revisar fusible → puente rectificador → condensador de filtro.
- **Falla intermitente**: conectores, soldaduras frías, condensadores electrolíticos.

## 🛠️ Estructura del proyecto
```
SchematicBuq/
├─ main.py                 # punto de entrada
├─ run.bat / run.sh        # lanzadores
├─ requirements.txt
├─ data/
│  ├─ nomenclature_es.json # base de conocimiento (nomenclatura + diagnóstico)
│  ├─ tessdata/            # idiomas OCR (spa, eng)
│  └─ esquematicos/        # esquemáticos organizados por aparato
├─ database/
│  ├─ device_db.py         # registro de aparatos
│  └─ nomenclature_db.py
├─ gui/
│  ├─ app.py               # ventana principal
│  └─ widgets/             # visor PDF, paneles de nomenclatura y conexiones
├─ resources/icons/app.ico
├─ tests/                  # pruebas
└─ utils/                  # parsers y utilidades
```

## ⚠️ Notas
- El OCR no es perfecto: en escaneos de baja calidad puede leer mal algún valor.
  Cuanto mejor sea el escaneo, mejor el resultado.
- Para conexiones (seguir la línea) necesitas un netlist (`.net`, `.cir`) o el netlist de KiCad.
- El primer indexado de PDF escaneados puede tardar; después las búsquedas son instantáneas.
- Si ocurre un error inesperado, la aplicación **no se cierra**: muestra un aviso y
  guarda el detalle en `logs/error.log`.

## 🧪 Pruebas (desarrollo)
Para comprobar que todo sigue funcionando tras un cambio:

```bash
python tests/_runall.py            # batería rápida (no reanaliza los PDF)
python tests/_runall.py _divtest   # solo las pruebas que contengan ese texto
```

La configuración se puede aislar con la variable de entorno
`SCHEMATICBUQ_CONFIG` (ruta a un `config.json` alternativo), útil para pruebas
sin tocar la configuración del usuario.
