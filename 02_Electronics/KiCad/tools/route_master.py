# -*- coding: utf-8 -*-
"""Routet die Master-Elektronik mit Freerouting (nach gen_pcb.py und route_buck_usb.py ausfuehren).

1. +5V-/GND-Pads der Master-Teile bekommen Vias auf die Flaechen (+5V oben, GND unten).
2. Temporaere Kopie: Flaechen entfernt, vorhandene Leiterbahnen fixiert, +5V/GND ohne Netz
   -> Freerouting routet nur die Master-Signalnetze.
3. Neue Leiterbahnen/Vias der Signalnetze werden in die echte Platine uebernommen,
   Leistungsnetze (VBUS/VDC) verbreitert, Flaechen neu gefuellt.
"""
import os, sys, math, glob, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import design as D
import kicad_env

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PRJ, "WortUhr.kicad_pcb")
MASTER = set(D.MASTER_PLACE)
POWER_W = {"VBUS": 0.6, "+15V": 0.8, "+3V3": 0.5, "USB_D+": 0.2, "USB_D-": 0.2}   # ROUTING_GUIDE.md: Power >= 0,5 mm
mm, toMM = pcbnew.FromMM, pcbnew.ToMM

board = pcbnew.LoadBoard(PCB)
edge = board.GetBoardEdgesBoundingBox()


def pos(p):
    return toMM(p.x), toMM(p.y)


def obstacles(b):
    """(x1,y1,x2,y2,layers,netname) fuer Pads, Leiterbahnen, Vias."""
    obs = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            lay = set()
            if p.IsOnLayer(pcbnew.F_Cu): lay.add("F")
            if p.IsOnLayer(pcbnew.B_Cu): lay.add("B")
            if p.GetDrillSize().x > 0: lay |= {"F", "B"}
            obs.append((toMM(bb.GetLeft()), toMM(bb.GetTop()), toMM(bb.GetRight()), toMM(bb.GetBottom()), lay, p.GetNetname()))
    for t in b.GetTracks():
        bb = t.GetBoundingBox()
        if t.GetClass() == "PCB_VIA":
            lay = {"F", "B"}
        else:
            lay = {"F"} if t.GetLayer() == pcbnew.F_Cu else {"B"}
        obs.append((toMM(bb.GetLeft()), toMM(bb.GetTop()), toMM(bb.GetRight()), toMM(bb.GetBottom()), lay, t.GetNetname()))
    return obs


def keepouts(b):
    ks = []
    for fp in b.GetFootprints():
        for z in fp.Zones():
            if z.GetIsRuleArea():
                bb = z.GetBoundingBox(); ks.append((toMM(bb.GetLeft()), toMM(bb.GetTop()), toMM(bb.GetRight()), toMM(bb.GetBottom())))
    return ks


def seg_ok(a, c, netname, obs, w=0.3, gap=0.25):
    n = max(2, int(math.hypot(c[0] - a[0], c[1] - a[1]) / 0.1))
    for i in range(n + 1):
        px, py = a[0] + (c[0] - a[0]) * i / n, a[1] + (c[1] - a[1]) * i / n
        for x1, y1, x2, y2, lay, nn in obs:
            if nn == netname:
                continue
            dx = max(x1 - px, 0, px - x2); dy = max(y1 - py, 0, py - y2)
            if math.hypot(dx, dy) < w / 2 + gap:
                return False
    return True


def free_spot(x, y, netname, obs, ks, r=0.4, gap=0.35, seg_from=None, center=None):
    """Freien Via-Platz nahe (x,y) suchen (beide Lagen); bevorzugt von der Bauteilmitte weg."""
    base = 0.0
    if center is not None and math.hypot(x - center[0], y - center[1]) > 1e-3:
        base = round(math.degrees(math.atan2(y - center[1], x - center[0])) / 45.0) * 45.0
    for d in (1.4, 1.8, 2.3, 2.8, 3.4, 4.0):
        for k in range(8):
            ang = base + (k + 1) // 2 * 45 * (1 if k % 2 else -1)
            vx, vy = x + d * math.cos(math.radians(ang)), y + d * math.sin(math.radians(ang))
            if not (toMM(edge.GetLeft()) + 1 < vx < toMM(edge.GetRight()) - 1 and toMM(edge.GetTop()) + 1 < vy < toMM(edge.GetBottom()) - 1):
                continue
            if any(k[0] - 0.5 < vx < k[2] + 0.5 and k[1] - 0.5 < vy < k[3] + 0.5 for k in ks):
                continue
            ok = True
            for x1, y1, x2, y2, lay, n in obs:
                if n == netname:
                    continue
                dx = max(x1 - vx, 0, vx - x2); dy = max(y1 - vy, 0, vy - y2)
                if math.hypot(dx, dy) < r + gap:
                    ok = False; break
            if ok and any(math.hypot(vx - a, vy - b) < 1.2 for a, b in VIAS):
                ok = False
            if ok and seg_from is not None and not seg_ok(seg_from, (vx, vy), netname, [o for o in obs if not (o[0] <= seg_from[0] <= o[2] and o[1] <= seg_from[1] <= o[3])]):
                ok = False
            if ok:
                return vx, vy
    return None


