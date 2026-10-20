#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base de conocimiento de DIAGNÓSTICO y MEDICIÓN por tipo de componente.

Contenido (en español) pensado para reparación real:
  * Usos típicos del componente en el circuito.
  * Prueba con multímetro (modo, pasos y lecturas esperadas).
  * Detección de CORTO CIRCUITO (cómo confirmarlo con el polímetro).
  * Fallos típicos (firma en el multímetro, causa y solución).
  * Guía por síntoma y avisos de seguridad.

Los valores "esperados" se calculan a partir del valor real del componente
cuando el programa lo conoce (p. ej. R28 = 10k -> debe medir ~10 kΩ).
"""
from utils.component_symbols import (
    parse_resistance, format_ohms, parse_farads, format_farads, capacitor_code,
)

# ----------------------------------------------------------------------------
# Utilidades de medición
# ----------------------------------------------------------------------------

def led_forward_voltage(color_text):
    t = (color_text or "").lower()
    if "infrarroj" in t or t.strip() in ("ir", "ir1"):
        return "1,0–1,6 V"
    if "rojo" in t or "red" in t:
        return "1,6–2,2 V"
    if "amarill" in t or "yellow" in t or "ambar" in t or "ámbar" in t or "naranja" in t:
        return "1,8–2,4 V"
    if "verde" in t or "green" in t:
        return "1,9–2,6 V"
    if "azul" in t or "blue" in t:
        return "2,6–3,4 V"
    if "blanc" in t or "white" in t or "uv" in t:
        return "2,8–3,6 V"
    return "1,6–3,4 V según color (rojo ≈1,8 V · azul/blanco ≈3,0 V)"


def _fmt(v):
    return format_ohms(v)


def expected_readings(kind, value=""):
    """Devuelve la lista de líneas de 'lecturas esperadas' según tipo y valor."""
    out = []
    val = (value or "").strip()

    if kind in ("resistor", "resistor_network", "thermistor", "varistor"):
        ohms = parse_resistance(val)
        if ohms:
            out.append(f"Valor nominal: <b>{_fmt(ohms)}</b>")
            out.append(f"Con el componente BUENO debe medir ≈ {_fmt(ohms)} "
                       f"(±5 %: {_fmt(ohms*0.95)} a {_fmt(ohms*1.05)})")
            out.append("Medido EN EL CIRCUITO suele salir MÁS BAJO (caminos en "
                       "paralelo). Nunca debe salir más alto que el nominal.")
        else:
            out.append("Valor no determinado: mide y compara con el esquema.")
        out.append("<b>En corto:</b> 0 Ω – 1 Ω (o pitido fijo en continuidad).")
        out.append("<b>Abierta:</b> O.L. / ∞ (no pita, sin lectura).")

    elif kind in ("capacitor", "filter"):
        f = parse_farads(val)
        code = capacitor_code(val)
        if f:
            out.append(f"Capacidad nominal: <b>{format_farads(f)}</b>")
        if code:
            out.append(f"Marcaje grabado (3 cifras): <b>{code}</b>")
        out.append("En modo Ω: la lectura debe subir de 0 hacia ∞ mientras carga "
                   "(condensador bueno).")
        out.append("Cerámico/plástico en corto: 0 Ω fijo. Con capacímetro: "
                   "capacidad dentro de ±20 %.")
        out.append("El multímetro simple NO detecta pérdida de capacidad: usa "
                   "un capacímetro o sustitúyelo por uno nuevo.")

    elif kind == "electrolytic":
        f = parse_farads(val)
        if f:
            out.append(f"Capacidad nominal: <b>{format_farads(f)}</b> (±20 %)")
        out.append("Bueno: en Ω la lectura sube al cargar; ESR baja (< 1 Ω en "
                   "condensadores de fuente).")
        out.append("<b>En corto (muy común):</b> 0 Ω en ambos sentidos y/o "
                   "cuerpo abombado, con fuga o reventado por arriba.")
        out.append("Seco/agotado: mide capacidad muy baja o ESR alta; el equipo "
                   "arranca mal o zumba.")

    elif kind in ("inductor", "ferrite"):
        out.append("Bueno: continuidad franca entre extremos (0,1–2 Ω en "
                   "bobinas pequeñas; decenas de Ω en chokes).")
        out.append("<b>Abierta:</b> O.L. (hilo roto) — la más común.")
        out.append("<b>En corto entre espiras:</b> la continuidad es correcta "
                   "pero el inductor recalienta y pierde función.")
        out.append("A masa/carcasa debe dar ∞ (aislamiento).")

    elif kind in ("diode", "zener", "tvs"):
        out.append("Modo DIODO (↔): en directo debe caer <b>0,4–0,7 V</b> "
                   "(Si) o 0,15–0,4 V (Schottky).")
        out.append("En inverso: <b>O.L.</b> (no conduce).")
        out.append("<b>En corto:</b> 0,000 V en los DOS sentidos.")
        out.append("<b>Abierto:</b> O.L. en los dos sentidos.")
        if kind == "zener" and val:
            out.append(f"Zener: en inverso con fuente y resistencia serie debe "
                       f"estabilizar en su tensión Zener ({val}).")

    elif kind == "bridge":
        out.append("Puente de 4 diodos. Modo DIODO entre '+' y '–': debe caer "
                   "<b>0,9–1,1 V</b> (dos uniones en serie).")
        out.append("Entre '~' y '+', y entre '~' y '–': caída ~0,5 V en un "
                   "sentido y O.L. en el otro.")
        out.append("<b>En corto:</b> ~0 V entre '+' y '–' en los DOS sentidos "
                   "(causa típica de fusible fundido).")
        out.append("<b>Rama abierta:</b> O.L. en una de las cuatro uniones "
                   "(rectifica a media onda y zumba).")

    elif kind == "led":
        out.append(f"Modo DIODO: en directo cae <b>{led_forward_voltage(val)}</b> "
                   "y muchos multímetros lo encienden débilmente.")
        out.append("En inverso: O.L.")
        out.append("<b>En corto:</b> 0 V en ambos sentidos (raro). "
                   "<b>Abierto:</b> O.L. en ambos (lo habitual al quemarse).")

    elif kind == "transistor":
        out.append("Un BJT son DOS diodos: base-emisor y base-colector.")
        out.append("Base→Emisor y Base→Colector: caen <b>0,5–0,7 V</b> (NPN: "
                   "positivo en la base).")
        out.append("Colector↔Emisor: <b>O.L.</b> en ambos sentidos.")
        out.append("<b>En corto (fallo típico):</b> 0 V entre C-E o entre B-E → "
                   "sustituir.")

    elif kind == "fet":
        out.append("Gate↔Source y Gate↔Drain: deben dar <b>O.L.</b> (muy alta "
                   "impedancia). Si dan continuidad → MOSFET destruido.")
        out.append("Drain↔Source: aparece el <b>diodo de cuerpo</b> (~0,4–0,6 V) "
                   "en un sentido y O.L. en el otro.")
        out.append("<b>En corto (fallo típico):</b> D-S en 0 Ω y/o G-S en 0 Ω.")

    elif kind in ("ic", "power"):
        out.append("Mide la resistencia entre el pin de alimentación (VCC/VDD) y "
                   "GND: debe ser de <b>cientos de Ω a varios kΩ</b>, NO 0 Ω.")
        out.append("Si VCC–GND da ~0 Ω → el IC (o un condensador de desacoplo "
                   "asociado) está en corto.")
        out.append("Ideal: comparar cada pin con GND contra un IC nuevo/bueno "
                   "(mismo modelo).")
        out.append("Revisa también la tensión de alimentación en el pin "
                   "correspondiente antes de condenar el chip.")

    elif kind in ("connector", "terminal", "jumper", "testpoint", "wire"):
        out.append("Bueno: continuidad franca (< 1 Ω) de un extremo al otro.")
        out.append("Sucio/oxidado: lectura alta e inestable o intermitente.")
        out.append("<b>Abierto / falso contacto:</b> O.L. o saltos al mover el "
                   "cable (muy típico en conectores).")

    elif kind == "switch":
        out.append("Abierto (reposo): O.L. entre contactos.")
        out.append("Cerrado (pulsado): 0 Ω (pitido de continuidad).")
        out.append("Si cerrado no da 0 Ω → contactos sucios/quemados "
                   "(el fallo más habitual).")

    elif kind == "fuse":
        out.append("Bueno: continuidad, ≈ 0 Ω.")
        out.append("<b>Fundido:</b> O.L. Comprueba el cristal/vidrio a contraluz.")
        out.append("¡NUNCA lo puentees con alambre! Busca primero la causa "
                   "(corto aguas abajo).")

    elif kind == "relay":
        out.append("Bobina: mide su resistencia (p. ej. 12 V ≈ 400 Ω; "
                   "24 V ≈ 1–2 kΩ). O.L. = bobina abierta.")
        out.append("Contactos en reposo: COM-NC = 0 Ω, COM-NO = O.L.")
        out.append("Al excitar la bobina debe oírse un clic y conmutar. "
                   "Contactos quemados = resistencia alta o pegados.")

    elif kind == "transformer":
        out.append("Continuidad en cada devanado (primario y secundario). "
                   "O.L. = devanado abierto (hilo cortado).")
        out.append("Entre primario y secundario, y a carcasa: debe dar "
                   "<b>O.L.</b> (aislamiento). Continuidad = derivación a masa.")
        out.append("Olor a quemado o barniz oscuro = bobina degradada.")

    elif kind in ("crystal", "ferrite"):
        out.append("En Ω debe ser <b>O.L.</b> (muy alta impedancia), ambos "
                   "sentidos.")
        out.append("No se puede verificar con un multímetro normal: usa "
                   "osciloscopio/frecuencímetro para ver si oscila.")
        out.append("Revisa los dos condensadores de carga asociados.")

    elif kind == "potentiometer":
        out.append("Entre extremos: resistencia total nominal.")
        out.append("Entre extremo y terminal central: sube/baja de 0 al total "
                   "AL GIRAR, de forma continua y sin saltos.")
        out.append("Saltos, 0 Ω fijo o O.L. en las puntas = pista rota/sucia.")

    elif kind == "speaker":
        out.append("Mide en Ω entre los dos terminales: debe dar algo MENOS que "
                   "su impedancia (altavoz de 8 Ω → ≈ 6–7 Ω en continua).")
        out.append("<b>En corto:</b> 0 Ω. <b>Abierto:</b> O.L.")
        out.append("Roznido con la mano = bobina descentrada.")

    elif kind in ("motor", "solenoid", "generator"):
        out.append("Mide la resistencia del devanado (típicamente unos pocos Ω "
                   "a decenas de Ω; no 0 Ω ni O.L.).")
        out.append("<b>Abierto:</b> O.L. <b>En corto:</b> 0 Ω o consumo enorme.")

    elif kind == "battery":
        out.append("Mide tensión en VDC: debe dar el nominal (1,5 / 3,7 / 9 / "
                   "12 V…).")
        out.append("Bajo carga no debe caer bruscamente; si cae, está agotada.")
        out.append("Revisa que no esté en corto (0 V y caliente).")

    else:
        out.append("Valor no determinado: mide y compara con el esquemático.")

    return out


# ----------------------------------------------------------------------------
# Perfiles de diagnóstico por tipo
# ----------------------------------------------------------------------------
# Cada perfil: uses, test{mode,steps}, short{steps, rows[(estado,lectura,qué significa)]},
# faults[(fallo, síntoma, firma_multímetro, causa)],
# symptoms{síntoma:[comprobaciones]}, safety[]

def _p(**kw):
    base = {"uses": [], "test": {"mode": "Ω (ohmios)", "steps": []},
            "short": {"steps": [], "rows": []}, "faults": [],
            "symptoms": {}, "safety": []}
    base.update(kw)
    return base


PROFILES = {
    "resistor": _p(
        uses=[
            "Limitar la corriente de un LED, transistor o circuito integrado.",
            "Formar divisores de tensión (referencias, polarización).",
            "Pull-up / pull-down en microcontroladores y buses.",
            "Carga y descarga de condensadores (constantes RC, temporizadores).",
            "Sensor de corriente (resistor shunt) midiendo la caída de tensión.",
        ],
        test={"mode": "Ω (ohmios), circuito DESENERGIZADO",
              "steps": [
                  "Apunta la placa (mide en el circuito primero).",
                  "Selecciona la escala de Ω más cercana al valor (o autorango).",
                  "Toca los extremos de la resistencia con las puntas.",
                  "Compara con el valor del esquema/código de colores.",
              ]},
        short={"steps": [
                   "Pon el multímetro en CONTINUIDAD (🔔) o en Ω mínimo.",
                   "Mide entre los dos terminales de la resistencia.",
                   "Une un extremo a masa y mide la resistencia del circuito a "
                   "masa desde el otro extremo: si es ~0 Ω, hay un corto en la red.",
               ],
               "rows": [
                   ("Bueno", "≈ valor ±5 %", "Funciona correctamente."),
                   ("En corto", "0 Ω – 1 Ω, pitido fijo", "Sustituir: la resistencia "
                    "ha perdido su valor (o hay un corto en la red, comprobar)."),
                   ("Abierto", "O.L. / ∞", "Sustituir: se rompió el cuerpo (típico "
                    "por sobrecarga o golpe)."),
               ]},
        faults=[
            ("Abierta (hilo roto)", "Sin señal / tensión correcta", "O.L. entre extremos",
             "Sobrecarga, golpe o quemadura. Se ve oscura o agrietada."),
            ("Desvalorizada", "Valores fuera de rango, ruido", "Mide muy por encima/abajo",
             "Calor excesivo (se carboniza) o sobrecarga. Sustituir."),
            ("Soldadura fría", "Intermitente al moverse", "Varía al mover la placa",
             "Temperatura de soldadura baja. Resoldar."),
        ],
        symptoms={
            "Tensión incorrecta en un punto": [
                "Comprueba la resistencia del punto anterior y posterior.",
                "Verifica el divisor de tensión (usa la pestaña Divisor).",
                "Revisa condensadores en paralelo (pueden falsear la lectura).",
            ],
            "Componente que no enciende": [
                "Mide la resistencia en serie que alimenta ese elemento (LED/transistor).",
                "Busca entre 0 Ω y O.L. para descartar la resistencia como causa.",
            ],
        },
        safety=["Trabaja SIEMPRE con el equipo desenchufado y condensadores "
                "descargados antes de medir Ω/continuidad."],
    ),

    "capacitor": _p(
        uses=[
            "Desacoplo/Filtrado de alimentación (suelen ir junto a cada chip).",
            "Acoplamiento de señal AC bloqueando la componente continua.",
            "Temporización y osciladores (con resistencias).",
            "Filtro de ruido y supresión de interferencias EMI.",
            "Arranque de motores (condensadores de marcha/arranque).",
        ],
        test={"mode": "Ω (carga) + Capac ímetro / ESR",
              "steps": [
                  "Descarga el condensador (une sus patas con una resistencia de "
                  "1 kΩ) para no dañar el instrumento.",
                  "Modo Ω: la lectura debe SUBIR de 0 hacia ∞ (se está cargando).",
                  "Con un capacímetro: mide la capacidad y compárala con el marcaje "
                  "(tolerancia ±10–20 %).",
                  "Con ESR-metro (recomendado): mide en el circuito para detectar "
                  "condensadores secos.",
              ]},
        short={"steps": [
                   "Pon el multímetro en Ω mínimo o continuidad.",
                   "Mide entre los terminales del condensador (descargado).",
                   "Si la lectura queda FIJA en 0 Ω y no sube, está en corto.",
               ],
               "rows": [
                   ("Bueno", "Sube de 0 a ∞ (carga)", "Se carga correctamente."),
                   ("En corto", "0 Ω fijo, pitido continuo", "Sustituir de inmediato: "
                    "es causa habitual de fusible quemado."),
                   ("Seco / pérdida", "Capacidad baja o ESR alta", "El equipo arranca "
                    "mal, zumba o falla en caliente. Sustituir."),
               ]},
        faults=[
            ("En corto (corto entre placas)", "El equipo no arranca / funde fusible",
             "0 Ω fijo", "Dieléctrico perforado por sobrevoltaje. Muy común en las "
             "fuentes y en los condensadores 'X/Y' de red."),
            ("Pérdida de capacidad", "Ruido, fallo al calentar, arranque difícil",
             "Capacidad baja", "Envejecimiento. Sustituir por uno del mismo valor "
             "y tensión o superior."),
            ("Fuga (derivación)", "Consumo excesivo, calentamiento",
             "Resistencia finita pero baja", "Aislamiento degradado."),
        ],
        symptoms={
            "Ruido o zumbido en audio": [
                "Revisa los condensadores de filtrado cerca de la fuente.",
                "Mide/comprueba por sustitución los cerámicos de desacoplo.",
            ],
            "Fusible que se quema": [
                "Mide el condensador grande de filtrado en modo Ω: si da 0 Ω, es el culpable.",
                "Revisa los 'X' (entre fase y neutro) y 'Y' (a tierra).",
            ],
        },
        safety=["Descarga siempre los condensadores grandes: pueden guardar "
                "tensión peligrosa incluso desenchufados."],
    ),

    "electrolytic": _p(
        uses=[
            "Filtrado principal en fuentes de alimentación (gran capacidad).",
            "Desacoplo y reserva de energía en amplificadores de potencia.",
            "Temporización larga y acoplamiento en audio.",
        ],
        test={"mode": "Ω (carga) + Capac ímetro / ESR",
              "steps": [
                  "Descarga el condensador (¡ojo con la tensión!).",
                  "Respeta la POLARIDAD: positivo (+) y negativo (franja blanca).",
                  "Modo Ω: debe cargar (subir la lectura).",
                  "Ideal: capacímetro/ESR-metro para ver capacidad y ESR.",
              ]},
        short={"steps": [
                   "Inspección visual: abombado por arriba, fuga de líquido, "
                   "fleje/cruz de venteo abierto.",
                   "Mide en Ω respetando polaridad: si da 0 Ω fijo → en corto.",
               ],
               "rows": [
                   ("Bueno", "Carga y ESR baja", "Correcto."),
                   ("En corto", "0 Ω, abombado", "Sustituir: causa nº1 de fallos en "
                    "fuentes conmutadas."),
                   ("Seco", "Capacidad muy baja / ESR alta", "Sustituir."),
                   ("Invertido", "Se calienta y revienta", "Montar SIEMPRE con la "
                    "polaridad correcta."),
               ]},
        faults=[
            ("En corto", "Fusible fundido / sin arranque", "0 Ω", "Dieléctrico roto."),
            ("Agotado (seco)", "Arranca a la 2ª, zumbido, imagen con ondulación",
             "Capacidad baja / ESR alta", "Evaporación del electrolito con el tiempo."),
            ("Invertido", "Reventón / olor", "0 Ω / abombado", "Montaje al revés."),
        ],
        symptoms={
            "Arranca a la segunda o zumba": [
                "Sospecha de electro líticos secos junto al conmutador/regulador.",
                "Sustitúyelos por igual valor y tensión ≥ a la original.",
            ],
        },
        safety=["Muy peligrosos cargados: descárgalos con una resistencia antes "
                "de tocarlos."],
    ),

    "diode": _p(
        uses=[
            "Rectificación (pasa a continua): fuentes, cargadores.",
            "Protección contra inversión de polaridad.",
            "Diodo de libre circulación (flyback) en relés y motores.",
            "Detección/demodulación de señal.",
        ],
        test={"mode": "🔔 / →| (modo diodo)",
              "steps": [
                  "Pon el multímetro en MODO DIODO (símbolo →|).",
                  "Punta roja (+) al ánodo, negra (–) al cátodo (la franja).",
                  "Debe caer 0,4–0,7 V (Si) o 0,15–0,4 V (Schottky).",
                  "Invierte las puntas: debe dar O.L.",
              ]},
        short={"steps": [
                   "Mide en modo diodo en AMBOS sentidos.",
                   "Si da 0,000 V (o casi) en los dos sentidos → en corto.",
                   "Si da O.L. en los dos sentidos → abierto.",
               ],
               "rows": [
                   ("Bueno", "0,4–0,7 V directo / O.L. inverso", "Correcto."),
                   ("En corto", "~0 V en ambos sentidos", "Sustituir: causa habitual "
                    "de fusible quemado."),
                   ("Abierto", "O.L. en ambos sentidos", "Sustituir."),
               ]},
        faults=[
            ("En corto", "Fusible fundido, tensión baja", "~0 V bidireccional",
             "Sobrecorriente o transitorio."),
            ("Abierto", "Sin rectificación / no carga", "O.L. bidireccional",
             "Sobrecorriente, golpe o fatiga."),
            ("Con fugas", "Tensión baja, calentamiento", "Caída baja pero conduce "
             "algo en inverso", "Degradación térmica."),
        ],
        symptoms={
            "No carga / tensión baja": [
                "Comprueba los diodos/puente de la fuente en modo diodo.",
                "Revisa el diodo en paralelo a relés o motores.",
            ],
        },
    ),

    "zener": _p(
        uses=[
            "Regulación de tensión (referencia simple).",
            "Protección contra sobrevoltaje (recorta picos).",
            "Limitador/sujetador de señal.",
        ],
        test={"mode": "🔔 / →| (modo diodo) + fuente",
              "steps": [
                  "En modo diodo, en DIRECTA cae 0,6–0,7 V.",
                  "En INVERSA: O.L. con el multímetro (necesita > la Vz para "
                  "conducir).",
                  "Para verificar Vz: fuente + resistencia serie (~1 kΩ) y mide "
                  "la tensión en el Zener (debe estabilizar en su Vz).",
              ]},
        short={"steps": [
                   "Mide en modo diodo ambos sentidos.",
                   "0 V en los dos sentidos = en corto (fallo más común del Zener).",
               ],
               "rows": [
                   ("Bueno", "0,6–0,7 V directo / O.L. inverso", "Correcto."),
                   ("En corto", "~0 V ambos sentidos", "Sustituir: deja pasar todo "
                    "y suele quemar lo de aguas abajo."),
                   ("Desvalorizado", "Vz desplazada", "Sustituir por el mismo Vz."),
               ]},
        faults=[
            ("En corto", "Sobretensión aguas abajo, equipo no arranca", "~0 V",
             "Sobrecorriente sostenida."),
            ("Abierto", "Pierde regulación, sobretensión", "O.L. inverso incluso "
             "con tensión", "Sobrecarga."),
        ],
        symptoms={
            "Tensión de referencia incorrecta": [
                "Mide la Vz con fuente y resistencia serie.",
                "Revisa que no esté montado al revés.",
            ],
        },
    ),

    "tvs": _p(
        uses=[
            "Protección de líneas contra picos (ESD, transitorios).",
            "Sujeción en entradas de alimentación y datos.",
        ],
        test={"mode": "🔔 / →| (modo diodo)", "steps": [
            "Modo diodo: en directa cae ~0,6–0,7 V.",
            "En inversa debe dar O.L. (o la tensión de sujeción si es TVS de "
            "dos direcciones).",
        ]},
        short={"steps": ["Mide en ambos sentidos: 0 V bidireccional = en corto."],
               "rows": [
                   ("Bueno", "Cae en un sentido / O.L. en otro", "Correcto."),
                   ("En corto", "~0 V ambos", "Sustituir."),
               ]},
        faults=[("En corto", "Fusible quemado / línea a 0 V", "~0 V",
                 "Absorbió un pico y se sacrificó (a veces hay que buscar la "
                 "causa del pico).")],
    ),

    "led": _p(
        uses=[
            "Indicador de encendido/estado.",
            "Iluminación (LED de potencia con disipador).",
            "Optoacopladores y displays.",
        ],
        test={"mode": "🔔 / →| (modo diodo)", "steps": [
            "Modo diodo: rojo al ánodo (+), negro al cátodo (–).",
            "Debe caer según el color y encender débilmente.",
            "Invierte: O.L.",
        ]},
        short={"steps": ["Modo diodo ambos sentidos: 0 V = en corto; O.L. en ambos "
                         "= abierto (típico quemado)."],
               "rows": [
                   ("Bueno", "Cae y enciende débil", "Correcto."),
                   ("Abierto", "O.L. ambos", "Sustituir (lo más común)."),
                   ("En corto", "~0 V ambos", "Sustituir."),
               ]},
        faults=[
            ("Abierto/ quemado", "No ilumina", "O.L.", "Sobrecorriente o sin "
             "resistencia limitadora."),
            ("Degradado", "Luz débil / parpadea", "Caída alta", "Fatiga térmica."),
        ],
        symptoms={
            "Indicador que no enciende": [
                "Mide la tensión en el LED y en su resistencia limitadora.",
                "Comprueba la polaridad y la resistencia en serie.",
            ],
        },
    ),

    "bridge": _p(
        uses=["Rectificar la tensión de red (AC→DC) en fuentes de alimentación."],
        test={"mode": "🔔 / →| (modo diodo)", "steps": [
            "Modo diodo entre '+' y '–': debe caer ~0,9–1,1 V (dos uniones).",
            "Entre '~' y '+', y entre '~' y '–': caída ~0,5 V en un sentido y "
            "O.L. en el otro.",
            "Cualquier combinación con 0 V = diodo interno en corto.",
        ]},
        short={"steps": [
            "Modo diodo entre '+' y '–' en AMBOS sentidos.",
            "Si da 0 V en los dos sentidos, está en corto (causa nº1 de fusible "
            "fundido).",
        ],
               "rows": [
                   ("Bueno", "~1 V en un sentido / O.L. en otro", "Correcto."),
                   ("En corto", "~0 V bidireccional", "Sustituir el puente."),
                   ("Una rama abierta", "Rectifica a media onda, zumba", "Caída "
                    "O.L. en una rama", "Sustituir el puente."),
               ]},
        faults=[
            ("En corto", "Fusible fundido, sin DC", "0 V '+'–'–'", "Pico de red o "
             "condensador de filtrado en corto."),
            ("Rama abierta", "Zumbido, tensión baja", "O.L. en una rama",
             "Sobrecorriente."),
        ],
        symptoms={"Fusible quemado + sin alimentación": [
            "Mide el puente en modo diodo '+'–'–'.",
            "Revisa el condensador de filtrado (puede estar en corto y dañar el puente).",
        ]},
    ),

    "transistor": _p(
        uses=[
            "Amplificación de señal (audio, sensores).",
            "Conmutación: activa relés, LED, motores desde señales débiles.",
            "Regulación y osciladores.",
        ],
        test={"mode": "🔔 / →| (modo diodo)",
              "steps": [
                  "Identifica B, C, E (según el encapsulado/datasheet).",
                  "NPN: rojo en la BASE. Negro en E y en C: deben caer 0,5–0,7 V.",
                  "C↔E en ambos sentidos: O.L. (no debe conducir).",
                  "En PNP se invierte la polaridad de las puntas.",
              ]},
        short={"steps": [
                   "Mide C-E: en un transistor bueno da O.L.",
                   "Si C-E da 0 Ω (o pitido), está en corto → sustituir.",
                   "Mide B-E y B-C: si dan 0 V, la unión está en corto.",
                   "Con el circuito alimentado, mide Vbe (debe ser ~0,6–0,7 V) y Vce "
                   "(pequeño si conduce, ≈ Vcc si está cortado).",
               ],
               "rows": [
                   ("Bueno", "B-E y B-C ≈ 0,6 V / C-E O.L.", "Correcto."),
                   ("En corto C-E", "0 Ω y suele calentar", "Sustituir: entra en "
                    "cortocircuito y el equipo queda 'pegado'."),
                   ("En corto B-E", "0 V base-emisor", "Sustituir."),
                   ("Abierto", "O.L. en todo", "Sustituir."),
               ]},
        faults=[
            ("Cortocircuito C-E", "Carga siempre activada / sin control",
             "0 Ω C-E, se calienta", "Sobrecorriente. Revisa la carga y la base."),
            ("Base abierta", "No conmuta", "O.L. B-E y B-C", "Sobrecarga."),
            ("Fugas", "Falso disparo / consumo en reposo", "Conduce débil C-E",
             "Fatiga térmica."),
        ],
        symptoms={
            "Salida siempre activa (no se apaga)": [
                "Mide C-E: probablemente en corto.",
                "Revisa el diodo flyback si gobierna un relé/bobina.",
            ],
            "No conmuta": [
                "Mide Vbe en funcionamiento (~0,6–0,7 V). Si no llega, el "
                "problema está en el mando (resistencia/IC).",
                "Comprueba la conexión de emisor a masa.",
            ],
        },
        safety=["Los transistores de potencia pueden estar calientes y tener "
                "tensión: descarga y deja enfriar antes de medir."],
    ),

    "fet": _p(
        uses=[
            "Conmutación de potencia (fuentes conmutadas, drivers).",
            "Control de motores y cargas desde lógica.",
            "Amplificación de alta impedancia.",
        ],
        test={"mode": "🔔 / →| (modo diodo)", "steps": [
            "G-S y G-D deben dar O.L. (puerta aislada).",
            "D-S: diodo de cuerpo (~0,4–0,6 V) en un sentido y O.L. en el otro.",
            "En el circuito: mide Vgs y Vds para ver si conmuta.",
        ]},
        short={"steps": [
                   "G-S en 0 Ω → MOSFET destruido (fallo muy típico).",
                   "D-S en 0 Ω → en corto, casi siempre consecuencia de la avería "
                   "de la etapa.",
               ],
               "rows": [
                   ("Bueno", "G aislada / D-S diodo de cuerpo", "Correcto."),
                   ("En corto G-S", "0 Ω G-S", "Sustituir y revisar el driver de "
                    "puerta."),
                   ("En corto D-S", "0 Ω D-S", "Sustituir y buscar la causa "
                    "(sobrecarga, condensador en corto)."),
               ]},
        faults=[
            ("En corto", "Fuente no arranca / fusible o resistencia de arranque "
             "quemada", "0 Ω", "Sobretensión en puerta o sobrecorriente."),
            ("Puerta abierta", "No conmuta", "O.L. G", "Descarga electrostática "
             "(ESD)."),
        ],
        symptoms={"Fuente conmutada que no arranca": [
            "Mide el MOSFET principal D-S: suele estar en corto tras un pico.",
            "Cambia también la resistencia de arranque y revisa el driver.",
        ]},
        safety=["Sensible a estática: usa pulsera antiestática y no toques la "
                "puerta."],
    ),

    "ic": _p(
        uses=[
            "Amplificadores operacionales, comparadores, reguladores.",
            "Microcontroladores, memoria y lógica.",
            "Drivers, temporizadores (555), conversores.",
        ],
        test={"mode": "Ω (VCC-GND) + VDC en funcionamiento", "steps": [
            "Con la placa SIN tensión, mide la resistencia entre el pin de "
            "alimentación y GND.",
            "Debe ser de cientos de Ω a varios kΩ; nunca 0 Ω.",
            "Con tensión, mide que la alimentación llegue al pin correcto.",
            "Compara las tensiones de cada pin con un IC bueno si es posible.",
        ]},
        short={"steps": [
                   "Mide VCC–GND en Ω: ~0 Ω = corto (el IC o un condensador de "
                   "desacoplo asociado).",
                   "Levanta el condensador de desacoplo y vuelve a medir para "
                   "separar culpables.",
                   "Revisa temperatura: un IC en corto suele calentar mucho.",
               ],
               "rows": [
                   ("Bueno", "VCC-GND cientos de Ω–kΩ", "Correcto."),
                   ("En corto", "~0 Ω VCC-GND", "Sustituir tras descartar un "
                    "condensador de desacoplo."),
                   ("Sin alimentación", "0 V en el pin", "No es el IC: falla la "
                    "alimentación/pista."),
               ]},
        faults=[
            ("En corto interno", "Equipo muerto / consumo alto", "~0 Ω VCC-GND",
             "Pico de tensión o sobrecorriente."),
            ("Salida dañada", "Función parcial", "Tensión de salida pegada a Vcc "
             "o GND", "Cortocircuito externo en su salida."),
            ("Sobrecalentamiento", "Falla al calentar", "Temperatura alta",
             "Sobrecarga o disipación insuficiente."),
        ],
        symptoms={
            "Equipo completamente muerto": [
                "Mide alimentación en los pines del IC principal.",
                "Comprueba VCC-GND en Ω por si está en corto.",
                "Sigue el rastro del corto (a menudo un condensador cerámico).",
            ],
            "Falla en caliente": [
                "Usa frío localizado (spray) sobre el IC sospechoso.",
                "Repasa soldaduras del encapsulado (BGA/QFN).",
            ],
        },
        safety=["Usa pulsera antiestática y revisa la tensión antes de condenar "
                "el chip."],
    ),

    "connector": _p(
        uses=["Unir placas, cables y periféricos.", "Alimentación y señal entre "
              "etapas."],
        test={"mode": "🔔 (continuidad)", "steps": [
            "Pon continuidad. Debe pitar de extremo a extremo.",
            "Mueve/agita el cable mientras mides: no debe cortarse (falso "
            "contacto).",
        ]},
        short={"steps": [
                   "Mira si hay pines puenteados por estaño, suciedad o doblados.",
                   "Comprueba continuidad entre pines que NO deben unirse "
                   "(cortocircuito entre contactos).",
               ],
               "rows": [
                   ("Bueno", "0 Ω entre extremos correctos", "Correcto."),
                   ("Falso contacto", "Lectura inestable al mover", "Limpiar o "
                    "sustituir el conector."),
                   ("En corto", "0 Ω entre pines distintos", "Limpiar estaño/patillas."),
               ]},
        faults=[
            ("Soldadura fría", "Intermitente", "Varía al tocar", "Resoldar."),
            ("Contacto oxidado", "Señal débil/inestable", "Resistencia alta",
             "Limpiar con alcohol/limpiacontactos."),
            ("Pin doblado/junto", "Corto entre señales", "0 Ω entre pines",
             "Enderezar/separar pines."),
        ],
        symptoms={"Funciona a veces": [
            "Mueve cada conector mientras observas; resoldar el sospechoso.",
            "Revisa el cable por si está roto por dentro.",
        ]},
    ),

    "switch": _p(
        uses=["Encendido/apagado.", "Selección de modo o entrada.", "Pulsadores "
              "de control."],
        test={"mode": "🔔 (continuidad)", "steps": [
            "Con el pulsador en reposo: O.L. entre contactos.",
            "Al pulsar/cerrar: debe dar 0 Ω (pitido).",
            "Prueba varias veces: no debe fallar ni chisporrotear.",
        ]},
        short={"steps": ["Si da 0 Ω SIEMPRE (también en reposo), está pegado/en "
                         "corto.",
                         "Si nunca da 0 Ω al pulsar, contactos sucios/abiertos."],
               "rows": [
                   ("Bueno", "O.L. reposo / 0 Ω pulsado", "Correcto."),
                   ("Pegado", "0 Ω siempre", "Sustituir."),
                   ("Sucio", "Resistencia alta al pulsar", "Limpiar o sustituir."),
               ]},
        faults=[("Contactos quemados", "No enciende / intermitente",
                 "Alta resistencia al cerrar", "Arco eléctrico. Sustituir.")],
        symptoms={"No enciende": ["Puentea temporalmente el interruptor para "
                                  "descartarlo.",
                                  "Mide continuidad al cerrar."]},
    ),

    "fuse": _p(
        uses=["Proteger el circuito contra sobrecorriente (se sacrifica él)."],
        test={"mode": "🔔 (continuidad)", "steps": [
            "Sin tensión, pon continuidad entre los dos extremos.",
            "Debe pitar (≈0 Ω). Si no pita, está fundido.",
            "Míralo a contraluz: hilo cortado o vidrio ennegrecido.",
        ]},
        short={"steps": [
                   "Un fusible fundido NO es la avería, es el SÍNTOMA.",
                   "Antes de cambiarlo, mide la resistencia del circuito "
                   "aguas abajo: puente rectificador, condensador de filtrado y "
                   "transistor de conmutación suelen estar en corto.",
                   "Si el nuevo fusible vuelve a fundir, hay un corto: encuéntralo.",
               ],
               "rows": [
                   ("Bueno", "0 Ω / pitido", "Correcto."),
                   ("Fundido", "O.L.", "NO puentear: buscar y reparar el corto."),
               ]},
        faults=[("Fundido", "Sin alimentación", "O.L.", "Corto aguas abajo o pico.")],
        safety=["NUNCA sustituyas por uno de mayor amperaje ni lo puentees con "
                "alambre: puedes provocar un incendio."],
    ),

    "inductor": _p(
        uses=["Filtrado en fuentes (choke).", "Almacenamiento de energía en "
              "conmutadas.", "Supresión de EMI.", "Sintonía/oscilación."],
        test={"mode": "🔔 (continuidad)", "steps": [
            "Continuidad entre extremos (pocos Ω).",
            "Debe dar O.L. entre el devanado y cualquier parte metálica.",
        ]},
        short={"steps": [
                   "Mide continuidad: si da O.L., hilo abierto.",
                   "Un inductor rara vez se cortocircuita a masa; si hay "
                   "continuidad a la carcasa, está derivado.",
               ],
               "rows": [
                   ("Bueno", "0,1–decenas Ω", "Correcto."),
                   ("Abierto", "O.L.", "Sustituir."),
                   ("Derivado a masa", "Continuidad a carcasa", "Sustituir."),
               ]},
        faults=[("Abierto", "Fuente no funciona / no filtra", "O.L.",
                 "Sobrecorriente o golpe.")],
        symptoms={"Fuente conmutada muerta": ["Mide el inductor de salida en "
                                              "continuidad.",
                                              "Revisa si está quemado/oscuro."]},
    ),

    "transformer": _p(
        uses=["Reducción/elevación de tensión.", "Aislamiento galvánico.",
              "Adaptación de impedancias."],
        test={"mode": "🔔 (continuidad)", "steps": [
            "Continuidad en cada devanado por separado.",
            "Entre devanados y a carcasa: O.L. (aislamiento).",
        ]},
        short={"steps": [
                   "Continuidad entre primario y secundario = derivación (corto "
                   "entre bobinas).",
                   "Continuidad a la carcasa = derivación a masa.",
               ],
               "rows": [
                   ("Bueno", "Continuidad en cada bobina / O.L. entre ellas",
                    "Correcto."),
                   ("Abierto", "O.L. en una bobina", "Sustituir."),
                   ("Derivado", "Continuidad entre bobinas/carcasa", "Sustituir: "
                    "peligro de choque."),
               ]},
        faults=[("Devanado abierto", "Sin tensión secundaria", "O.L.",
                 "Sobrecorriente o fusible térmico interno."),
                ("Aislamiento roto", "Chispazos/olor", "Continuidad a masa",
                 "Envejecimiento. Sustituir.")],
        safety=["Trabaja desenchufado: los transformadores de red guardan "
                "tensión peligrosa."],
    ),

    "crystal": _p(
        uses=["Reloj de microcontroladores.", "Base de tiempo.", "Osciladores "
              "de RF."],
        test={"mode": "Osciloscopio / frecuencímetro", "steps": [
            "El multímetro normal da O.L. en ambos sentidos (es normal).",
            "Comprueba con osciloscopio si oscila a su frecuencia.",
            "Revisa los condensadores de carga a cada lado.",
        ]},
        short={"steps": ["Si con el multímetro da continuidad (0 Ω), está roto "
                         "(cristal partido).",
                         "Prueba por sustitución con uno igual."],
               "rows": [
                   ("Bueno", "O.L. + oscila", "Correcto."),
                   ("Roto", "0 Ω o no oscila", "Sustituir."),
               ]},
        faults=[("Roto/partido", "El equipo no arranca", "0 Ω", "Golpe."),
                ("No oscila", "MCU sin arrancar", "O.L. sin señal en "
                 "osciloscopio", "Cristal o condensadores de carga.")],
        symptoms={"Microcontrolador que no arranca": [
            "Verifica que el cristal oscila.",
            "Revisa los condensadores de carga y las soldaduras.",
        ]},
    ),

    "potentiometer": _p(
        uses=["Ajuste de volumen/brillo.", "Referencia ajustable.",
              "Trimmers de calibración."],
        test={"mode": "Ω (ohmios)", "steps": [
            "Entre extremos: resistencia total.",
            "Entre extremo y cursor: cambia de 0 al total al girar, progresivo.",
        ]},
        short={"steps": ["Si entre extremos da 0 Ω → en corto.",
                         "Si al girar hay saltos o no llega a 0 y al máximo → "
                         "pista sucia/rota."],
               "rows": [
                   ("Bueno", "Cambia progresivo al girar", "Correcto."),
                   ("En corto", "0 Ω entre extremos", "Sustituir."),
                   ("Pista rota", "Saltos / cortes al girar", "Limpiar o "
                    "sustituir (típico: ruido al mover el volumen)."),
               ]},
        faults=[("Pista desgastada", "Ruido/crujido al girar", "Saltos de "
                 "resistencia", "Desgaste. Sustituir.")],
        symptoms={"Ruido al mover el volumen": ["Limpia/o cambia el "
                                                 "potenciómetro.",
                                                 "Revisa sus soldaduras."]},
    ),

    "varistor": _p(
        uses=["Protección contra picos de red (MOV).", "Sujeción de "
              "transitorios."],
        test={"mode": "Ω", "steps": [
            "En reposo debe dar MUY alta resistencia (normalmente O.L.).",
            "Mídelo fuera del circuito para asegurar.",
        ]},
        short={"steps": ["Si da 0 Ω o baja, se ha sacrificado por un pico → "
                         "sustituir.",
                         "Suele ir acompañado de fusible fundido."],
               "rows": [
                   ("Bueno", "Alta resistencia/O.L.", "Correcto."),
                   ("En corto", "0 Ω / baja", "Sustituir (protegió al equipo)."),
               ]},
        faults=[("En corto", "Fusible fundido", "0 Ω", "Absorbió un pico de red. "
                 "Sustituir y revisar la red eléctrica.")],
    ),

    "thermistor": _p(
        uses=["Limitador de corriente de arranque (NTC).", "Sensor de "
              "temperatura.", "Protección térmica (PTC)."],
        test={"mode": "Ω + calor", "steps": [
            "Mide su resistencia a temperatura ambiente.",
            "NTC: al calentarlo, la resistencia BAJA. PTC: SUBE.",
        ]},
        short={"steps": ["0 Ω = en corto (no protege). O.L. = abierto "
                         "(típico si se quemó)."],
               "rows": [
                   ("Bueno", "Cambia con la temperatura", "Correcto."),
                   ("Abierto", "O.L.", "Sustituir (fallo muy común)."),
                   ("En corto", "0 Ω", "Sustituir."),
               ]},
        faults=[("Abierto", "No arranca en frío / fuente muerta", "O.L.",
                 "Sobrecorriente en el arranque.")],
    ),

    "speaker": _p(
        uses=["Reproducir sonido.", "Carga de salida de amplificadores."],
        test={"mode": "Ω", "steps": [
            "Mide entre los terminales: algo MENOS que su impedancia.",
            "Altavoz de 8 Ω → lectura ≈ 6–7 Ω.",
        ]},
        short={"steps": ["0 Ω = bobina en corto.", "O.L. = bobina abierta "
                         "(silbido/rotura)."],
               "rows": [
                   ("Bueno", "≈ 0,8 × impedancia", "Correcto."),
                   ("En corto", "0 Ω", "Sustituir."),
                   ("Abierto", "O.L.", "Sustituir (típico por exceso de "
                    "potencia)."),
               ]},
        faults=[("Bobina abierta", "Sin sonido", "O.L.", "Exceso de potencia."),
                ("Rozamiento", "Distorsión/crujido", "Lectura correcta",
                 "Bobina descentrada.")],
    ),

    "relay": _p(
        uses=["Conmutar cargas de potencia con señal débil.", "Aislamiento "
              "galvánico."],
        test={"mode": "Ω + VDC", "steps": [
            "Mide la bobina (según su tensión: 5 V≈70 Ω, 12 V≈400 Ω, 24 V≈1–2 kΩ).",
            "Contactos en reposo: COM-NC ≈ 0 Ω, COM-NO O.L.",
            "Alimenta la bobina y comprueba que conmuta (clic).",
        ]},
        short={"steps": ["Bobina 0 Ω = en corto. O.L. = abierta (típico).",
                         "Contactos pegados: COM-NO y COM-NC dan 0 Ω a la vez."],
               "rows": [
                   ("Bueno", "Bobina ~su valor / contactos conmutan", "Correcto."),
                   ("Bobina abierta", "O.L.", "Sustituir."),
                   ("Contactos pegados", "0 Ω ambos", "Sustituir (carga queda "
                    "siempre encendida)."),
               ]},
        faults=[("Contactos quemados", "Carga no enciende o queda encendida",
                 "Alta resistencia/pegados", "Arco eléctrico. Revisa el diodo "
                 "flyback.")],
    ),

    "battery": _p(
        uses=["Alimentar el equipo o la memoria."],
        test={"mode": "VDC", "steps": [
            "Mide la tensión en los terminales.",
            "Compara con el nominal (1,5 / 3,7 / 9 / 12 V).",
            "Mide bajo carga: no debe caer bruscamente.",
        ]},
        short={"steps": ["Tensión 0 V y caliente = posible corto interno.",
                         "Revisa la polaridad y que no haya inversión."],
               "rows": [
                   ("Bueno", "≈ nominal y estable", "Correcto."),
                   ("Agotada", "Muy por debajo del nominal", "Sustituir."),
                   ("En corto", "0 V y caliente", "Sustituir."),
               ]},
        faults=[("Agotada", "No enciende/pierde memoria", "Tensión baja",
                 "Uso prolongado.")],
        safety=["Respeta la polaridad y no cortocircuites los terminales."],
    ),

    "motor": _p(
        uses=["Accionamiento mecánico."],
        test={"mode": "Ω + amperios", "steps": [
            "Mide la resistencia del devanado (pocos Ω a decenas).",
            "Comprueba el consumo en funcionamiento.",
        ]},
        short={"steps": ["0 Ω = en corto. O.L. = escobillas/bobina abiertas."],
               "rows": [
                   ("Bueno", "Resistencia moderada", "Correcto."),
                   ("Abierto", "O.L.", "Sustituir/revisar escobillas."),
                   ("En corto", "0 Ω", "Sustituir."),
               ]},
        faults=[("Escobillas gastadas", "No gira/zumba", "O.L./alto",
                 "Desgaste.")],
    ),

    "solenoid": _p(
        uses=["Accionar válvulas/cerraduras."],
        test={"mode": "Ω", "steps": ["Mide la bobina (típicamente decenas de Ω "
                                     "a unos pocos kΩ)."]},
        short={"steps": ["0 Ω = en corto. O.L. = bobina abierta."],
               "rows": [("Bueno", "Resistencia esperada", "Correcto."),
                        ("Abierto", "O.L.", "Sustituir.")]},
        faults=[("Bobina abierta", "No acciona", "O.L.", "Sobrecorriente.")],
    ),

    "antenna": _p(
        uses=["Captar/emitir señal de radio."],
        test={"mode": "Continuidad / comprobación física", "steps": [
            "Muchas antenas dan circuito abierto en continua (es normal).",
            "Revisa conexiones y que no esté partida.",
        ]},
        short={"steps": ["Continuidad a masa donde no debe = derivación."],
               "rows": [("Bueno", "Según diseño", "Correcto."),
                        ("Rota", "Conector suelto", "Reparar conexión.")]},
    ),

    "generic": _p(
        uses=["Componente identificado por su designador; revisa el esquema "
              "para conocer su función exacta."],
        test={"mode": "Ω / continuidad", "steps": [
            "Mide continuidad y resistencia entre sus terminales.",
            "Compara con el esquema y con un componente igual bueno.",
        ]},
        short={"steps": ["Pon continuidad: 0 Ω fijo puede indicar corto, pero "
                         "comprueba que no sea normal en el circuito (una bobina "
                         "sí da 0 Ω).",
                         "Compara con un componente idéntico bueno."],
               "rows": [("Dudoso", "—", "Contrasta con el esquema/datasheet.")]},
        faults=[("Degradado/ quemado", "Varios síntomas", "Fuera de valor",
                 "Sustituir por otro igual.")],
    ),
}


# ----------------------------------------------------------------------------
# Guía general por síntoma (cuando no hay un componente concreto)
# ----------------------------------------------------------------------------
GENERAL_SYMPTOMS = {
    "No enciende / no da señal de vida": [
        "Revisa la alimentación: fusible, interruptor y cable de red.",
        "Mide tensiones de la fuente (primario y secundario).",
        "Comprueba el puente rectificador y el condensador de filtrado en modo "
        "diodo/Ω (busca cortos).",
        "Mide el transistor/ MOSFET de conmutación: suele estar en corto.",
    ],
    "Fusible que se quema al instante": [
        "NO cambies el fusible sin buscar la causa.",
        "Mide en Ω/diodo: puente rectificador, condensador de filtrado, "
        "transistor de conmutación y diodos.",
        "Revisa el varistor/MOV de entrada (puede haberse sacrificado).",
    ],
    "Se calienta en exceso": [
        "Localiza el componente caliente (o usa frío localizado).",
        "Comprueba transistores, reguladores y resistencias de potencia.",
        "Verifica disipadores, pasta térmica y ventilación.",
    ],
    "Funciona a veces / intermitente": [
        "Mueve conectores y cables mientras mides (falso contacto).",
        "Resuelda soldaduras frías (sobre todo en conectores y componentes "
        "grandes).",
        "Sospecha de condensadores electrolíticos secos.",
    ],
    "Ruido / zumbido / hum": [
        "Revisa los condensadores de filtrado de la fuente.",
        "Comprueba la masa y los blindajes.",
    ],
    "Sonido distorsionado": [
        "Revisa la alimentación simétrica (±V) de los amplificadores.",
        "Comprueba condensadores de acoplo y transistores de salida.",
    ],
    "No da la tensión correcta": [
        "Mide la etapa de regulación (Zener, regulador IC, divisor).",
        "Comprueba realimentación y condensadores asociados.",
    ],
}


# ----------------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------------

def get_profile(kind):
    return PROFILES.get(kind) or PROFILES["generic"]


def diagnose(kind, value="", designator="", type_name=""):
    """Devuelve un dict con todo el contenido de diagnóstico ya resuelto.

    {'designator','kind','name','uses','test','short','faults',
     'expected','symptoms','safety'}
    """
    prof = get_profile(kind)
    return {
        "designator": (designator or "").upper(),
        "kind": kind,
        "type_name": type_name or "",
        "uses": prof.get("uses", []),
        "test": prof.get("test", {}),
        "short": prof.get("short", {}),
        "faults": prof.get("faults", []),
        "expected": expected_readings(kind, value),
        "symptoms": prof.get("symptoms", {}),
        "safety": prof.get("safety", []),
    }
