# -*- coding: utf-8 -*-
"""Zweiter Teil des Routings: SES aus Freerouting uebernehmen (nach route_master.py --prepare + Freerouting).

Aufruf (KiCad-Python): python tools/route_finish.py [pfad.ses]
Liest den Zustand aus route_master.py. Uebernimmt nur die neu gerouteten Signalnetze, entfernt offene Vias
und Stichleitungen und fuellt die Flaechen neu.
"""
import os, sys, json, tempfile
import pcbnew

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PRJ, "WortUhr.kicad_pcb")
ST = json.load(open(os.path.join(tempfile.gettempdir(), "wortuhr_route_state.json")))
ses = next((a for a in sys.argv[1:] if a.endswith(".ses")), ST["ses"])
assert os.path.exists(ses), "no SES"
ROUTE, CREATED = set(ST["route"]), set(ST["created"])
mm, toMM = pcbnew.FromMM, pcbnew.ToMM
board = pcbnew.LoadBoard(PCB)
tb = pcbnew.LoadBoard(ST["tmp_pcb"])
assert pcbnew.ImportSpecctraSES(tb, ses), "SES import failed"


def pos(p):
    return toMM(p.x), toMM(p.y)


def add_track(b, a, c, netname, layer, w):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
    t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNet(b.FindNet(netname)); b.Add(t); CREATED.add(t.m_Uuid.AsString()); return t


def add_via(b, x, y, netname, d=0.8, drill=0.4):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(b.FindNet(netname)); b.Add(v); CREATED.add(v.m_Uuid.AsString()); return v


# ---------------------------------------------------------------- 3. Uebernehmen
old = set()
for t in board.GetTracks():
    key = (t.GetClass(), t.GetNetname(), t.GetStart().x, t.GetStart().y, t.GetEnd().x if t.GetClass() != "PCB_VIA" else 0)
    old.add(key)
copied = 0
COPIED_VIAS = []
for t in tb.GetTracks():
    n = t.GetNetname()
    if n not in ROUTE or n.startswith("USB_D"):   # USB ist von Hand verlegt, Router-Reste nicht uebernehmen
        continue
    key = (t.GetClass(), n, t.GetStart().x, t.GetStart().y, t.GetEnd().x if t.GetClass() != "PCB_VIA" else 0)
    if key in old:
        continue
    if t.GetClass() == "PCB_VIA":
        COPIED_VIAS.append(add_via(board, toMM(t.GetPosition().x), toMM(t.GetPosition().y), n, max(toMM(t.GetWidth(pcbnew.F_Cu)), toMM(t.GetDrillValue()) + 0.4), toMM(t.GetDrillValue())))   # Restring >= 0.2 mm (JLCPCB)
    else:
        add_track(board, pos(t.GetStart()), pos(t.GetEnd()), n, t.GetLayer(), toMM(t.GetWidth()))
    copied += 1
print("copied", copied)
# ueberfluessige Vias (nur auf einer Lage angeschlossen) entfernen
ends = {}
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        for p in (t.GetStart(), t.GetEnd()):
            ends.setdefault((round(p.x / 20000), round(p.y / 20000), t.GetNetname()), set()).add(t.GetLayer())
pads = {(round(p.GetPosition().x / 20000), round(p.GetPosition().y / 20000)) for fp in board.GetFootprints() for p in fp.Pads()}
removed = 0
POUR = {"GND": pcbnew.B_Cu, "+5V": pcbnew.F_Cu}
for v in COPIED_VIAS:
    n = v.GetNetname()
    key = (round(v.GetPosition().x / 20000), round(v.GetPosition().y / 20000), n)
    if (key[0], key[1]) in pads:
        continue
    lay = set(ends.get(key, set()))
    if n in POUR:
        lay.add(POUR[n])          # Flaeche verbindet die andere Lage
    if len(lay) < 2:
        board.Remove(v); removed += 1
print("dangling vias removed", removed)
# kurze Stummel ohne Anschluss (Reste entfernter Vias) entfernen
q = lambda p: (round(p.x / 20000), round(p.y / 20000))
stubs = 0
for _ in range(5):
    pts = {}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            for p in (t.GetStart(), t.GetEnd()):
                pts.setdefault((q(p), t.GetNetname(), t.GetLayer()), 0)
                pts[(q(p), t.GetNetname(), t.GetLayer())] += 1
    anchors = {(q(v.GetPosition()), v.GetNetname()) for v in board.GetTracks() if v.GetClass() == "PCB_VIA"}
    padpts = {q(p.GetPosition()) for fp in board.GetFootprints() for p in fp.Pads()}
    gone = 0
    for t in list(board.GetTracks()):
        if t.GetClass() != "PCB_TRACK" or toMM(t.GetLength()) > 1.0 or t.m_Uuid.AsString() in CREATED:
            continue
        for p in (t.GetStart(), t.GetEnd()):
            k = q(p)
            if pts[(k, t.GetNetname(), t.GetLayer())] == 1 and (k, t.GetNetname()) not in anchors and k not in padpts:
                board.Remove(t); gone += 1
                break
    stubs += gone
    if not gone:
        break
print("dangling stubs removed", stubs)
# GND-Inseln auf der Unterseite ueber die Oberseite anbinden
# J1 traegt den gesamten Eingangs-Rueckstrom: breite Bruecke, je zwei Vias
_R = lambda x, y: (x + 40.0, y + 40.0)
_J = [(66.4, 221.9), (66.4, 223.0), (60.2, 223.0), (60.2, 223.3)]
for _a, _c in zip(_J, _J[1:]):
    add_track(board, _R(*_a), _R(*_c), "GND", pcbnew.F_Cu, 0.8)
for _v in ((66.4, 221.9), (66.4, 223.0), (60.2, 223.3)):
    add_via(board, _v[0] + 40.0, _v[1] + 40.0, "GND", 0.7, 0.3)
# U1 Masse-Pad 64 liegt zwischen USB-Paar und Modulrand
add_track(board, _R(41.0, 215.5), _R(43.6, 215.5), "GND", pcbnew.F_Cu, 0.4)
for _v in ((41.0, 215.5), (43.6, 215.5)):
    add_via(board, _v[0] + 40.0, _v[1] + 40.0, "GND", 0.7, 0.3)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
print("saved")
