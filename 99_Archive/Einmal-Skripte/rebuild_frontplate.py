# -*- coding: utf-8 -*-
"""Frontplatte aus der DXF neu aufbauen (WORTUHR_CONTOURS=<konturen.json> freecadcmd rebuild_frontplate.py).

Anlaesse: NEUN-Korrektur, 4 Minutenpunkte Ø 4 mm in den Ecken (18 mm vom Rand). In Zeile 8 wurden E (Spalte 7) und N (Spalte 8) getauscht, damit die Zeile
ZEHNEUNEVIER lautet und NEUN zusammenhaengend ist. Die Konturen kommen als JSON (aus der DXF per ezdxf).
Ersetzt die Form von 'Frontplatte' (z 25-26, y = DXF-y - 500), exportiert STEP und das Render-Netz.
"""
import os, sys, json
import FreeCAD as App, Part, Mesh, MeshPart
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cont = json.load(open(os.environ["WORTUHR_CONTOURS"]))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
old = doc.getObject("Frontplatte")


def face(c):
    if c["t"] == "C":
        w = Part.Wire(Part.makeCircle(c["r"], V(c["c"][0], c["c"][1], 0)))
    else:
        pts = [V(x, y, 0) for x, y in c["p"]]
        if (pts[0] - pts[-1]).Length > 1e-6:
            pts.append(pts[0])
        w = Part.makePolygon(pts)
    return Part.Face(w)


faces = sorted((face(c) for c in cont), key=lambda f: -f.Area)
plate = faces[0].cut(Part.makeCompound(faces[1:])).extrude(V(0, 0, 1))
plate.translate(V(0, -500, 25))
plate = plate.removeSplitter()
assert plate.isValid() and len(plate.Solids) == 1
print("VOL old %.3f new %.3f  faces old %d new %d" % (old.Shape.Volume, plate.Volume, len(old.Shape.Faces), len(plate.Faces)))
print("Volumenaenderung %.2f mm^3 (4 Minutenpunkte Ø 4 x 1 mm = -50,27)" % (plate.Volume - old.Shape.Volume))
old.Shape = plate
doc.recompute(); doc.save()
Part.export([old], os.path.join(ROOT, "01_Mechanic", "Frontplatte", "Frontplatte_1mm.step"))
MeshPart.meshFromShape(Shape=plate, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(
    os.path.join(ROOT, "04_Rendering", "meshes", "frontplatte.stl"))
print("REBUILD DONE")
