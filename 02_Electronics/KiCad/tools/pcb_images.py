# -*- coding: utf-8 -*-
"""Bilder der Platine zum Pruefen ohne Layout-Programm (kicad-cli).

Aufruf:  python tools/pcb_images.py [ausgabeordner]     (Standard: 02_Electronics/Bilder)
Erzeugt:
- Platine_3D_oben.png, Platine_3D_unten.png         Draufsicht (Master, mit allen Bauteilen)
- Platine_3D_schraeg_oben.png, ..._schraeg_unten.png  perspektivisch
- Platine_Lagen.pdf      eine Seite je Lage (Kupfer, Bestueckungsdruck, Loetstopp, Fab), mit Platinenumriss; zoombar
- Platine_Kupfer_oben.svg / _unten.svg               Kupferlagen als Vektorbild (im Browser zoombar)
"""
import os, sys, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
PCB = os.path.join(PRJ, "WortUhr.kicad_pcb")
CLI = os.environ.get("KICAD_CLI", r"P:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(PRJ), "Bilder")
os.makedirs(OUT, exist_ok=True)


def run(args):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("kicad-cli fehlgeschlagen: %s\n%s" % (" ".join(args), r.stdout + r.stderr))


R = ["pcb", "render", "--quality", "high", "--background", "opaque"]
for name, extra in (("Platine_3D_oben.png", ["--side", "top", "-w", "2400", "-h", "2400"]),
                    ("Platine_3D_unten.png", ["--side", "bottom", "-w", "2400", "-h", "2400"]),
                    ("Platine_3D_schraeg_oben.png", ["--rotate", "-40,0,30", "--perspective", "--zoom", "0.8", "-w", "2400", "-h", "1800"]),
                    ("Platine_3D_schraeg_unten.png", ["--side", "bottom", "--rotate", "40,0,-30", "--perspective", "--zoom", "0.8", "-w", "2400", "-h", "1800"])):
    run(R + extra + ["-o", os.path.join(OUT, name), PCB])
    print("ok", name)

LAYERS = "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Fab,B.Fab"
run(["pcb", "export", "pdf", "--mode-multipage", "--layers", LAYERS, "--common-layers", "Edge.Cuts",
     "--include-border-title", "-o", os.path.join(OUT, "Platine_Lagen.pdf"), PCB])
print("ok Platine_Lagen.pdf")
tmp = os.path.join(OUT, "_svg"); os.makedirs(tmp, exist_ok=True)
for layer, name, mirror in (("F.Cu", "Platine_Kupfer_oben.svg", []), ("B.Cu", "Platine_Kupfer_unten.svg", ["--mirror"])):
    run(["pcb", "export", "svg", "--mode-single", "--layers", f"{layer},Edge.Cuts", "--fit-page-to-board", "--exclude-drawing-sheet"]
        + mirror + ["-o", os.path.join(OUT, name), PCB])
    print("ok", name)
shutil.rmtree(tmp, ignore_errors=True)
