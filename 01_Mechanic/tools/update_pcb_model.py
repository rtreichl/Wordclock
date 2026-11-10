# -*- coding: utf-8 -*-
"""Platinen im FreeCAD-Modell aus den aktuellen STEP-Exporten neu aufbauen (freecadcmd update_pcb_model.py).

Quelle: LED-Board_master.step (Q4) und LED-Board_slave.step (Q2, Q1, Q3) aus den freigegebenen Produktionsdaten
(05_Production/05_Platine_JLCPCB). Fuer eine noch nicht freigegebene Platine WORTUHR_STEP_DIR=<stage>/PCB setzen.
Die Lage ergibt sich aus der Leiterplatte selbst: Sie wird auf die bisherige Lage der jeweiligen Platine gelegt,
gedreht um 0/90/180/270 Grad. Fuer L1 gibt es kein 3D-Modell, deshalb ein Platzhalter 13,5 x 12,5 x 6,5 mm (Bourns SRP1265A, Maximalhoehe).
Prueft danach Kollisionen mit beiden Gitter-Varianten und dem Rueckrahmen.
"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
EXP = os.environ.get("WORTUHR_STEP_DIR") or os.path.join(ROOT, "05_Production", "05_Platine_JLCPCB")
import sys
sys.path.insert(0, os.path.join(ROOT, "02_Electronics", "KiCad", "tools"))
import design as D  # noqa: E402  Rastermasse: eine Quelle
# Objekt: STEP, Drehung, Aussenecke (x, y) der Leiterplatte am Rand der Uhr
PL = {"PCB_Q4_Master": ("LED-Board_master.step", 0), "PCB_Q2": ("LED-Board_slave.step", 90), "PCB_Q1": ("LED-Board_slave.step", 180), "PCB_Q3": ("LED-Board_slave.step", 270)}
(XC, YC), B0, B1 = D.CLOCK_CENTER, D.BOARD_MIN, D.BOARD_MAX


def board(sols):
    return max(sols, key=lambda s: s.BoundBox.XLength * s.BoundBox.YLength)


def local_to_global(x, y, ang):
    u, v = x, -y
    return {0: (XC + u, YC + v), 90: (XC - v, YC + u), 180: (XC - u, YC - v), 270: (XC + v, YC - u)}[ang]


Z_TOP = 5.0
for name, (f, ang) in PL.items():
    s = Part.read(os.path.join(EXP, f))
    b = board(s.Solids); bb = b.BoundBox
    # KiCad-STEP: Oberseite zeigt nach +z; lokaler Ursprung so, dass Platinenecke (0,5 | 0,5) links oben liegt
    s2 = s.copy()
    s2.translate(V(-bb.XMin + B0, -bb.YMax - B0, Z_TOP - bb.ZMax))     # jetzt x = lokal x, y = -lokal y
    s2.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    s2.translate(V(XC, YC, 0))
    sols = list(s2.Solids)
    if name == "PCB_Q4_Master":
        lx, ly = local_to_global(102.0, 224.0, 0)
        sols.append(Part.makeBox(13.5, 12.5, 6.5, V(lx - 6.75, ly - 6.25, Z_TOP - (bb.ZMax - bb.ZMin) - 6.5)))
    o = doc.getObject(name)
    nb = board(sols).BoundBox
    print(name, "Platine", [round(v, 2) for v in (nb.XMin, nb.XMax, nb.YMin, nb.YMax, nb.ZMin, nb.ZMax)], "Solids", len(sols), "alt", len(o.Shape.Solids))
    o.Shape = Part.makeCompound(sols)
doc.recompute()

grids = {}
for n in ("Q1_obenlinks", "Q2_obenrechts", "Q3_untenlinks", "Q4_untenrechts"):
    grids[n] = doc.getObject(n).Shape
    grids[n + "_JLC3DP"] = doc.getObject(n + "_JLC3DP").Shape
rear = [(o.Name, o.Shape) for o in doc.getObject("Rueckrahmen").Group]
total = 0.0
for name in PL:
    o = doc.getObject(name)
    for so in o.Shape.Solids:
        for label, g in list(grids.items()) + rear:
            if so.BoundBox.intersect(g.BoundBox):
                v = so.common(g).Volume
                if v > 1e-3:
                    total += v; c = so.BoundBox.Center
                    print("KOLLISION", name, label, round(v, 2), "mm3 bei", round(c.x, 1), round(c.y, 1), "z", round(so.BoundBox.ZMin, 2), round(so.BoundBox.ZMax, 2))
print("KOLLISION GESAMT", round(total, 2))
doc.save()
print("PCB MODEL DONE")
