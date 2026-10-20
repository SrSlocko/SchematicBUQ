# -*- coding: utf-8 -*-
"""Prueba de la calculadora de divisor de tensión."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.widgets.voltage_divider import (VoltageDividerPanel, parse_number,
                                         fmt_ohms)

print("--- parse_number ---")
casos = {"10k": 1e4, "4k7": 4.7e3, "1M": 1e6, "2M2": 2.2e6, "470": 470,
         "0R22": 0.22, "2,2k": 2.2e3, "4.7K": 4.7e3, "220": 220}
ok = True
for txt, esp in casos.items():
    got = parse_number(txt)
    good = got is not None and abs(got - esp) < 1e-6 * max(1, esp)
    ok = ok and good
    print(f"  {txt!r:>8} -> {got}  {'OK' if good else 'MAL (esperado ' + str(esp) + ')'}")

print("\n--- modos ---")
p = VoltageDividerPanel()

# Modo 0: Vout dadas Vin, R1, R2
p.mode.setCurrentIndex(0)
p.ed_vin.setText("40"); p.ed_r1.setText("10k"); p.ed_r2.setText("4k7")
p.calculate()
vout = parse_number(p.ed_vout.text())
esp = 40 * 4700 / 14700
print(f"  Vout = {vout:.4f} V (esperado {esp:.4f})  "
      f"{'OK' if abs(vout - esp) < 1e-3 else 'MAL'}")

# Modo 1: R2 para Vout=12, Vin=40, R1=10k
p.mode.setCurrentIndex(1)
p.ed_vin.setText("40"); p.ed_r1.setText("10k"); p.ed_vout.setText("12")
p.calculate()
r2 = parse_number(p.ed_r2.text())
esp = 10000 * 12 / (40 - 12)
print(f"  R2   = {r2:.2f} ohm (esperado {esp:.2f})  "
      f"{'OK' if abs(r2 - esp) < 1 else 'MAL'}")

# Modo 2: R1 para Vout=12, Vin=40, R2=4k7
p.mode.setCurrentIndex(2)
p.ed_vin.setText("40"); p.ed_r2.setText("4k7"); p.ed_vout.setText("12")
p.calculate()
r1 = parse_number(p.ed_r1.text())
esp = 4700 * (40 - 12) / 12
print(f"  R1   = {r1:.2f} ohm (esperado {esp:.2f})  "
      f"{'OK' if abs(r1 - esp) < 1 else 'MAL'}")

print("\n--- aviso de potencia (R1 grande) ---")
p.mode.setCurrentIndex(0)
p.ed_vin.setText("24"); p.ed_r1.setText("100"); p.ed_r2.setText("100")
p.calculate()
txt = p.result.toPlainText()
print("  contiene aviso de potencia:", "disipa" in txt)
print("  muestra corriente:", "Corriente" in txt)

print("\nRESULTADO GLOBAL:", "TODO OK" if ok else "HAY FALLOS")
