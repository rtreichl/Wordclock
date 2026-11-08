# -*- coding: utf-8 -*-
"""Render-Netze aus dem FreeCAD-Modell schreiben (freecadcmd 04_Rendering/export_meshes.py).

Ausgabe: 04_Rendering/meshes/*.stl (oder Ordner aus WORTUHR_MESH_OUT), Einheit mm, Modellkoordinaten.
Leuchtend: "IST ZWANZIG VOR ZWOELF" + 2 Minutenpunkte (oben links, oben rechts) = 11:42.
"""
import os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("WORTUHR_MESH_OUT", os.path.join(HERE, "meshes")); os.makedirs(OUT, exist_ok=True)
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
PX, PY, XC, YC = 38.5177, 38.4037, 250.6275, -250.0
xs = [XC + (i - 5.5) * PX for i in range(12)]; ys = [YC + (5.5 - j) * PY for j in range(12)]
LIT = ((4, 1, 3), (6, 6, 12), (7, 1, 3), (12, 5, 9))      # IST, ZWANZIG, VOR, ZWOELF
lit = {(r, c) for r, c0, c1 in LIT for c in range(c0, c1 + 1)}


def w(shape, name, lin=0.05):
    MeshPart.meshFromShape(Shape=shape, LinearDeflection=lin, AngularDeflection=0.3, Relative=False).write(os.path.join(OUT, name + ".stl"))


on, off = [], []
for r in range(1, 13):
    for c in range(1, 13):
        (on if (r, c) in lit else off).append(Part.makeBox(30, 30, 2.0, V(xs[c - 1] - 15, ys[r - 1] - 15, 22.9)))
DOTS = [(18.0, -18.0), (482.0, -18.0), (482.0, -482.0), (18.0, -482.0)]   # Minute 1..4 im Uhrzeigersinn
MINUTES = 2
for n, (x, y) in enumerate(DOTS):
    (on if n < MINUTES else off).append(Part.makeCylinder(2.8, 2.0, V(x, y, 22.9)))
w(doc.getObject("Frontplatte").Shape, "frontplatte", 0.02)
w(Part.makeCompound(on), "diffusor_an"); w(Part.makeCompound(off), "diffusor_aus")
for n in ("Q1_obenlinks", "Q2_obenrechts", "Q3_untenlinks", "Q4_untenrechts"):
    w(doc.getObject(n).Shape, "gitter_" + n, 0.1)
w(doc.getObject("Lichtleiter").Shape, "lichtleiter", 0.02)
for n in ("PCB_Q4_Master", "PCB_Q2", "PCB_Q1", "PCB_Q3"):
    w(doc.getObject(n).Shape, "pcb_" + n, 0.1)
w(Part.makeCompound([o.Shape for o in doc.getObject("Rueckrahmen").Group]), "rueckrahmen", 0.1)
print("MESHES DONE", OUT, sorted(os.listdir(OUT)), len(on), "leuchtende Kammern")
