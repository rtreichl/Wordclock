# -*- coding: utf-8 -*-
"""Schwalbenschwanz-Verbindungen oben schliessen (freecadcmd fix_dovetail_top.py).

Befund Qualifikation: Taschen gingen bis z = 25 durch und lagen nur 0,2 mm neben den
Diffusor-Taschen (z 22,9-25). Korrektur: Taschen enden bei z = 21,5, Zapfen bei z = 21,1.
Die Teile werden dadurch von unten zusammengeschoben.
"""
import os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
PX, PY, XC, YC = 38.5177, 38.4037, 250.6275, -250.0
xs = [XC + (i - 5.5) * PX for i in range(12)]; ys = [YC + (5.5 - j) * PY for j in range(12)]
XS, YS = (xs[5] + xs[6]) / 2, (ys[5] + ys[6]) / 2
rw = [(ys[j] + ys[j + 1]) / 2 for j in range(11)]; cw = [(xs[i] + xs[i + 1]) / 2 for i in range(11)]
J = [("Q1", "Q2", XS, rw[j], 0) for j in (0, 2, 4)] + [("Q3", "Q4", XS, rw[j], 0) for j in (6, 8, 10)] + \
    [("Q1", "Q3", cw[i], YS, -90) for i in (0, 2, 4)] + [("Q2", "Q4", cw[i], YS, -90) for i in (6, 8, 10)]
N = {"Q1": "Q1_obenlinks", "Q2": "Q2_obenrechts", "Q3": "Q3_untenlinks", "Q4": "Q4_untenrechts"}
Z_SOCK, Z_MALE = 21.5, 21.1


def trap(hl, neck, tip, z0, h):
    pts = [(0, -neck / 2), (hl, -tip / 2), (hl, tip / 2), (0, neck / 2)]
    return Part.Face(Part.makePolygon([V(u, v, z0) for u, v in pts] + [V(0, -neck / 2, z0)])).extrude(V(0, 0, h))


def put(sh, x, y, ang):
    s = sh.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), ang); s.translate(V(x, y, 0)); return s


# Diffusor-Taschen (30,4 x 30,4 x 2,1 mit Eckfreistichen) wie im Modell
P, DEPTH, RR = 30.4, 2.1, 0.75
pockets = []
for x in xs:
    for y in ys:
        b = Part.makeBox(P, P, DEPTH + 1, V(x - P / 2, y - P / 2, 25 - DEPTH))
        pockets.append(b.fuse([Part.makeCylinder(RR, DEPTH + 1, V(x + sx * P / 2, y + sy * P / 2, 25 - DEPTH)) for sx in (-1, 1) for sy in (-1, 1)]))
pockets = Part.makeCompound(pockets)

shapes = {q: doc.getObject(n).Shape for q, n in N.items()}
for f, t, x, y, a in J:
    fill = put(trap(3.8, 5.0, 7.6, Z_SOCK, 25 - Z_SOCK), x, y, a).cut(pockets)
    shapes[t] = shapes[t].fuse(fill)
    shapes[f] = shapes[f].cut(put(trap(3.52, 4.45, 7.05, Z_MALE, 5), x, y, a))
for q, n in N.items():
    s = shapes[q].removeSplitter()
    assert s.isValid() and len(s.Solids) == 1, q
    doc.getObject(n).Shape = s
    print(q, "ok", round(s.Volume))
doc.recompute(); doc.save()
out = os.path.join(ROOT, "01_Mechanic", "Gitter")
for q, n in N.items():
    o = doc.getObject(n); Part.export([o], os.path.join(out, f"Gitter_{n}.step"))
    s = o.Shape.copy(); s.rotate(V(0, 0, 0), V(1, 0, 0), 180); b = s.BoundBox; s.translate(V(-b.XMin, -b.YMin, -b.ZMin))
    MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(os.path.join(out, f"Gitter_{n}_druckfertig.3mf"))
print("FIX DONE")
