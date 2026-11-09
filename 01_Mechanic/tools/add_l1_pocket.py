# -*- coding: utf-8 -*-
"""Rueckrahmen Q4 lang: Tasche fuer Spule L1 (Bourns SRP1265A, 13,5 x 12,5 x max. 6,5 mm) (freecadcmd add_l1_pocket.py).

Die Spule sitzt auf der Platinenunterseite und ragt bis z = -3,01 mm. Tasche mit 1 mm Luft je Seite und zum Boden.
Offen zur Platine; beim Druck liegt die Wandseite auf dem Bett, die Tasche braucht also keine Stuetzen.
Schreibt die STEP-Datei der Leiste und die Druckplatte 1 neu.
"""
import os
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
OUT = os.path.join(ROOT, "01_Mechanic", "Rueckrahmen")
XMIN, XMAX, YMIN, YMAX = 345.88, 359.38, -480.25, -467.75      # Lage L1 im Modell
AIR, FLOOR, TOP = 1.0, -4.0, 3.6

bar = doc.getObject("Rueckrahmen_Q4_untenrechts_lang")
before = bar.Shape.Volume
box = Part.makeBox(XMAX - XMIN + 2 * AIR, YMAX - YMIN + 2 * AIR, TOP - FLOOR, V(XMIN - AIR, YMIN - AIR, FLOOR))
s = bar.Shape.cut(box).removeSplitter()
assert s.isValid() and len(s.Solids) == 1
bar.Shape = s
doc.recompute()
Part.export([bar], os.path.join(OUT, "Rueckrahmen_Q4_untenrechts_lang.step"))

# Druckplatte 1: gleiche Anordnung wie bisher (Wandseite aufs Bett, 5 mm Abstand)
parts, y = [], 0.0
for q in ("Q1_obenlinks", "Q2_obenrechts", "Q3_untenlinks", "Q4_untenrechts"):
    c = doc.getObject(f"Rueckrahmen_{q}_lang").Shape.copy()
    b = c.BoundBox
    c.translate(V(-b.XMin + 2, -b.YMin + 2 + y, -b.ZMin))
    y += b.YLength + 5
    parts.append(c)
MeshPart.meshFromShape(Shape=Part.makeCompound(parts), LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(
    os.path.join(OUT, "Rueckrahmen_Druckplatte1_lange_Leisten.3mf"))
doc.save()
print("L1 POCKET DONE", round(before - s.Volume, 1), "mm3 entfernt")
