# -*- coding: utf-8 -*-
"""Erzeugt WLED ledmap.json fuer die WortUhr (4 Platinen, Kette Q4 -> Q2 -> Q1 -> Q3)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import design as D

# Platinen-Reihenfolge in der Datenkette und Abbildung lokale Kammer (k,j) -> (Spalte, Zeile) der Uhr
BOARDS = [("Q4 unten rechts (Master)", lambda k, j: (6 + k, 6 + j)),
          ("Q2 oben rechts",           lambda k, j: (6 + j, 5 - k)),
          ("Q1 oben links",            lambda k, j: (5 - k, 5 - j)),
          ("Q3 unten links",           lambda k, j: (5 - j, 6 + k))]
cells = []  # physische Kammer-Reihenfolge -> (Spalte, Zeile)
for name, f in BOARDS:
    for (k, j), _ in D.PATH:
        cells.append(f(k, j))
assert len(set(cells)) == 144
out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "WLED")
os.makedirs(out, exist_ok=True)
# 1 LED je Kammer: Matrix 12x12, map[Matrixposition] = physischer Index
m1 = [0] * 144
for phys, (col, row) in enumerate(cells):
    m1[row * 12 + col] = phys
# 2 LEDs je Kammer: Matrix 24x12 (je Kammer zwei Pixel nebeneinander: links = LED A, rechts = LED B)
m2 = [0] * 288
for idx, (col, row) in enumerate(cells):
    m2[row * 24 + 2 * col] = 2 * idx
    m2[row * 24 + 2 * col + 1] = 2 * idx + 1
json.dump({"n": "WortUhr 1 LED/Kammer", "width": 12, "height": 12, "map": m1}, open(os.path.join(out, "ledmap_1LED_12x12.json"), "w"))
json.dump({"n": "WortUhr 2 LED/Kammer", "width": 24, "height": 12, "map": m2}, open(os.path.join(out, "ledmap_2LED_24x12.json"), "w"))
print("ok", out, "first cells", cells[:6], "last", cells[-3:])
