# -*- coding: utf-8 -*-
"""Montageloecher der Platinen im FreeCAD-Modell von Ø 3,2 auf Ø 4,3 mm aufbohren (freecadcmd).

Gleicher Stand wie 02_Electronics/KiCad (H1-H6 = MountingHole_4.3mm_M4). Nur die Leiterplatte selbst
(groesster Solid) wird geaendert; Bauteile bleiben.
"""
import os
import FreeCAD as App, Part
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
R_OLD, R_NEW = 1.6, 2.15
for n in ("PCB_Q4_Master", "PCB_Q2", "PCB_Q1", "PCB_Q3"):
    o = doc.getObject(n); sol = list(o.Shape.Solids)
    k = max(range(len(sol)), key=lambda i: sol[i].BoundBox.XLength * sol[i].BoundBox.YLength)
    b = sol[k]; bb = b.BoundBox
    cs = {(round(e.Curve.Center.x, 3), round(e.Curve.Center.y, 3)) for e in b.Edges
          if type(e.Curve).__name__ == "Circle" and abs(e.Curve.Radius - R_OLD) < 0.01}
    assert len(cs) in (0, 6), (n, cs)
    if cs:
        cyl = Part.makeCompound([Part.makeCylinder(R_NEW, bb.ZLength + 2, V(x, y, bb.ZMin - 1)) for x, y in cs])
        sol[k] = b.cut(cyl).removeSplitter()
        o.Shape = Part.makeCompound(sol)
    print(n, "Loecher", len(cs), "-> Ø %.1f" % (2 * R_NEW))
doc.recompute(); doc.save()
print("PCB HOLES DONE")
