# -*- coding: utf-8 -*-
"""Qualifikation Runde 2 (freecadcmd):
- Schwalbenschwanz-Taschen enden bei z = 20,4 (Zapfen 20,0): 2,5 mm Boden unter den Diffusor-Taschen
- Q4: Spalt neben dem Fuehrungsstift der Hohlbuchse sauber freischneiden (kein 0,17-mm-Rest)"""
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
def trap(hl, neck, tip, z0, h):
    pts = [(0, -neck / 2), (hl, -tip / 2), (hl, tip / 2), (0, neck / 2)]
    return Part.Face(Part.makePolygon([V(u, v, z0) for u, v in pts] + [V(0, -neck / 2, z0)])).extrude(V(0, 0, h))
def put(sh, x, y, a):
    s = sh.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), a); s.translate(V(x, y, 0)); return s
S = {q: doc.getObject(n).Shape for q, n in N.items()}
for f, t, x, y, a in J:
    S[t] = S[t].fuse(put(trap(3.8, 5.0, 7.6, 20.4, 1.1), x, y, a))     # Tasche 20,4..21,5 schliessen
    S[f] = S[f].cut(put(trap(3.52, 4.45, 7.05, 20.0, 1.2), x, y, a))   # Zapfen bis 20,0 kuerzen
jx = XS + 100.0
S["Q4"] = S["Q4"].cut(Part.makeBox(5.0, 6.0, 1.6, V(jx - 2.5, -484.6, 4.9)))   # Fuehrungsstift-Freiraum zusammenhaengend
out = os.path.join(ROOT, "01_Mechanic", "Gitter")
for q, n in N.items():
    s = S[q].removeSplitter(); assert s.isValid() and len(s.Solids) == 1, q
    o = doc.getObject(n); o.Shape = s
    Part.export([o], os.path.join(out, f"Gitter_{n}.step"))
    m = s.copy(); m.rotate(V(0, 0, 0), V(1, 0, 0), 180); b = m.BoundBox; m.translate(V(-b.XMin, -b.YMin, -b.ZMin))
    MeshPart.meshFromShape(Shape=m, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(os.path.join(out, f"Gitter_{n}_druckfertig.3mf"))
doc.recompute(); doc.save(); print("ROUND2 DONE")