CREATED = set()


def add_track(b, a, c, netname, layer, w):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
    t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNet(b.FindNet(netname)); b.Add(t); CREATED.add(t.m_Uuid.AsString()); return t


def add_via(b, x, y, netname, d=0.8, drill=0.4):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(b.FindNet(netname)); b.Add(v); CREATED.add(v.m_Uuid.AsString()); return v


# ---------------------------------------------------------------- 1. Power-Vias
ks = keepouts(board)
VIAS = []
added = 0
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in MASTER:
        continue
    for p in fp.Pads():
        n = p.GetNetname()
        top = p.IsOnLayer(pcbnew.F_Cu) and not p.IsOnLayer(pcbnew.B_Cu)
        if ref in ("U5", "U7", "L1", "C23", "C24", "C25", "R22", "C28") or (ref == "U3" and p.GetNumber() == "5"):
            continue
        need = (n == "+5V") or (n == "GND" and top)
        if not need:
            continue
        # Bauteile mit hohem Strom bekaemen mehrere Vias (derzeit keines: L1 ist von Hand verlegt)
        count = 6 if ref == "L1" else 1
        x, y = pos(p.GetPosition())
        layer = pcbnew.F_Cu if top else pcbnew.B_Cu
        fx, fy = pos(fp.GetPosition())
        for _ in range(count):
            obs = obstacles(board)
            s = free_spot(x, y, n, obs, ks, seg_from=(x, y), center=(fx, fy))
            if not s:
                print("kein Via-Platz fuer", ref, p.GetNumber()); break
            add_track(board, (x, y), s, n, layer, 0.6 if count > 1 else 0.3)
            add_via(board, s[0], s[1], n, 0.8 if count > 1 else 0.7, 0.4 if count > 1 else 0.3)
            VIAS.append(s)
            added += 1
