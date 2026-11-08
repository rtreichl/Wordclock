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
    if n not in ROUTE:
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
# Nacharbeit (ROUTING_GUIDE Abschnitt 4): GND-Inseln um USB-C und U1 an die Hauptflaeche
R = lambda x, y: (x + 40.0, y + 40.0)
_q = (80.0, 254.45)
_u1 = board.FindFootprintByReference("U1")
_gp = [pos(p_.GetPosition()) for p_ in _u1.Pads() if p_.GetNetname() == "GND"]
_gq = min(_gp, key=lambda v: (v[0] - _q[0]) ** 2 + (v[1] - _q[1]) ** 2)
_inner = [v for v in _gp if 68 < v[0] < 78 and 257 < v[1] < 270]
_in = min(_inner, key=lambda v: (v[0] - _gq[0]) ** 2 + (v[1] - _gq[1]) ** 2)
for t in list(board.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "GND" and (abs(toMM(t.GetStart().x) - _gq[0]) < 0.02 and abs(toMM(t.GetStart().y) - _gq[1]) < 0.02):
        board.Remove(t)
_va, _vb = R(41.1, 216.0), R(36.5, 216.0)
add_track(board, _va, _vb, "GND", pcbnew.F_Cu, 0.4)
add_via(board, _va[0], _va[1], "GND", 0.7, 0.3); add_via(board, _vb[0], _vb[1], "GND", 0.7, 0.3)
for a_, b_ in ((R(67.44, 219.5), R(67.44, 217.6)), (R(58.9, 224.5), R(57.0, 224.5))):
    add_track(board, a_, b_, "GND", pcbnew.F_Cu, 0.4)
    add_via(board, b_[0], b_[1], "GND", 0.7, 0.3)
add_via(board, R(58.9, 224.5)[0], R(58.9, 224.5)[1], "GND", 0.7, 0.3)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
print("saved")
