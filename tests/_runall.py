# -*- coding: utf-8 -*-
"""Ejecuta la batería de pruebas rápidas y resume el resultado.

Uso:  python tests/_runall.py            (todas las pruebas rápidas)
      python tests/_runall.py _divtest  (solo las que contengan ese texto)

Excluye a propósito las pruebas de OCR pesadas (_ocr*, _reindex, _speedtest,
_probe, test_ampeg), que tardan minutos porque reanalizan los PDF reales.
"""
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAPIDAS = [
    "_audit_verify.py", "_audit_edges.py", "_audit_crash.py", "_audit_repro.py",
    "_compviewtest.py", "_diagtest.py", "_dist.py", "_divtest.py",
    "_guitest.py", "_guitest2.py", "_interactiontest.py", "_intergu.py",
    "_multiinteg.py", "_multishot.py", "_multitest.py", "_nomtest.py",
    "_symtest.py", "_visual.py", "_compinteg.py", "_devicestest.py",
    "_finaltest.py", "_flowauto.py", "_pagetest.py", "_viewertest.py",
]

PESADAS = ("_ocr", "_reindex", "_speedtest", "_probe", "test_ampeg", "_r21check")


def main():
    filtro = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [t for t in RAPIDAS if filtro.lower() in t.lower()]
    if not tests:
        print("No hay pruebas que coincidan con", repr(filtro))
        return 1
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    fallos = []
    for t in tests:
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, os.path.join("tests", t)],
                               cwd=BASE, capture_output=True, timeout=180, env=env)
            code = p.returncode
            out = p.stdout.decode("utf-8", "replace")
            err = p.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            code, out, err = "TIMEOUT", "", ""
        dt = time.time() - t0
        malo = (code != 0) or ("REVISAR" in out) or ("FALLA" in out)
        if malo:
            fallos.append(t)
        ultima = [l for l in out.strip().splitlines() if l.strip()]
        ultima = ultima[-1] if ultima else ""
        print(f"  {'FALLO' if malo else 'OK   '} {t:<22} [{dt:5.1f}s] {ultima[:90]}")
        if malo and err:
            print("        " + err.strip().splitlines()[-1][:110])

    print(f"\nRESUMEN: {len(tests) - len(fallos)}/{len(tests)} correctas")
    if fallos:
        print("Fallan:", ", ".join(fallos))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
