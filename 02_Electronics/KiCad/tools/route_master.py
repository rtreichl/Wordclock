# -*- coding: utf-8 -*-
"""Routet die Master-Elektronik mit Freerouting (nach gen_pcb.py ausfuehren).

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

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PRJ, "WortUhr.kicad_pcb")
HOME = os.path.expanduser("~/.kicad-mcp")
JAVA = glob.glob(os.path.join(HOME, "jre", "*", "bin", "java.exe"))[0]
JAR = os.path.join(HOME, "freerouting.jar")
MASTER = set(D.MASTER_PLACE)
POWER_W = {"VBUS": 0.6, "+15V": 0.8, "+3V3": 0.5, "USB_DP": 0.2, "USB_DN": 0.2}   # ROUTING_GUIDE.md: Power >= 0,5 mm
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
        base = math.degrees(math.atan2(y - center[1], x - center[0]))
    for d in (1.4, 1.8, 2.3, 2.8, 3.4, 4.0):
        for k in range(12):
            ang = base + (k + 1) // 2 * 30 * (1 if k % 2 else -1)
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
        if ref == "U5" or (ref == "U7" and p.GetNumber() == "5") or (ref == "U3" and p.GetNumber() == "5"):
            continue
        need = (n == "+5V") or (n == "GND" and top)
        if not need:
            continue
        # Dioden-Kathoden / Hohlbuchse: mehrere Vias fuer Strom
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
# J1 VBUS: 0,6 mm passt nur gerade aus den Pins heraus -> feste Anschluesse, Vias und 0,6-mm-Steg oben (PWR-001)
_vb = sorted(pos(p.GetPosition()) for p in board.FindFootprintByReference("J1").Pads() if p.GetNetname() == "VBUS")
_xs = sorted({round(x, 3) for x, y in _vb}); _y = min(y for x, y in _vb) - 2.2
for _x in _xs:
    add_track(board, [(x, y) for x, y in _vb if abs(x - _x) < 0.01][0], (_x, _y), "VBUS", pcbnew.B_Cu, 0.6)
    add_via(board, _x, _y, "VBUS", 0.8, 0.4); added += 1
_yb = _y - 2.5      # Steg oberhalb lassen: darunter wechseln die USB-Datenleitungen die Lage
add_track(board, (_xs[0], _y), (_xs[0], _yb), "VBUS", pcbnew.F_Cu, 0.6)
add_track(board, (_xs[-1], _y), (_xs[-1], _yb), "VBUS", pcbnew.F_Cu, 0.6)
add_track(board, (_xs[0], _yb), (_xs[-1], _yb), "VBUS", pcbnew.F_Cu, 0.6)
_f1 = [pos(p.GetPosition()) for p in board.FindFootprintByReference("F1").Pads() if p.GetNetname() == "VBUS"][0]
_fx = 40 + 68.6
for a_, c_ in zip([(_xs[-1], _y), (_xs[-1] + 1.45, _y + 1.45), (_fx, _y + 1.45), (_fx, _f1[1])], [(_xs[-1] + 1.45, _y + 1.45), (_fx, _y + 1.45), (_fx, _f1[1])]):
    add_track(board, a_, c_, "VBUS", pcbnew.F_Cu, 0.6)
add_via(board, _fx, _f1[1], "VBUS", 0.8, 0.4); added += 1
add_track(board, (_fx, _f1[1]), _f1, "VBUS", pcbnew.B_Cu, 0.6)
NET_SW = [n for n in board.GetNetsByName().keys() if str(n).endswith("BUCK_SW")][0]
NET_SW = str(NET_SW)
def _pad(ref, num):
    return [pos(p.GetPosition()) for p in board.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def _rel(x, y):
    return (x + 40.0, y + 40.0)
def _poly(pts, layer, net, w):
    for a_, c_ in zip(pts, pts[1:]):
        add_track(board, a_, c_, net, layer, w)
# Wandler: kurze, breite Wege (Datenblatt-Layout)
_sw = _pad("U7", "7"); _swa = (_sw[0] + 2.35, _sw[1])
_poly([_sw, _swa], pcbnew.B_Cu, NET_SW, 0.3); _poly([_swa, _pad("L1", "1")], pcbnew.B_Cu, NET_SW, 1.5)
_c = _pad("C21", "1"); _u = _pad("U7", "1")
_ua = (_u[0] - 1.3, _u[1])
_poly([_c, (_c[0], _u[1]), _ua], pcbnew.B_Cu, "+15V", 0.8); _poly([_ua, _u], pcbnew.B_Cu, "+15V", 0.3)
# U7: BST-Kondensator, Masse der feinen Pins
_b8 = _pad("U7", "8"); _c1 = _pad("C26", "1"); _c2 = _pad("C26", "2")
_poly([_b8, (_b8[0] + 0.4, _b8[1] + 0.7), _c1], pcbnew.B_Cu, [n for n in map(str, board.GetNetsByName().keys()) if n.endswith("BUCK_BST")][0], 0.25)
_poly([_c2, (_c2[0], _swa[1])], pcbnew.B_Cu, NET_SW, 0.5)
_p4 = _pad("U7", "4"); _p10 = _pad("U7", "10")
_poly([_p4, (_p4[0], _p4[1] - 0.8), (_p4[0] - 0.9, _p4[1] - 1.7)], pcbnew.B_Cu, "GND", 0.25)
pass
_v5 = _pad("U7", "5"); _sg = -1 if _v5[1] < 40 + 224.0 else 1
_v5a = (_v5[0], _v5[1] + _sg * 1.7); _v5b = (_v5[0], _v5[1] + _sg * 2.4)
_poly([_v5, _v5a], pcbnew.B_Cu, "+5V", 0.25); _poly([_v5a, _v5b], pcbnew.B_Cu, "+5V", 0.65)
add_via(board, _v5b[0], _v5b[1], "+5V", 0.8, 0.4); added += 1
_u35 = _pad("U3", "5"); _uv = _rel(60.1, 219.5)
add_track(board, _u35, _uv, "+5V", pcbnew.B_Cu, 0.4); add_via(board, _uv[0], _uv[1], "+5V", 0.8, 0.4); added += 1
# +3V3 fest (PWR-001, Punkt 3: von aussen ueber die Kondensatoren zum Pin)
_V1, _V2, _V3, _V4 = _rel(45.2, 224.1), _rel(21.9, 228.6), _rel(11.5, 227.6), _rel(22.5, 224.1)
_P = "+3V3"
_poly([_pad("C3", "1"), _pad("U2", "5"), _rel(49.9, 226.7), _rel(46.6, 226.7), _rel(45.2, 225.3), _V1], pcbnew.B_Cu, _P, 0.5)
_poly([_V1, _pad("R3", "1")], pcbnew.B_Cu, _P, 0.5)
_T = _rel(26.1, 224.1)
_poly([_V1, _T, _rel(21.9, 228.3), _V2], pcbnew.F_Cu, _P, 0.5)
_poly([_T, _V4], pcbnew.F_Cu, _P, 0.5)
_poly([_V4, _pad("R4", "1")], pcbnew.B_Cu, _P, 0.5)
_poly([_V2, _pad("C9", "1")], pcbnew.B_Cu, _P, 0.5)
_poly([_V2, _pad("C4", "1"), _rel(24.6, 225.7), _pad("U1", "3")], pcbnew.B_Cu, _P, 0.5)
_poly([_V2, _rel(15.0, 228.6), _V3, _rel(4.0, 227.6), _rel(2.73, 228.9), (cx, y1)], pcbnew.F_Cu, _P, 0.5)
_poly([_V3, _pad("R7", "1")], pcbnew.B_Cu, _P, 0.5)
_poly([_V3, _rel(10.2, 227.6), _pad("R6", "1")], pcbnew.B_Cu, _P, 0.5)
_poly([_V3, _rel(12.8, 227.6), _pad("R8", "1")], pcbnew.B_Cu, _P, 0.5)
for _v in (_V1, _V2, _V3, _V4):
    add_via(board, _v[0], _v[1], _P, 0.8, 0.4); added += 1
_NV = [n for n in map(str, board.GetNetsByName().keys()) if n.endswith("BUCK_VCC")][0]
_p9 = _pad("U7", "9"); _c = [pos(p.GetPosition()) for p in board.FindFootprintByReference("C27").Pads() if p.GetNetname() == _NV][0]
_poly([_p9, (_p9[0], _c[1]), _c], pcbnew.B_Cu, _NV, 0.25)
# Masse-Inseln an feinen Pins an die Flaeche anbinden
_gp = lambda ref, num: _pad(ref, num)
_c27g = [pos(p.GetPosition()) for p in board.FindFootprintByReference("C27").Pads() if p.GetNetname() == "GND"][0]
_c22g = [pos(p.GetPosition()) for p in board.FindFootprintByReference("C22").Pads() if p.GetNetname() == "GND"][0]
_poly([_p10, (_p10[0], _p10[1] + 1.2), _c27g, _c22g], pcbnew.B_Cu, "GND", 0.25)
_u32 = _pad("U3", "2"); _g1 = (_u32[0] + 1.46, _u32[1]); _g2 = (_g1[0] + 1.8, _g1[1])
_poly([_u32, _g1], pcbnew.B_Cu, "GND", 0.3); _poly([_g1, _g2], pcbnew.F_Cu, "GND", 0.4)      # kurze Bruecke ueber die USB-Leitungen
add_via(board, _g1[0], _g1[1], "GND", 0.7, 0.3); add_via(board, _g2[0], _g2[1], "GND", 0.7, 0.3); added += 2
# U1: Masse-Pins der Ostseite innerhalb des USB-Paars an die Massefelder unter dem Modul
_gu = [(p.GetNumber(), pos(p.GetPosition())) for p in board.FindFootprintByReference("U1").Pads() if p.GetNetname() == "GND"]
_east = [q for n, q in _gu if abs(q[0] - (40 + 40.0)) < 0.5 and q[1] < 40 + 218]
_inner = [q for n, q in _gu if 40 + 28 < q[0] < 40 + 38 and 40 + 217 < q[1] < 40 + 230]
print("U1 Ost-GND", _east, "innen", len(_inner))
# +15V: Sicherung -> PD-Widerstaende -> Wandler-Eingang
_f2 = [pos(p.GetPosition()) for p in board.FindFootprintByReference("F1").Pads() if p.GetNetname() == "+15V"][0]
_y15 = 40 + 227.0
_poly([_f2, _rel(76.5, 227.0), _rel(85.0, 227.0), _pad("C21", "1")], pcbnew.B_Cu, "+15V", 0.8)
_poly([_rel(76.5, 227.0), _pad("R20", "1")], pcbnew.B_Cu, "+15V", 0.8)
_poly([_rel(78.5, 227.0), _pad("R21", "1")], pcbnew.B_Cu, "+15V", 0.8)
_poly([_rel(85.0, 227.0), _pad("C22", "1")], pcbnew.B_Cu, "+15V", 0.8)
_u69 = _pad("U6", "9"); _u611 = _pad("U6", "11")
_poly([(_u611[0] + 1.0, _u69[1]), _u69, (_u69[0] + 1.4, _u69[1])], pcbnew.B_Cu, "GND", 0.3)
# EN und PD_GOOD: lange Wege quer ueber den Streifen auf der Oberseite
_NE = [n for n in map(str, board.GetNetsByName().keys()) if n.endswith("/EN")][0]
_r2 = _pad("R3", "2"); _ve1 = (_r2[0], _r2[1] - 2.3); _sw = [pos(p.GetPosition()) for p in board.FindFootprintByReference("SW1").Pads() if p.GetNetname() == _NE]
_sw1 = min(_sw, key=lambda q: abs(q[1] - (40 + 219)) + q[0] * 0.001); _ve2 = (_sw1[0], 40 + 220.3)
_poly([_r2, _ve1], pcbnew.B_Cu, _NE, 0.25); _poly([_ve1, (_ve1[0] + 0.5, 40 + 220.3), _ve2], pcbnew.F_Cu, _NE, 0.25); _poly([_ve2, _sw1], pcbnew.B_Cu, _NE, 0.25)
_p34 = _pad("U1", "34"); _pg1 = _rel(41.0, 218.3); _u610 = _pad("U6", "10"); _pg2 = _rel(75.3, 224.9)
_poly([_p34, _pg1], pcbnew.B_Cu, "PD_GOOD", 0.2); _poly([_pg1, _rel(41.0, 220.9), _rel(75.3, 220.9), _pg2], pcbnew.F_Cu, "PD_GOOD", 0.2); _poly([_pg2, _u610], pcbnew.B_Cu, "PD_GOOD", 0.2)
for _v, _n in ((_ve1, _NE), (_ve2, _NE), (_pg1, "PD_GOOD"), (_pg2, "PD_GOOD")):
    add_via(board, _v[0], _v[1], _n, 0.7, 0.3); added += 1
# USB als Paar: w 0,45 / s 0,15 mm auf der Unterseite
_dn, _dp = _pad("U3", "6"), _pad("U3", "4")
_poly([_dn, _rel(59.6, 218.55), _rel(58.25, 217.2), _rel(43.0, 217.2), _rel(42.6, 216.8), _rel(42.6, 213.0), _rel(42.2, 212.6), _rel(33.4, 212.6), _rel(33.0, 213.0), _pad("U1", "23")], pcbnew.B_Cu, "USB_DN", 0.45)
_poly([_dp, _rel(59.6, 220.45), _rel(56.95, 217.8), _rel(42.4, 217.8), _rel(42.0, 217.4), _rel(42.0, 213.6), _rel(41.6, 213.2), _rel(34.25, 213.2), _rel(33.85, 213.6), _pad("U1", "24")], pcbnew.B_Cu, "USB_DP", 0.45)
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
FR_ARGS = ["--router.autorouter.max_passes=100", "--router.automatic_neckdown=false", "--gui.enabled=false"]
r = subprocess.run([JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-l", "en"] + FR_ARGS, capture_output=True, text=True, timeout=3600)
print("freerouting rc", r.returncode, r.stdout[-800:], r.stderr[-400:])
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "route_finish.py")], check=True)
