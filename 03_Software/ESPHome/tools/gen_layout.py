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
        "// LED-Nummer: cell_led(Index, LEDS_PER_CELL) + 0..LEDS_PER_CELL-1", "static const uint8_t CELL_INDEX[12][12] = {"]
for r in range(12):
    out.append("  {" + ", ".join("%3d" % phys[(r, c)] for c in range(12)) + "},")
out += ["};", "",
        "// Je Platine: 36 Kammern, nach Kammer %d (Kette) folgt die Minuten-LED in der Aussenecke." % D.MINUTE_AFTER,
        "static const uint8_t MINUTE_AFTER = %d;" % D.MINUTE_AFTER,
        "// Platine (0 = Q4 Master unten rechts, 1 = Q2 oben rechts, 2 = Q1 oben links, 3 = Q3 unten links)",
        "// fuer Minutenpunkt 1..4 im Uhrzeigersinn ab oben links.",
        "static const uint8_t MINUTE_BOARD[4] = {2, 1, 0, 3};", "",
        "inline int leds_per_board(int lpc) { return 36 * lpc + 1; }",
        "// Erste LED einer Kammer (Index aus CELL_INDEX) in der Kette",
        "inline int cell_led(int cell, int lpc) {",
        "  int b = cell / 36, c = cell % 36;",
        "  return b * leds_per_board(lpc) + c * lpc + (c > MINUTE_AFTER ? 1 : 0);",
        "}",
        "// LED des Minutenpunkts n (0..3)",
        "inline int minute_led(int n, int lpc) {",
        "  return MINUTE_BOARD[n] * leds_per_board(lpc) + (MINUTE_AFTER + 1) * lpc;",
        "}", "",
        "}  // namespace wortuhr", ""]
dst = os.path.join(os.path.dirname(HERE), "wortuhr_layout.h")
open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("geschrieben:", dst)
for r in range(12):
    print(" ".join(letters[(r, c)] for c in range(12)))
