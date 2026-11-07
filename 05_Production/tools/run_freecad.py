# -*- coding: utf-8 -*-
"""Startet qualify_laser.py und qualify_print.py in freecadcmd.
Aufruf:  freecadcmd 05_Production/tools/run_freecad.py   (Staging: Umgebungsvariable WORTUHR_STAGE, Standard ./stage)"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STAGE = os.environ.get("WORTUHR_STAGE", os.path.join(ROOT, "stage"))
os.makedirs(STAGE, exist_ok=True)
for s in ("qualify_laser.py", "qualify_print.py"):
    g = {"STAGE": STAGE, "ROOT": ROOT, "__name__": "__main__"}
    exec(open(os.path.join(HERE, s), encoding="utf-8").read(), g)
print("FREECAD QUALIFIKATION FERTIG")
