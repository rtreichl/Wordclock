# -*- coding: utf-8 -*-
"""Minutenpunkte in den Ecken: Lichtkammern im Gitter (P1S + JLC3DP) und Minuten-LED im Platinenmodell.

Je Ecke (freecadcmd add_minute_dots.py):
- Diffusor-Tasche Ø 5,9 x 2,1 mm oben (runder Diffusor Ø 5,6 x 2 mm), unter dem Punkt Ø 4 der Frontplatte
- Lichtkanal Ø 5 mm: schraeg von der LED, die letzten 5 mm senkrecht unter dem Punkt
- Aussparung Ø 7,4 x 2 mm unten fuer das LED-Gehaeuse 5 x 5 mm (Mitte = LED-Position)
Punkte 18 mm von beiden Plattenkanten (bei 20 mm nur 0,4 mm Wand zu den Eck-Freistichen der Diffusor-Taschen); LED-Positionen aus der Platine (lokal 230/230, je Platine gedreht).
Rund statt eckig, weil das Buchstabenraster rechts 1,3 mm naeher am Rand liegt (sonst < 2,5 mm Wand).
Exportiert danach STEP/3MF beider Varianten neu.
"""
import os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
N = {"Q1": "Q1_obenlinks", "Q2": "Q2_obenrechts", "Q3": "Q3_untenlinks", "Q4": "Q4_untenrechts"}
DOT = {"Q1": (18.0, -18.0), "Q2": (482.0, -18.0), "Q3": (18.0, -482.0), "Q4": (482.0, -482.0)}
LED = {"Q1": (20.628, -20.0), "Q2": (480.627, -20.0), "Q3": (20.628, -480.0), "Q4": (480.627, -480.0)}
PCB = {"Q1": "PCB_Q1", "Q2": "PCB_Q2", "Q3": "PCB_Q3", "Q4": "PCB_Q4_Master"}
Z_PCB, Z_TOP, POCKET_D = 5.0, 25.0, 2.1
R_POCKET, R_BORE, R_LED, H_LED = 2.95, 2.5, 3.7, 2.0
Z_STRAIGHT = Z_TOP - POCKET_D - 5.0


def cut_corner(q):
    (dx, dy), (lx, ly) = DOT[q], LED[q]
    pocket = Part.makeCylinder(R_POCKET, POCKET_D + 1, V(dx, dy, Z_TOP - POCKET_D))
    # Lichtkanal: schraeg von der LED bis z = Z_STRAIGHT unter den Punkt, dann senkrecht bis in die Tasche
    # (endet der schraege Teil direkt in der Tasche, entsteht am Taschenboden ein 0,7-mm-Keil)
    c0 = Part.Wire(Part.makeCircle(R_LED, V(lx, ly, Z_PCB + H_LED)))   # Kegel setzt buendig auf der Aussparung an (gleiche Kante)
    c1 = Part.Wire(Part.makeCircle(R_BORE, V(dx, dy, Z_STRAIGHT)))
    bore = Part.makeLoft([c0, c1], True).fuse(Part.makeCylinder(R_BORE, Z_TOP - Z_STRAIGHT, V(dx, dy, Z_STRAIGHT)))
    rec = Part.makeCylinder(R_LED, H_LED + 0.1, V(lx, ly, Z_PCB - 0.1))
    return Part.makeCompound([pocket, bore, rec])


for suf in ("", "_JLC3DP"):
    for q, n in N.items():
        o = doc.getObject(n + suf)
        if o is None:
            continue
        tool = cut_corner(q)
        if o.Shape.common(tool).Volume < 1.0:      # schon geschnitten
            print(o.Name, "bereits vorhanden"); continue
        s = o.Shape.cut(tool).removeSplitter()
        assert s.isValid() and len(s.Solids) == 1, o.Name
        o.Shape = s
        print(o.Name, "Eckkammer geschnitten")

# Minuten-LED (5 x 5 x 1,6 mm) und C175 (Unterseite) ins Platinenmodell
for q, n in PCB.items():
    o = doc.getObject(n); lx, ly = LED[q]
    body = Part.makeBox(5.0, 5.0, 1.6, V(lx - 2.5, ly - 2.5, Z_PCB))
    sols = list(o.Shape.Solids)
    if not any(abs(so.BoundBox.Center.x - lx) < 0.05 and abs(so.BoundBox.Center.y - ly) < 0.05 and so.BoundBox.ZMin >= Z_PCB - 1e-3 for so in sols):
        o.Shape = Part.makeCompound(sols + [body]); print(n, "Minuten-LED eingesetzt")

# Diffusor-Scheiben (Ø 5,6 x 2 mm) als eigenes Objekt
discs = Part.makeCompound([Part.makeCylinder(2.8, 2.0, V(x, y, Z_TOP - POCKET_D)) for x, y in DOT.values()])
d = doc.getObject("Diffusor_Minuten") or doc.addObject("Part::Feature", "Diffusor_Minuten")
d.Shape = discs
doc.recompute(); doc.save()


def export(o, step, mf):
    Part.export([o], step)
    s = o.Shape.copy(); s.rotate(V(0, 0, 0), V(1, 0, 0), 180); b = s.BoundBox; s.translate(V(-b.XMin, -b.YMin, -b.ZMin))
    MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(mf)


g = os.path.join(ROOT, "01_Mechanic", "Gitter")
for n in N.values():
    export(doc.getObject(n), os.path.join(g, f"Gitter_{n}.step"), os.path.join(g, f"Gitter_{n}_druckfertig.3mf"))
    export(doc.getObject(n + "_JLC3DP"), os.path.join(g, "JLC3DP", f"Gitter_{n}_JLC3DP.step"),
           os.path.join(g, "JLC3DP", f"Gitter_{n}_JLC3DP_druckfertig.3mf"))
Part.export([d], os.path.join(ROOT, "01_Mechanic", "Diffusor", "Diffusor_Minutenpunkt_D5.6x2.step"))
print("MINUTE DOTS DONE")
