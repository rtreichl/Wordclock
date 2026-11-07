# -*- coding: utf-8 -*-
"""Platine komplett erzeugen: gen_pcb -> route_master -> DRC, bis alles sauber ist.

Freerouting arbeitet nicht deterministisch; daher bis zu N Versuche. Erfolgreich, wenn
DRC 0 Fehler, 0 offene Verbindungen, 0 Abweichungen zum Schaltplan (nur kosmetische Hinweise erlaubt).
Aufruf (KiCad-Python):  python tools/build_pcb.py [versuche]
"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
PY = sys.executable
CLI = os.environ.get("KICAD_CLI", r"P:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
COSMETIC = {"silk_edge_clearance", "silk_overlap", "silk_over_copper", "starved_thermal"}


def drc():
    out = os.path.join(PRJ, "drc_build.json")
    subprocess.run([CLI, "pcb", "drc", "--schematic-parity", "--format", "json", "-o", out,
                    os.path.join(PRJ, "WortUhr.kicad_pcb")], capture_output=True)
    d = json.load(open(out, encoding="utf-8")); os.remove(out)
    bad = [v["type"] for v in d["violations"] if v["type"] not in COSMETIC]
    return bad, len(d["unconnected_items"]), len(d["schematic_parity"])


tries = int(sys.argv[1]) if len(sys.argv) > 1 else 5
for n in range(1, tries + 1):
    for s in ("gen_pcb.py", "route_master.py"):
        subprocess.run([PY, os.path.join(HERE, s)], check=True, capture_output=True)
    bad, unc, par = drc()
    print(f"Versuch {n}: Fehler {len(bad)} {sorted(set(bad))}, offen {unc}, Paritaet {par}")
    if not bad and unc == 0 and par == 0:
        print("PCB OK")
        sys.exit(0)
sys.exit("PCB nach %d Versuchen nicht sauber" % tries)
