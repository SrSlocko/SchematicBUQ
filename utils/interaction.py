#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Motor de INTERACCIÓN entre componentes.

Responde a la pregunta «¿cómo se comporta este componente y con quién
interactúa?» sin necesidad de un netlist perfecto:

  * Si el proyecto trae netlist (KiCad, EasyEDA, Altium, .net/.cir), usa las
    NETS reales del circuito.
  * Si sólo hay PDF/imagen (lo normal en un esquemático escaneado), agrupa los
    componentes por PROXIMIDAD en la hoja y lo avisa claramente: son vecinos
    «de zona», no una conexión eléctrica confirmada.

Con esos vecinos:

  * Describe el PAPEL del componente en el circuito.
  * Explica CÓMO SE COMPORTA (fórmulas y comportamiento real).
  * Detecta SUBCIRCUITOS TÍPICOS (divisor, filtro RC, desacoplo, flyback...).
  * Explica QUÉ PASA EN EL CIRCUITO si el componente falla (efecto sobre los
    vecinos, no sólo la lectura del multímetro).
"""
import os
import re

from utils.component_symbols import component_kind, kind_name

# ---------------------------------------------------------------------------
# Rol del componente dentro del circuito (para qué está ahí y cómo se relaciona)
# ---------------------------------------------------------------------------
KIND_ROLE = {
    "resistor": "Limita la corriente y reparte tensiones. Rara vez trabaja solo: "
                "junto a otro componente fija la corriente (limitadora), el "
                "voltaje de un punto (divisor/polarización) o mantiene un nivel "
                "(pull-up / pull-down).",
    "resistor_network": "Varias resistencias en un mismo encapsulado. Cada "
                        "elemento hace de limitador o de pull-up/pull-down; si "
                        "falla un canal, sólo afecta a esa señal.",
    "potentiometer": "Resistencia ajustable: actúa como divisor variable. El "
                     "cursor entrega una fracción de la tensión, así que controla "
                     "directamente el nivel (volumen, brillo, referencia).",
    "thermistor": "Su resistencia depende de la temperatura. Forma parte de un "
                  "divisor con otra resistencia: el cambio de tensión en el punto "
                  "medio es lo que lee el circuito (sensor).",
    "varistor": "En reposo es casi un aislante; si la tensión sube demasiado se "
                "vuelve conductor y se sacrifica, salvando al resto del circuito.",
    "capacitor": "Almacena carga. Bloquea la continua y deja pasar los cambios "
                 "(AC): acopla señal entre etapas y desacopla el ruido de la "
                 "alimentación a masa. Con una resistencia forma temporizadores.",
    "electrolytic": "Condensador de gran capacidad, con polaridad. Mantiene la "
                    "tensión de alimentación estable (filtrado) y reserva energía "
                    "para los picos de corriente de la etapa.",
    "inductor": "Almacena energía en un campo magnético. Se opone a los cambios "
                "de corriente: filtra y suaviza. Con un condensador forma un "
                "filtro (fuentes conmutadas).",
    "ferrite": "Absorbe el ruido de alta frecuencia (EMI) sin afectar a la "
               "continua. Va en serie con la alimentación o con una señal.",
    "filter": "Filtro pasivo: deja pasar unas frecuencias y atenúa otras, "
              "separando la señal útil del ruido.",
    "crystal": "Marca el ritmo: vibra a una frecuencia fija. Con dos "
               "condensadores de carga forma el oscilador que da los ciclos al "
               "circuito (reloj, base de tiempo).",
    "diode": "Válvula de un solo sentido: conduce en un sentido (ánodo→cátodo) y "
             "bloquea en el otro. Rectifica, protege de inversiones de polaridad "
             "y absorbe los picos de las bobinas (flyback).",
    "zener": "Conduce en inverso cuando la tensión llega a su valor Zener: fija "
             "una tensión de referencia y recorta sobretensiones.",
    "tvs": "Diodo de protección: en condiciones normales no hace nada y, ante un "
           "pico, conduce y lo absorbe para no dañar lo que protege.",
    "led": "Emite luz al paso de corriente. Necesita SIEMPRE una resistencia en "
           "serie que limite la corriente; suele indicar el estado del equipo.",
    "photodiode": "Convierte luz en corriente. Suele acompañar a un amplificador "
                  "que traduce esa corriente en tensión.",
    "bridge": "Cuatro diodos que convierten la corriente alterna en continua. "
              "Es la entrada de la fuente de alimentación.",
    "transistor": "Amplifica o conmuta. Con una corriente pequeña en la base "
                  "controla una corriente mayor entre colector y emisor: es el "
                  "interruptor/amplificador de la etapa.",
    "fet": "Se controla por tensión en la puerta (gate) y conmuta corrientes "
           "grandes con muy poca pérdida: el conmutador típico de las fuentes.",
    "ic": "Realiza la función principal de la etapa (amplificar, regular, "
          "temporizar, procesar). Depende de su alimentación y de los "
          "condensadores de desacoplo que tiene al lado.",
    "connector": "Une etapas, placas o el exterior. Es el punto donde se "
                 "inyecta la señal o la alimentación.",
    "switch": "Corta o desvía la señal/alimentación. En reposo abre, al "
              "accionarlo cierra el camino.",
    "jumper": "Une dos puntos de forma fija o seleccionable (configuración).",
    "fuse": "Protege de sobrecorriente: si la corriente sube demasiado, se funde "
            "y corta la alimentación para evitar males mayores.",
    "battery": "Fuente de energía del equipo; marca la tensión de referencia del "
               "circuito.",
    "motor": "Carga electromecánica: convierte la corriente en movimiento. Suele "
             "llevar un diodo y un condensador de supresión al lado.",
    "solenoid": "Bobina que acciona algo mecánicamente al recibir corriente.",
    "speaker": "Carga de salida del amplificador: convierte la señal eléctrica en "
               "sonido.",
    "transformer": "Sube o baja la tensión de red y aísla el equipo. Es la "
                   "primera etapa de la fuente.",
    "power": "Nodo de alimentación del equipo: reparte la tensión a todas las "
             "etapas.",
    "generic": "Componente identificado por su designador; revisa el esquema "
               "para conocer su función exacta en la etapa.",
}

# ---------------------------------------------------------------------------
# Cómo se comporta (comportamiento real, con la fórmula si aplica)
# ---------------------------------------------------------------------------
KIND_BEHAVIOR = {
    "resistor": [
        "Ley de Ohm: <b>V = I · R</b>. Si la tensión entre sus extremos es fija, "
        "por ella pasa siempre la misma corriente.",
        "En un divisor con otra resistencia: <b>Vout = Vin · R2 / (R1 + R2)</b>.",
        "Al medir en el circuito (Ω) suele dar MENOS que su valor, porque puede "
        "haber caminos en paralelo.",
    ],
    "resistor_network": [
        "Cada elemento se comporta como una resistencia independiente.",
        "Se usa para agrupar muchas pull-up/pull-down en un solo encapsulado "
        "(buses, memorias, displays).",
    ],
    "potentiometer": [
        "Entre extremos: siempre la resistencia total.",
        "El cursor entrega una tensión proporcional a su posición: al girar, la "
        "tensión de salida sube o baja de forma continua.",
    ],
    "thermistor": [
        "NTC: al calentarse, su resistencia <b>baja</b>. PTC: <b>sube</b>.",
        "Forma un divisor con otra resistencia; el circuito lee el cambio de "
        "tensión del punto medio para saber la temperatura.",
    ],
    "varistor": [
        "Por debajo de su tensión de disparo se comporta como un aislante.",
        "Ante un pico conduce y lo absorbe; soporta pocos picos antes de fallar.",
    ],
    "capacitor": [
        "Al aplicarle tensión se carga (la lectura de Ω sube hacia ∞) y se "
        "descarga cuando desaparece.",
        "Se opone a los cambios bruscos: <b>bloquea la continua y deja pasar la "
        "corriente alterna</b>.",
        "Con una resistencia: tiempo de carga ≈ <b>τ = R · C</b>.",
    ],
    "electrolytic": [
        "Igual que un condensador, pero con más capacidad y con polaridad "
        "(si se invierte, se calienta y revienta).",
        "Mantiene la tensión de la fuente «llena» entre los picos de corriente.",
    ],
    "inductor": [
        "Se opone a los cambios de corriente: la suaviza.",
        "Con un condensador forma un filtro LC que elimina el rizado de las "
        "fuentes conmutadas.",
    ],
    "ferrite": [
        "Poca resistencia en continua, mucha impedancia en alta frecuencia.",
        "Bloquea el ruido que viaja por el cable sin que la alimentación se caiga.",
    ],
    "filter": [
        "Deja pasar una banda de frecuencias y atenúa el resto.",
        "Su comportamiento depende de los componentes que lo acompañan (R, L, C).",
    ],
    "crystal": [
        "Vibra a una frecuencia muy estable (p. ej. 4 MHz) cuando el circuito "
        "oscila.",
        "Necesita dos condensadores de carga: si se desvalorizan, deja de "
        "arrancar o falla la frecuencia.",
    ],
    "diode": [
        "Directo (ánodo +, cátodo −): conduce y cae 0,4–0,7 V (Si) o "
        "0,15–0,4 V (Schottky).",
        "Inverso: no conduce (O.L.).",
        "En una bobina (relé, motor) absorbe el pico al cortar la corriente: es "
        "el diodo de libre circulación.",
    ],
    "zener": [
        "En directo es un diodo normal.",
        "En inverso empieza a conducir justo en su tensión Zener y mantiene ese "
        "valor: por eso fija la referencia.",
    ],
    "tvs": [
        "Inactivo mientras la tensión es normal (O.L.).",
        "Ante un pico conduce y lo desvía; si el pico es grande, se sacrifica.",
    ],
    "led": [
        "Conduce en directo y emite luz; la caída depende del color "
        "(rojo ≈1,8 V, azul/blanco ≈3,0 V).",
        "La corriente la fija la resistencia en serie: "
        "<b>I ≈ (Valimentación − Vled) / R</b>.",
    ],
    "photodiode": [
        "Genera corriente al recibir luz; en inverso es más lineal.",
        "Su señal es pequeñísima: siempre lleva un amplificador (op-amp/transistor).",
    ],
    "bridge": [
        "Convierte la alterna en continua pulsante (dos diodos conducen en cada "
        "semiciclo).",
        "Después siempre hay un condensador de filtrado que la alisa.",
    ],
    "transistor": [
        "NPN: cuando la base sube ~0,65 V respecto al emisor, empieza a conducir "
        "entre colector y emisor.",
        "Como interruptor: saturado ≈0 V en C-E (conduce); cortado = O.L. (no "
        "conduce).",
        "Como amplificador: una variación pequeña en la base produce una "
        "variación grande en el colector.",
    ],
    "fet": [
        "Conduce entre drenador y surtidor cuando la tensión de puerta supera su "
        "umbral (Vgs).",
        "La puerta consume prácticamente nada: se controla con tensión, no con "
        "corriente.",
        "Al conmutar cargas inductivas lleva un diodo de protección.",
    ],
    "ic": [
        "Hace su función sólo si tiene la alimentación correcta en sus pines.",
        "Consumo y tensión de los pines son la pista para saber si trabaja bien.",
        "Suele llevar un condensador de desacoplo entre VCC y GND muy cerca.",
    ],
    "connector": [
        "Un extremo debe estar unido al otro (pocos Ω).",
        "Es el punto más propenso a falsos contactos: los fallos aparecen al "
        "mover el cable.",
    ],
    "switch": [
        "En reposo abre el circuito (O.L.); al accionarlo cierra (≈0 Ω).",
        "Soporta la corriente de la carga que conmuta; si se quema, se queda "
        "abierto o pegado.",
    ],
    "jumper": [
        "Une dos puntos: siempre continuidad (≈0 Ω).",
        "Se usa para elegir configuración (por eso se quita y se pone).",
    ],
    "fuse": [
        "En condiciones normales es un trozo de cable (≈0 Ω).",
        "Si pasa más corriente de la prevista, el hilo se funde y abre el "
        "circuito: protege al resto.",
    ],
    "battery": [
        "Entrega una tensión que cae un poco al pedirle corriente.",
        "Si la tensión cae mucho bajo carga, está agotada o no puede dar el "
        "consumo de la etapa.",
    ],
    "motor": [
        "Al arrancar pide mucha corriente (pico); en régimen gira más suelto.",
        "Genera picos al apagarse: por eso lleva diodo/condensador de supresión.",
    ],
    "solenoid": [
        "Bobina con mucha inductancia: consume un pico al activar y genera otro "
        "al cortar.",
        "Suele ir con diodo de libre circulación.",
    ],
    "speaker": [
        "Su bobina es casi un cortocircuito para la continua pero una carga para "
        "la señal de audio.",
        "En continua mide algo menos que su impedancia (un 8 Ω ≈ 6–7 Ω).",
    ],
    "transformer": [
        "Transforma la tensión en proporción a su relación de espiras.",
        "Aísla el equipo de la red: primario y secundario NO deben tocarse.",
    ],
    "power": [
        "Reparte la alimentación a todas las etapas.",
        "Su tensión es la referencia de medida de todo el circuito.",
    ],
    "generic": [
        "Comportamiento según su función en la etapa; compáralo con el esquema.",
    ],
}

# ---------------------------------------------------------------------------
# Qué pasa EN EL CIRCUITO si falla (efecto sobre los vecinos)
# ---------------------------------------------------------------------------
KIND_FAILURE_IMPACT = {
    "resistor": [
        ("Se ABRE (hilo roto)", "Corta la corriente en esa rama: el punto se "
         "queda sin tensión o la señal desaparece. Un LED/transistor que "
         "alimentaba deja de funcionar."),
        ("Se pone EN CORTO / baja de valor", "Pasa más corriente de la prevista: "
         "el punto sube de tensión, y el componente siguiente se sobrecalienta."),
        ("Sube de valor", "Se queda 'sin corriente' la rama: el circuito funciona "
         "débil o no arranca."),
    ],
    "capacitor": [
        ("En CORTO", "Pone a 0 V la red donde esté: la alimentación se cae y es "
         "la causa nº1 de un fusible fundido."),
        ("ABIERTO", "Pierde el filtrado/acoplo: aparece ruido, zumbido o la señal "
         "no pasa de una etapa a la siguiente."),
        ("SECO / pierde capacidad", "No filtra bien: el equipo arranca mal, zumba "
         "o falla al calentarse."),
    ],
    "electrolytic": [
        ("En CORTO", "Corta la alimentación (fusible) y puede dañar la etapa."),
        ("SECO / agotado", "Rizado y arranque a la segunda, zumbido, imagen "
         "ondulada."),
    ],
    "inductor": [
        ("ABIERTO", "La etapa no recibe energía: la fuente no arranca o no hay "
         "salida."),
        ("En corto entre espiras", "La continuidad es correcta, pero recalienta y "
         "no filtra."),
    ],
    "diode": [
        ("En CORTO", "Deja pasar en los dos sentidos: suele fundir el fusible y "
         "descargar el condensador de filtrado."),
        ("ABIERTO", "Desaparece la rectificación/protección: media onda, picos no "
         "absorbidos, el relé/motor puede dañar el mando."),
    ],
    "zener": [
        ("En CORTO", "La tensión de referencia se va a 0 V: todo lo que dependía "
         "de ella deja de funcionar."),
        ("ABIERTO", "La tensión de referencia SUBE sin control y puede dañar los "
         "circuitos alimentados."),
    ],
    "led": [
        ("ABIERTO (fundido)", "No ilumina y, si está en serie, corta esa rama."),
    ],
    "transistor": [
        ("En CORTO C-E", "La carga se queda SIEMPRE activada (aunque no la "
         "mandes)."),
        ("ABIERTO / base abierta", "Nunca conmuta: la carga nunca se activa."),
    ],
    "fet": [
        ("En CORTO D-S", "La fuente no arranca o se queda con tensión siempre "
         "presente; suele quemar la resistencia de arranque y el fusible."),
        ("Puerta abierta", "No conmuta nunca."),
    ],
    "ic": [
        ("En CORTO (VCC-GND)", "Se lleva la alimentación a 0 V y calienta: "
         "avería generalizada de la etapa."),
        ("Salida dañada", "La señal de salida se queda pegada a VCC o a GND."),
    ],
    "fuse": [
        ("FUNDIDO", "Quita la alimentación a todo lo que cuelga de él. OJO: es un "
         "síntoma, no la avería; hay un corto aguas abajo."),
    ],
    "connector": [
        ("Falso contacto", "Todo lo que pasa por él falla de forma intermitente al "
         "mover el equipo."),
    ],
    "transformer": [
        ("Devanado abierto", "No hay tensión en el secundario (nada funciona)."),
        ("Derivación a masa", "Peligro de choque; normalmente funde el fusible."),
    ],
    "speaker": [
        ("Bobina abierta", "Silencio total con el amplificador funcionando."),
        ("En corto", "Fuerza al amplificador y lo puede dañar."),
    ],
    "relay": [
        ("Contactos pegados", "La carga se queda encendida aunque no la mandes."),
        ("Bobina abierta", "La carga nunca se activa."),
    ],
}

# ---------------------------------------------------------------------------
# Relación entre el componente elegido y cada vecino
# ---------------------------------------------------------------------------
_RELATION_BY_PAIR = {
    frozenset({"resistor", "capacitor"}):
        "Forma con él un filtro RC o una temporización (τ = R·C).",
    frozenset({"resistor", "electrolytic"}):
        "La resistencia limita la corriente de carga del electrolítico.",
    frozenset({"resistor", "led"}):
        "Es la resistencia que limita la corriente del LED.",
    frozenset({"resistor", "zener"}):
        "La resistencia limita la corriente y el Zener fija la tensión.",
    frozenset({"resistor", "diode"}):
        "Juntos polarizan o protegen ese punto.",
    frozenset({"resistor", "transistor"}):
        "Fija la corriente/base del transistor (polarización).",
    frozenset({"resistor", "fet"}):
        "Fija la tensión de puerta del MOSFET (polarización).",
    frozenset({"resistor", "resistor"}):
        "Pueden formar un DIVISOR de tensión (Vout = Vin·R2/(R1+R2)).",
    frozenset({"resistor", "ic"}):
        "Referencia/pull-up o limitadora de un pin del integrado.",
    frozenset({"capacitor", "ic"}):
        "Es el condensador de DESACOPLO de la alimentación del integrado.",
    frozenset({"electrolytic", "ic"}):
        "Reserva/desacoplo de energía para el pico de corriente del integrado.",
    frozenset({"capacitor", "inductor"}):
        "Juntos forman un filtro LC que suaviza la tensión.",
    frozenset({"electrolytic", "bridge"}):
        "El electrolítico FILTRA la continua que sale del puente.",
    frozenset({"electrolytic", "transformer"}):
        "Transformador → rectificador → filtrado (fuente de alimentación).",
    frozenset({"capacitor", "transformer"}):
        "Filtrado o supresión de ruido de la etapa de alimentación.",
    frozenset({"capacitor", "crystal"}):
        "Es uno de los condensadores de carga del oscilador.",
    frozenset({"diode", "relay"}):
        "Es el diodo de LIBRE CIRCULACIÓN (flyback) de la bobina del relé.",
    frozenset({"diode", "motor"}):
        "Absorbe el pico de la bobina del motor (flyback).",
    frozenset({"diode", "inductor"}):
        "Protege de los picos de la bobina (flyback).",
    frozenset({"led", "transistor"}):
        "El transistor enciende y apaga el LED (indicador).",
    frozenset({"transistor", "speaker"}):
        "El transistor entrega la potencia al altavoz (etapa de salida).",
    frozenset({"ic", "speaker"}):
        "El integrado es el amplificador que mueve el altavoz.",
    frozenset({"bridge", "transformer"}):
        "El puente rectifica la alterna que entrega el transformador.",
    frozenset({"fuse", "transformer"}):
        "El fusible protege el primario del transformador.",
    frozenset({"fuse", "bridge"}):
        "El fusible protege la entrada; si se funde, mira el puente.",
    frozenset({"transistor", "relay"}):
        "El transistor conmuta la bobina del relé (driver).",
    frozenset({"fet", "transformer"}):
        "El MOSFET conmuta el primario (fuente conmutada).",
    frozenset({"resistor", "potentiometer"}):
        "Ajuste de nivel/referencia junto a la resistencia.",
    frozenset({"capacitor", "resistor_network"}):
        "Filtrado junto a la red de resistencias.",
    frozenset({"connector", "capacitor"}):
        "Condensador de entrada/salida del conector (filtro de línea).",
    frozenset({"switch", "fuse"}):
        "Interruptor y protección de entrada en serie con la alimentación.",
}

# ---------------------------------------------------------------------------
# Subcircuitos típicos
# ---------------------------------------------------------------------------
SUBCIRCUITS = [
    ({"resistor", "capacitor"}, "Filtro / temporizador RC",
     "La resistencia limita la corriente con la que se carga el condensador "
     "(τ = R·C). Sirve para filtrar ruido o para dar un retardo."),
    ({"resistor", "electrolytic"}, "Filtrado o polarización",
     "La resistencia controla la carga del electrolítico; juntos suavizan o "
     "retrasan la tensión de esa rama."),
    ({"resistor", "resistor"}, "Posible divisor de tensión",
     "Dos resistencias reparten la tensión de entrada: "
     "Vout = Vin · R2 / (R1 + R2). Se usa para referencias y polarización."),
    ({"resistor", "led"}, "LED con resistencia limitadora",
     "La resistencia fija la corriente del LED: I ≈ (Valim − Vled) / R. Si la "
     "resistencia se abre, el LED se apaga."),
    ({"resistor", "zener"}, "Referencia de tensión con Zener",
     "La resistencia limita la corriente y el Zener fija una tensión estable."),
    ({"resistor", "transistor"}, "Polarización / driver de transistor",
     "Las resistencias fijan la corriente de base; el transistor amplifica o "
     "conmuta la carga."),
    ({"resistor", "fet"}, "Polarización / driver de MOSFET",
     "La resistencia fija la tensión de puerta y protege la puerta."),
    ({"capacitor", "ic"}, "Desacoplo de alimentación",
     "El condensador absorbe el ruido y los picos de corriente que pide el "
     "integrado. Si se abre, aparecen fallos intermitentes."),
    ({"electrolytic", "bridge"}, "Fuente: rectificación + filtrado",
     "El puente convierte la alterna en continua y el electrolítico la alisa. "
     "Si el condensador está en corto, el fusible se funde."),
    ({"capacitor", "inductor"}, "Filtro LC",
     "La bobina y el condensador eliminan el rizado de la fuente conmutada."),
    ({"capacitor", "crystal"}, "Oscilador con cristal",
     "El cristal marca la frecuencia y los condensadores la ajustan. Si uno se "
     "desvaloriza, el equipo no arranca."),
    ({"diode", "relay"}, "Diodo de libre circulación (flyback)",
     "Absorbe el pico de la bobina al desconectarla y protege al transistor que "
     "la manda."),
    ({"diode", "motor"}, "Supresión de picos del motor",
     "El diodo desvía el pico inductivo del motor."),
    ({"transistor", "speaker"}, "Etapa de salida de audio",
     "El transistor amplifica y entrega la potencia al altavoz."),
    ({"bridge", "transformer"}, "Entrada de fuente lineal",
     "El transformador baja la tensión y el puente la rectifica."),
    ({"fuse", "bridge"}, "Protección de entrada",
     "Si el fusible se funde, mide el puente y el condensador de filtrado: casi "
     "siempre hay un corto ahí."),
    ({"fet", "transformer"}, "Fuente conmutada",
     "El MOSFET conmuta el primario; el transformador transfiere la energía al "
     "secundario con aislamiento."),
    ({"led", "transistor"}, "Indicador controlado",
     "El transistor enciende y apaga el LED según la señal de mando."),
    ({"potentiometer", "resistor"}, "Ajuste de referencia/nivel",
     "El potenciómetro reparte la tensión y la resistencia fija el rango."),
]


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def kind_of(designator, type_name=""):
    return component_kind(designator, type_name or "")


def role_text(kind):
    return KIND_ROLE.get(kind) or KIND_ROLE["generic"]


def behavior_text(kind):
    return KIND_BEHAVIOR.get(kind) or KIND_BEHAVIOR["generic"]


def failure_impact(kind):
    return KIND_FAILURE_IMPACT.get(kind) or []


def relation_text(center_kind, other_kind):
    if not other_kind or center_kind == other_kind:
        pair = frozenset({center_kind})
    else:
        pair = frozenset({center_kind, other_kind})
    for key, txt in _RELATION_BY_PAIR.items():
        if key == pair:
            return txt
    return ""


def detect_subcircuits(center_kind, neighbor_kinds):
    """Subcircuitos típicos que forma el componente con sus vecinos."""
    kinds = set(k for k in neighbor_kinds if k)
    if center_kind:
        kinds.add(center_kind)
    out = []
    for needed, title, text in SUBCIRCUITS:
        if needed.issubset(kinds):
            out.append((title, text))
    return out


# ---------------------------------------------------------------------------
# Vecinos: nets reales o proximidad en la hoja
# ---------------------------------------------------------------------------
def _norm(p):
    try:
        return os.path.normcase(os.path.normpath(os.path.abspath(p)))
    except Exception:
        return (p or "")


def _first_rect(result):
    for rect in (result.rects or []):
        try:
            vals = [float(v) for v in rect]
            if len(vals) >= 4:
                return vals[:4]
        except Exception:
            continue
    return None


def _center(rect):
    return ((rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0)


def neighbors_of(index, designator, file_path="", page=0,
                 max_dist=90.0, limit=16):
    """Devuelve los componentes con los que interactúa.

    Si hay netlist usa las NETS reales; si no, usa la PROXIMIDAD en la hoja.
    Cada vecino: {'designator','value','kind','type_name','net','dist','real'}
    """
    des = (designator or "").upper()
    out = []
    if not des or index is None:
        return out, False

    # --- 1) Nets reales (netlist / CAD) ---
    real = False
    entries = {}
    try:
        nets = index.nets_of(des)
    except Exception:
        nets = []
    if nets:
        real = True
        for net in nets:
            for member in index.connections.get(net, []):
                m = (member or "").upper()
                if not m or m == des:
                    continue
                e = entries.setdefault(m, {"designator": m, "value": "",
                                           "kind": "", "type_name": "",
                                           "nets": [], "dist": None})
                if net not in e["nets"]:
                    e["nets"].append(net)
    if real:
        values = {}
        for r in index.results:
            d = (r.designator or "").upper()
            if d and d not in values:
                values[d] = r
        for m, e in entries.items():
            r = values.get(m)
            if r is not None:
                e["value"] = r.value or ""
                e["type_name"] = r.component_type or ""
                e["kind"] = kind_of(m, r.component_type)
            else:
                e["kind"] = kind_of(m)
            e["net"] = ", ".join(e["nets"][:2])
            out.append(e)
        out.sort(key=lambda e: e["designator"])
        return out[:limit], True

    # --- 2) Proximidad en la hoja (no hay netlist) ---
    target = _norm(file_path)
    center = None
    others = []
    for r in index.results:
        if _norm(r.file_path) != target:
            continue
        if page and r.page != page:
            continue
        rect = _first_rect(r)
        if not rect:
            continue
        d = (r.designator or "").upper()
        if d == des:
            center = rect
            continue
        others.append((r, rect))
    if center is None:
        return out, False

    cx, cy = _center(center)
    ch = max(1.0, center[3] - center[1])
    scored = []
    for r, rect in others:
        ox, oy = _center(rect)
        dx = abs(ox - cx)
        dy = abs(oy - cy)
        dist = (dx * dx + dy * dy) ** 0.5
        # En un esquemático, lo que está en la misma fila (misma línea de
        # señal) interactúa aunque esté un poco más lejos.
        if dy < max(14.0, ch):
            dist *= 0.65
        if dist <= max_dist:
            scored.append((dist, r, rect))
    scored.sort(key=lambda t: t[0])
    for dist, r, rect in scored[:limit]:
        d = (r.designator or "").upper()
        out.append({
            "designator": d,
            "value": r.value or "",
            "type_name": r.component_type or "",
            "kind": kind_of(d, r.component_type),
            "nets": [],
            "net": "misma zona de la hoja",
            "dist": dist,
        })
    return out, False


def build(index, designator, value="", type_name="", file_path="", page=0):
    """Reúne toda la información de interacción para el panel."""
    des = (designator or "").upper()
    kind = kind_of(des, type_name)
    neighbors, real_nets = neighbors_of(index, des, file_path, page)
    return {
        "designator": des,
        "kind": kind,
        "kind_name": kind_name(kind),
        "value": value or "",
        "role": role_text(kind),
        "behavior": behavior_text(kind),
        "impact": failure_impact(kind),
        "neighbors": neighbors,
        "real_nets": real_nets,
        "subcircuits": detect_subcircuits(
            kind, [n.get("kind") for n in neighbors]),
    }
