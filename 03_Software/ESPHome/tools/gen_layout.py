# -*- coding: utf-8 -*-
"""Erzeugt wortuhr_layout.h fuer ESPHome aus den Projektdaten.

- Buchstaben je Kammer aus 00_Design/Frontplatte-500mm-Sencilla.svg (Pfad-IDs Lzz_ss_X)
- physische Kammer-Reihenfolge der Datenkette aus 02_Electronics/KiCad/tools/design.py
  (Master Q4 -> Q2 -> Q1 -> Q3, gleiche Abbildung wie gen_ledmap.py)
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while not os.path.isdir(os.path.join(ROOT, "05_Production")):  # Repo-Wurzel (auch ohne .git)
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "02_Electronics", "KiCad", "tools"))
import design as D  # noqa: E402

BOARDS = [lambda k, j: (6 + k, 6 + j),      # Q4 unten rechts (Master)
          lambda k, j: (6 + j, 5 - k),      # Q2 oben rechts
          lambda k, j: (5 - k, 5 - j),      # Q1 oben links
          lambda k, j: (5 - j, 6 + k)]      # Q3 unten links
phys = {}
for b, f in enumerate(BOARDS):
    for c, ((k, j), _) in enumerate(D.PATH):
        col, row = f(k, j)
        phys[(row, col)] = b * 36 + c
assert len(phys) == 144

svg = open(os.path.join(ROOT, "00_Design", "Frontplatte-500mm-Sencilla.svg"), encoding="utf-8").read()
letters = {}
for r, c, l in re.findall(r'id="L(\d\d)_(\d\d)_([^"_]+)', svg):
    letters[(int(r) - 1, int(c) - 1)] = l
assert len(letters) == 144

out = ["// Automatisch erzeugt von 03_Software/ESPHome/tools/gen_layout.py - nicht von Hand aendern.",
       "#pragma once", "#include <cstdint>", "",
       "namespace wortuhr {", "",
       "// Buchstabenraster (Zeile 0 = oben, Spalte 0 = links)"]
for r in range(12):
    out.append("//   " + " ".join(letters[(r, c)] for c in range(12)))
out += ["", "// Physischer Kammer-Index (0..143) in der Datenkette fuer [Zeile][Spalte].",
        "// LED-Nummer = Index * LEDS_PER_CELL + 0..LEDS_PER_CELL-1", "static const uint8_t CELL_INDEX[12][12] = {"]
for r in range(12):
    out.append("  {" + ", ".join("%3d" % phys[(r, c)] for c in range(12)) + "},")
out += ["};", "", "}  // namespace wortuhr", ""]
dst = os.path.join(os.path.dirname(HERE), "wortuhr_layout.h")
open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("geschrieben:", dst)
for r in range(12):
    print(" ".join(letters[(r, c)] for c in range(12)))
