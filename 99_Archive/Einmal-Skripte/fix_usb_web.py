# -*- coding: utf-8 -*-
"""Q4: 1-mm-Steg zwischen USB-C-Rahmenausschnitt und Freiraum darueber entfernen (freecadcmd)."""
import os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
XS, YS = 250.6275, -250.0
o = doc.getObject("Q4_untenrechts")
for cx, w in ((XS + 63.0, 12.0), (XS + 100.0, 3.6)):          # USB-C, Fuehrungsstift Hohlbuchse
    o.Shape = o.Shape.cut(Part.makeBox(w, 2.2, 1.6, V(cx - w / 2, -484.6, 4.9)))
s = o.Shape.removeSplitter(); assert s.isValid() and len(s.Solids) == 1; o.Shape = s
doc.recompute(); doc.save()
out = os.path.join(ROOT, "01_Mechanic", "Gitter")
Part.export([o], os.path.join(out, "Gitter_Q4_untenrechts.step"))
m = s.copy(); m.rotate(V(0, 0, 0), V(1, 0, 0), 180); b = m.BoundBox; m.translate(V(-b.XMin, -b.YMin, -b.ZMin))
MeshPart.meshFromShape(Shape=m, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(os.path.join(out, "Gitter_Q4_untenrechts_druckfertig.3mf"))
print("USB FIX DONE", round(s.Volume))
