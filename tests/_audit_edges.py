# -*- coding: utf-8 -*-
"""Casos límite de la interfaz (entradas vacías, ceros, texto, designadores raros)."""
import os, sys, traceback, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["SCHEMATICBUQ_CONFIG"] = os.path.join(tempfile.mkdtemp(), "config.json")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.widgets.voltage_divider import VoltageDividerPanel, parse_number

fails = []

def case(name, fn):
    try:
        fn()
        print(f"  [ok]    {name}")
    except Exception as e:
        fails.append(name)
        print(f"  [CRASH] {name}: {type(e).__name__}: {e}")
        traceback.print_exc()

print("== Parsing de números ==")
for txt, exp in [("10k", 1e4), ("4k7", 4700.0), ("2M2", 2.2e6), ("470", 470.0),
                 ("0R22", 0.22), ("2,2k", 2200.0), ("", None), ("abc", None),
                 ("1e5", None), ("-5", None), ("100nF", None)]:
    got = parse_number(txt)
    good = (got is None and exp is None) or (got is not None and exp is not None and abs(got - exp) < 1e-6)
    print(f"    {txt!r:8} -> {got} {'OK' if good else 'DIFERENTE (esperado ' + str(exp) + ')'}")

print("\n== Calculadora: entradas límite ==")
dv = VoltageDividerPanel()

def run(mode, vin, r1, r2, vout):
    dv.mode.setCurrentIndex(mode)
    dv.ed_vin.setText(vin); dv.ed_r1.setText(r1)
    dv.ed_r2.setText(r2); dv.ed_vout.setText(vout)
    dv.calculate()

case("modo Vout: todo vacío", lambda: run(0, "", "", "", ""))
case("modo Vout: R1=0", lambda: run(0, "10", "0", "4k7", ""))
case("modo Vout: texto", lambda: run(0, "xx", "yy", "zz", ""))
case("modo R2: normal", lambda: run(1, "40", "10k", "", "12"))
case("modo R2: Vout>Vin", lambda: run(1, "5", "10k", "", "10"))
case("modo R2: Vout vacío", lambda: run(1, "5", "10k", "", ""))
case("modo R1: normal", lambda: run(2, "40", "", "4k7", "12"))
case("modo R1: Vout=0", lambda: run(2, "10", "", "1k", "0"))       # <-- sospechoso
case("modo R1: Vout vacío", lambda: run(2, "10", "", "1k", ""))
case("modo R1: R2=0", lambda: run(2, "10", "", "0", "5"))
case("modo R1: Vout=Vin", lambda: run(2, "10", "", "1k", "10"))
case("Vin=0", lambda: run(0, "0", "1k", "1k", ""))
case("Vin negativo", lambda: run(0, "-10", "1k", "1k", ""))
case("Vin enorme", lambda: run(0, "1e12", "1", "1", ""))

print("\n== Designadores raros en los paneles ==")
from gui.widgets.nomenclature_panel import NomenclaturePanel
from gui.widgets.diagnostic_panel import DiagnosticPanel
from gui.widgets.multimeter_panel import MultimeterPanel
from gui.widgets.component_view import ComponentView
from utils.search_index import SearchIndex

np_, dp, mp, cv = NomenclaturePanel(), DiagnosticPanel(), MultimeterPanel(), ComponentView()
idx = SearchIndex()
for des in ["", "   ", "XYZ99999", "R", "12345", "@#$", "RÃ‰S"]:
    case(f"show_info({des!r})", lambda d=des: np_.show_info(d))
    case(f"diag.show_component({des!r})", lambda d=des: dp.show_component(d, "", ""))
    case(f"multi.show_component({des!r})", lambda d=des: mp.show_component(d, "", ""))
    case(f"comp_view.show_component({des!r})", lambda d=des: cv.show_component(d, "", "", ""))
    case(f"nomen.clear()", lambda: np_.clear())

print("\nRESULTADO:", "TODO OK" if not fails else f"{len(fails)} FALLOS -> {fails}")
sys.exit(0 if not fails else 1)