# Sensor U5 (Oberseite, Pins 1-3 zeigen nach links): GND-Pins gemeinsam auf ein Via, +3V3 kurz zu C8 auf der Unterseite
u5 = board.FindFootprintByReference("U5")
pp = {p.GetNumber(): pos(p.GetPosition()) for p in u5.Pads()}
(x2, y2), (x3, y3) = pp["2"], pp["3"]
xo = x2 - 1.1
add_track(board, (x2, y2), (xo, y2), "GND", pcbnew.F_Cu, 0.2)
add_track(board, (x3, y3), (xo, y3), "GND", pcbnew.F_Cu, 0.2)
add_track(board, (xo, y2), (xo, y3 + 1.5), "GND", pcbnew.F_Cu, 0.25)
add_via(board, xo, y3 + 1.5, "GND", 0.7, 0.3); added += 1
x1, y1 = pp["1"]
cx, cy = [pos(p.GetPosition()) for p in board.FindFootprintByReference("C8").Pads() if p.GetNetname() == "+3V3"][0]
add_track(board, (x1, y1), (cx, y1), "+3V3", pcbnew.F_Cu, 0.25)
add_via(board, cx, y1, "+3V3", 0.8, 0.4); added += 1
add_track(board, (cx, y1), (cx, cy), "+3V3", pcbnew.B_Cu, 0.5)
def _pad(ref, num):
    return [pos(p.GetPosition()) for p in board.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def _rel(x, y):
    return (x + 40.0, y + 40.0)
def _poly(pts, layer, net, w):
    for a_, c_ in zip(pts, pts[1:]):
        dx_, dy_ = abs(a_[0] - c_[0]), abs(a_[1] - c_[1])
        assert dx_ < 1e-3 or dy_ < 1e-3 or abs(dx_ - dy_) < 0.03, ("Winkel", net, a_, c_)
        add_track(board, a_, c_, net, layer, w)
# VBUS: beide Pinpaare ueber Vias und Steg oben, dann zur Sicherung
_vb = sorted(pos(p.GetPosition()) for p in board.FindFootprintByReference("J1").Pads() if p.GetNetname() == "VBUS")
_xs = sorted({round(x, 3) for x, y in _vb}); _y = min(y for x, y in _vb) - 2.2
for _x in _xs:
    _poly([[(x, y) for x, y in _vb if abs(x - _x) < 0.01][0], (_x, _y)], pcbnew.B_Cu, "VBUS", 0.6)
    add_via(board, _x, _y, "VBUS", 0.8, 0.4); added += 1
_poly([(_xs[0], _y), (_xs[-1], _y)], pcbnew.F_Cu, "VBUS", 0.6)
_f1 = [pos(p.GetPosition()) for p in board.FindFootprintByReference("F1").Pads() if p.GetNetname() == "VBUS"][0]
_fx = 40 + 68.6
_poly([(_xs[-1], _y), (_xs[-1] + 1.45, _y + 1.45), (_fx, _y + 1.45), (_fx, _f1[1])], pcbnew.F_Cu, "VBUS", 0.6)
add_via(board, _fx, _f1[1], "VBUS", 0.8, 0.4); added += 1
_poly([(_fx, _f1[1]), _f1], pcbnew.B_Cu, "VBUS", 0.6)
# +3V3 fest (PWR-001, Punkt 3: von aussen ueber die Kondensatoren zum Pin)
_V1, _V2, _V3, _V4 = _rel(45.2, 224.1), _rel(21.9, 228.6), _rel(11.5, 227.6), _rel(22.5, 224.1)
_P = "+3V3"
_c3, _u25 = _pad("C3", "1"), _pad("U2", "5")
_poly([_c3, (_c3[0], _u25[1]), _u25, (_u25[0] - 2.3, _u25[1] + 2.3), _rel(46.6, _u25[1] + 2.3 - 40), (_rel(46.6, 0)[0] - 1.4, _u25[1] + 0.9), (_V1[0], _V1[1])], pcbnew.B_Cu, _P, 0.65)
_r31 = _pad("R3", "1")
_poly([_V1, (_r31[0] + (_V1[1] - _r31[1]), _V1[1]), _r31], pcbnew.B_Cu, _P, 0.5)
_T = _rel(26.1, 224.1)
_poly([_V1, _T, _rel(21.9, 228.3), _V2], pcbnew.F_Cu, _P, 0.65)   # Espressif: Hauptleitung >= 25 mil
# Espressif: beim Lagenwechsel der Hauptleitung mindestens zwei Vias
_V1b = (_V1[0], _u25[1] + 0.9)
_poly([_V1, _V1b], pcbnew.F_Cu, _P, 0.65)
add_via(board, _V1b[0], _V1b[1], _P, 0.8, 0.4); added += 1
_poly([_T, _V4], pcbnew.F_Cu, _P, 0.5)
_r41 = _pad("R4", "1")
_poly([_V4, (_V4[0], _r41[1] + (_V4[0] - _r41[0])), _r41], pcbnew.B_Cu, _P, 0.5)
_c91 = _pad("C9", "1"); _c41 = _pad("C4", "1"); _u13 = _pad("U1", "3")
_poly([_V2, (_V2[0], _c91[1] + (_V2[0] - _c91[0])), _c91], pcbnew.B_Cu, _P, 0.5)
_poly([_V2, (_c41[0], _V2[1]), _c41, (_c41[0] + (_c41[1] - _u13[1]), _u13[1]), _u13], pcbnew.B_Cu, _P, 0.5)
_poly([_V2, _rel(15.0, 228.6), _rel(14.0, 227.6), _V3, _rel(4.0, 227.6), (cx, _rel(0, 227.6)[1] + (_rel(4.0, 0)[0] - cx)), (cx, y1)], pcbnew.F_Cu, _P, 0.5)
_poly([_V3, _pad("R7", "1")], pcbnew.B_Cu, _P, 0.5)
_r61 = _pad("R6", "1"); _r81 = _pad("R8", "1")
_poly([_V3, (_r61[0] + (_V3[1] - _r61[1]), _V3[1]), _r61], pcbnew.B_Cu, _P, 0.5)
_poly([_V3, (_r81[0] - (_V3[1] - _r81[1]), _V3[1]), _r81], pcbnew.B_Cu, _P, 0.5)
_V2b = (_c41[0], _V2[1])
_poly([_V2, _V2b], pcbnew.F_Cu, _P, 0.65)
add_via(board, _V2b[0], _V2b[1], _P, 0.8, 0.4); added += 1
for _v in (_V1, _V2, _V3, _V4):
    add_via(board, _v[0], _v[1], _P, 0.8, 0.4); added += 1
# +15V: Sicherung -> PD-Widerstaende -> Wandler-Eingang
_f2 = [pos(p.GetPosition()) for p in board.FindFootprintByReference("F1").Pads() if p.GetNetname() == "+15V"][0]
_y15 = 40 + 226.2
_c211 = _pad("C21", "1")
_xa = _f2[0] + (_f2[1] - _y15)
_poly([_f2, (_xa, _y15), (_c211[0] - (_y15 - _c211[1]), _y15), _c211], pcbnew.B_Cu, "+15V", 0.8)
_r20 = _pad("R20", "1"); _r21 = _pad("R21", "1")
_poly([_r20, (_r20[0], _y15), (_xa, _y15)], pcbnew.B_Cu, "+15V", 0.8)
_poly([_r21, (_r21[0], _y15)], pcbnew.B_Cu, "+15V", 0.8)
# PD_VDD: U6 Pin 3..1 -> C20 -> Via. Die Versorgung von R20 laeuft ueber den Kondensator zum Pin (DEC-002, DEC-009)
_NV = [n for n in map(str, board.GetNetsByName().keys()) if n.endswith("/PD_VDD")][0]
_u61, _c201 = _pad("U6", "1"), _pad("C20", "1")
_dv = _c201[0] - _u61[0]
assert _dv > 0, "C20 Pad 1 muss rechts unter U6 Pin 1 liegen"
_poly([_pad("U6", "3"), _u61, (_u61[0], _u61[1] + 1.0), (_c201[0], _u61[1] + 1.0 + _dv), _c201], pcbnew.B_Cu, _NV, 0.3)
_vv = (_c201[0] + 0.175, _c201[1] + 1.1)
_poly([_c201, (_c201[0], _c201[1] + 0.925), _vv], pcbnew.B_Cu, _NV, 0.3)
add_via(board, _vv[0], _vv[1], _NV, 0.7, 0.3); added += 1
_u69 = _pad("U6", "9"); _u611 = _pad("U6", "11")
_poly([(_u611[0] + 1.0, _u69[1]), _u69, (_u69[0] + 1.4, _u69[1])], pcbnew.B_Cu, "GND", 0.3)
# EN und PD_GOOD: lange Wege quer ueber den Streifen auf der Oberseite
_NE = [n for n in map(str, board.GetNetsByName().keys()) if n.endswith("/EN")][0]
_r2 = _pad("R3", "2"); _ve1 = (_r2[0], _r2[1] - 2.3); _sw = [pos(p.GetPosition()) for p in board.FindFootprintByReference("SW1").Pads() if p.GetNetname() == _NE]
_sw1 = min(_sw, key=lambda q: abs(q[1] - (40 + 219)) + q[0] * 0.001); _ve2 = (_sw1[0], 40 + 220.3)
_poly([_r2, _ve1], pcbnew.B_Cu, _NE, 0.25); _poly([_ve1, (_ve1[0] + (40 + 220.3 - _ve1[1]), 40 + 220.3), _ve2], pcbnew.F_Cu, _NE, 0.25); _poly([_ve2, _sw1], pcbnew.B_Cu, _NE, 0.25)
_p34 = _pad("U1", "34"); _pg1 = (_p34[0] + 1.0, _p34[1] + 0.25); _u610 = _pad("U6", "10"); _pg2 = _rel(75.3, 224.9)
_poly([_p34, (_pg1[0] - 0.25, _p34[1]), _pg1], pcbnew.B_Cu, "PD_GOOD", 0.2)
_poly([_pg1, (_pg1[0], _rel(0, 220.8)[1]), _rel(75.3, 220.8), _pg2], pcbnew.F_Cu, "PD_GOOD", 0.2)
_poly([_pg2, (_u610[0] + (_pg2[1] - _u610[1]), _pg2[1]), _u610], pcbnew.B_Cu, "PD_GOOD", 0.2)
for _v, _n in ((_ve1, _NE), (_ve2, _NE), (_pg1, "PD_GOOD"), (_pg2, "PD_GOOD")):
    add_via(board, _v[0], _v[1], _n, 0.7, 0.3); added += 1
# SW1: beide Pads 1 durchverbinden
_poly([sorted(_sw)[0], sorted(_sw)[-1]], pcbnew.B_Cu, _NE, 0.25)
# I2C an U5: unter der Antennen-Sperrflaeche (y >= 229.25) unten nach Osten, an R6-R8 vorbei
_NA, _NC = [[n for n in map(str, board.GetNetsByName().keys()) if n.endswith(e)][0] for e in ("/SDA", "/SCL")]
_u54 = _pad("U5", "4"); _u56 = _pad("U5", "6"); _r82 = _pad("R8", "2")
_sc = _rel(8.9, 228.9); _sa = _rel(9.9, 229.9); _sa2 = _rel(15.0, 222.98)
_poly([_u56, (_u56[0], _rel(0, 229.6)[1]), _rel(8.0, 228.9), _sc], pcbnew.F_Cu, _NC, 0.2)
_poly([_sc, _rel(9.5, 228.3), _rel(14.1, 228.3), _rel(14.4, 228.0), (_rel(14.4, 0)[0], _r82[1] + 0.9), _r82], pcbnew.B_Cu, _NC, 0.2)
_poly([_u54, _rel(9.4, 231.5), _rel(9.9, 231.0), _sa], pcbnew.F_Cu, _NA, 0.2)
_poly([_sa, _rel(9.9, 229.3), _rel(10.4, 228.8), _rel(14.6, 228.8), _rel(15.0, 228.4), _sa2], pcbnew.B_Cu, _NA, 0.2)
# I2C komplett bis U1: der Router laesst diese Stuecke sonst offen
_r72 = _pad("R7", "2"); _u15 = _pad("U1", "5"); _u16 = _pad("U1", "6")
_a1 = (_r72[0], _sa2[1]); _a2 = _rel(24.89, 223.28)
_poly([_r72, _a1], pcbnew.B_Cu, _NA, 0.2)
_poly([_a1, _sa2, _rel(24.59, 222.98), _a2], pcbnew.F_Cu, _NA, 0.2)
_poly([_a2, (_a2[0], _u15[1] - 0.37), (_a2[0] + 0.37, _u15[1]), _u15], pcbnew.B_Cu, _NA, 0.2)
_c1 = (_r82[0], _rel(0, 221.6)[1]); _c2 = _rel(24.66, 221.6)
_poly([_r82, _c1], pcbnew.B_Cu, _NC, 0.2)
_poly([_c1, _c2], pcbnew.F_Cu, _NC, 0.2)
_poly([_c2, (_c2[0], _u16[1] - 1.16), (_c2[0] + 1.16, _u16[1]), _u16], pcbnew.B_Cu, _NC, 0.2)
for _v, _n in ((_a1, _NA), (_a2, _NA), (_c1, _NC), (_c2, _NC)):
    add_via(board, _v[0], _v[1], _n, 0.7, 0.3); added += 1
for _v, _n in ((_sc, _NC), (_sa, _NA), (_sa2, _NA)):
    add_via(board, _v[0], _v[1], _n, 0.7, 0.3); added += 1
print("power vias", added)
pcbnew.SaveBoard(PCB, board)

# ---------------------------------------------------------------- 2. Temp-Board fuer Freerouting
tmpd = tempfile.mkdtemp(prefix="wortuhr_fr_")
tmp_pcb = os.path.join(tmpd, "route.kicad_pcb")
tb = pcbnew.LoadBoard(PCB)
for z in list(tb.Zones()):
    tb.Remove(z)
for t in tb.GetTracks():
    t.SetLocked(True)
# Oberseite (= +5V-Flaeche) im LED-Bereich fuer neue Leiterbahnen sperren,
# damit die Flaeche nicht in Inseln zerfaellt; oben nur im Rahmenstreifen (y > 227.5) routen.
def top_keepout(x0, y0, x1, y1):
    ko = pcbnew.ZONE(tb)
    ko.SetIsRuleArea(True); ko.SetDoNotAllowTracks(True); ko.SetDoNotAllowVias(False)
    ko.SetDoNotAllowZoneFills(False); ko.SetDoNotAllowPads(False); ko.SetDoNotAllowFootprints(False)
    ko.SetLayer(pcbnew.F_Cu)
    o = ko.Outline(); o.NewOutline()
    for _x, _y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        o.Append(mm(40 + _x), mm(40 + _y))
    tb.Add(ko)


def buck_keepout(layer):
    ko = pcbnew.ZONE(tb)
    ko.SetIsRuleArea(True); ko.SetDoNotAllowTracks(True); ko.SetDoNotAllowVias(True)
    ko.SetDoNotAllowZoneFills(False); ko.SetDoNotAllowPads(False); ko.SetDoNotAllowFootprints(False)
    ko.SetLayer(layer)
    o = ko.Outline(); o.NewOutline()
    for _x, _y in [(84.0, 216.0), (116.0, 216.0), (116.0, 231.0), (84.0, 231.0)]:
        o.Append(mm(40 + _x), mm(40 + _y))
    tb.Add(ko)


buck_keepout(pcbnew.B_Cu); buck_keepout(pcbnew.F_Cu)     # Wandler ist von Hand verlegt
top_keepout(0, 0, 240, 205.0)            # LED-Feld oberhalb des Masterstreifens
top_keepout(140, 205.0, 240, 240)        # rechter Teil der untersten Reihe
for _k in range(4):                      # LED-Gruppen der untersten Reihe im Masterstreifen
    _cx = D.cell_center(_k, 5)[0]
    top_keepout(_cx - 13.0, 204.0, _cx + 13.0, 219.0)
nonet = tb.FindNet("")
# nur Signalnetze der Master-Teile routen; alles andere wird netzloses Hindernis
ROUTE = set()
for fp in tb.GetFootprints():
    if fp.GetReference() in MASTER:
        ROUTE |= {p.GetNetname() for p in fp.Pads()}
ROUTE -= {""}
PWR = {"+5V", "GND"}
ROUTE = {n for n in ROUTE if not n.startswith("unconnected") and n not in PWR}   # +5V/GND laufen ueber die Flaechen
print("route nets:", sorted(ROUTE))
for fp in tb.GetFootprints():
    m = fp.GetReference() in MASTER
    for p in fp.Pads():
        n = p.GetNetname()
        if n not in ROUTE:
            p.SetNet(nonet)
for i, t in enumerate(list(tb.GetTracks())):
    n = t.GetNetname()
    if n not in ROUTE:
        ni = pcbnew.NETINFO_ITEM(tb, "OBST_%d" % i, 100000 + i)   # eigener Code, sonst Kollision mit vorhandenen Netzen
        tb.Add(ni)
        t.SetNet(ni)
ns = tb.GetDesignSettings().m_NetSettings
for name, w in POWER_W.items():
    nc = pcbnew.NETCLASS("P_" + name.strip("/+"))
    nc.SetTrackWidth(mm(w)); nc.SetClearance(mm(0.2)); nc.SetViaDiameter(mm(0.8)); nc.SetViaDrill(mm(0.4))
    ns.SetNetclass(nc.GetName(), nc)
    ns.SetNetclassPatternAssignment(name, nc.GetName())
_dflt = ns.GetDefaultNetclass()          # Standard-Via fuer Freerouting: 0.7/0.3 mm (Restring 0.2 mm, JLCPCB)
_dflt.SetViaDiameter(mm(0.7)); _dflt.SetViaDrill(mm(0.3))
ns.RecomputeEffectiveNetclasses()
pcbnew.SaveBoard(tmp_pcb, tb)
tb = pcbnew.LoadBoard(tmp_pcb)
dsn, ses = os.path.join(tmpd, "route.dsn"), os.path.join(tmpd, "route.ses")
assert pcbnew.ExportSpecctraDSN(tb, dsn), "DSN export failed"
print("routing ...", dsn)
# Zustand fuer route_finish.py (getrennte Schritte: Routing laeuft ueber den Freerouting-MCP)
import json
STATE = os.path.join(tempfile.gettempdir(), "wortuhr_route_state.json")
json.dump({"tmp_pcb": tmp_pcb, "dsn": dsn, "ses": ses, "route": sorted(ROUTE), "created": sorted(CREATED)}, open(STATE, "w"))
print("STATE", STATE); print("DSN", dsn); print("SES", ses)
if "--prepare" in sys.argv:
    sys.exit(0)
# Ohne --prepare: lokaler Lauf mit derselben Engine (build_pcb.py)
JAVA, JAR = kicad_env.freerouting()
FR_ARGS = ["--router.autorouter.max_passes=100", "--router.automatic_neckdown=false", "--gui.enabled=false"]
r = subprocess.run([JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-l", "en"] + FR_ARGS, capture_output=True, text=True, timeout=3600)
print("freerouting rc", r.returncode, r.stdout[-800:], r.stderr[-400:])
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "route_finish.py")], check=True)
