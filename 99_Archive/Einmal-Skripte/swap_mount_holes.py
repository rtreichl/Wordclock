# -*- coding: utf-8 -*-
"""Montageloecher H1-H6 im bestehenden Layout auf Ø 4,3 mm umstellen (wie MountingHole_4.3mm_M4).

Grund: Ø 4,3 mm fuer M3 gibt +-0,65 mm Spiel. Damit passt das Lochbild der Platine auch zu
3D-Druck-Gittern mit +-0,4 % Masstoleranz (JLC3DP) und gleicht Druck- und Montagetoleranzen aus.
Leiterbahnen bleiben unveraendert. Textersetzung in der .kicad_pcb (die SWIG-Objekte von
FootprintLoad + LoadBoard vertragen sich in KiCad 10 nicht), danach Zonen neu fuellen.
Aufruf mit KiCad-Python.
"""
import os, re, pcbnew

PCB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "WortUhr.kicad_pcb")
s = open(PCB, encoding="utf-8").read()
OLD = '(footprint "MountingHole:MountingHole_3.2mm_M3"'
n = 0
while OLD in s:
    i = s.index(OLD); j = s.index("\n\t(footprint", i + 10) if "\n\t(footprint" in s[i + 10:] else len(s)
    blk = s[i:j]
    blk = blk.replace(OLD, '(footprint "MountingHole:MountingHole_4.3mm_M4"')
    blk = blk.replace("Mounting Hole 3.2mm, M3, no annular", "Mounting Hole 4.3mm, M4, no annular")
    blk = blk.replace("(end 3.2 0)", "(end 4.3 0)").replace("(end 3.45 0)", "(end 4.55 0)")
    blk = blk.replace("(at 0 -4.15 0)", "(at 0 -5.3 0)").replace("(at 0 4.15 0)", "(at 0 5.3 0)")
    blk = blk.replace("(size 3.2 3.2)", "(size 4.3 4.3)").replace("(drill 3.2)", "(drill 4.3)")
    s = s[:i] + blk + s[j:]; n += 1
assert n == 6, n
open(PCB, "w", encoding="utf-8").write(s)
b = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)
print("H1-H6 auf 4,3 mm, Zonen gefuellt")
