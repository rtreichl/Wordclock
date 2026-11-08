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
POWER_W = {"/VBUS": 0.6, "/VDC": 1.2, "/+3V3": 0.5}   # ROUTING_GUIDE.md: Power >= 0,5 mm
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
        if ref == "U5":
            continue
        need = (n == "/+5V") or (n == "/GND" and top)
        if not need:
            continue
        # Dioden-Kathoden / Hohlbuchse: mehrere Vias fuer Strom
        count = 4 if ref in ("D73", "D74") else 1
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
# Sensor U5 (Oberseite): GND-Pins 2/3 gemeinsam nach aussen auf ein Via
u5 = board.FindFootprintByReference("U5")
pp = {p.GetNumber(): pos(p.GetPosition()) for p in u5.Pads()}
(x2, y2), (x3, y3) = pp["2"], pp["3"]
xo = x2 + 1.1
add_track(board, (x2, y2), (xo, y2), "/GND", pcbnew.F_Cu, 0.2)
add_track(board, (x3, y3), (xo, y3), "/GND", pcbnew.F_Cu, 0.2)
add_track(board, (xo, y2), (xo, y3 - 1.6), "/GND", pcbnew.F_Cu, 0.25)
add_via(board, xo, y3 - 1.6, "/GND", 0.7, 0.3); added += 1
# U5 Pin 1 (+3V3): 0,5-mm-Raster laesst keine 0,5-mm-Bahn zu -> kurzer 0,25-mm-Anschluss, Via, 0,5 mm zu C8 (direkt darunter)
x1, y1 = pp["1"]
c8 = {p.GetNumber(): pos(p.GetPosition()) for p in board.FindFootprintByReference("C8").Pads() if p.GetNetname() == "/+3V3"}
cx, cy = list(c8.values())[0]
vx3 = cx + 1.2
add_track(board, (x1, y1), (x1 + 1.1, cy), "/+3V3", pcbnew.F_Cu, 0.25)
add_track(board, (x1 + 1.1, cy), (vx3, cy), "/+3V3", pcbnew.F_Cu, 0.25)
add_via(board, vx3, cy, "/+3V3", 0.8, 0.4); added += 1
add_track(board, (vx3, cy), (cx, cy), "/+3V3", pcbnew.B_Cu, 0.5)
# J1 VBUS: 0,6 mm passt nur gerade aus den Pins heraus -> feste Anschluesse, Vias und 0,6-mm-Steg oben (PWR-001)
_vb = sorted(pos(p.GetPosition()) for p in board.FindFootprintByReference("J1").Pads() if p.GetNetname() == "/VBUS")
_xs = sorted({round(x, 3) for x, y in _vb}); _y = min(y for x, y in _vb) - 2.2
for _x in _xs:
    add_track(board, [(x, y) for x, y in _vb if abs(x - _x) < 0.01][0], (_x, _y), "/VBUS", pcbnew.B_Cu, 0.6)
    add_via(board, _x, _y, "/VBUS", 0.8, 0.4); added += 1
_yb = _y - 2.5      # Steg oberhalb lassen: darunter wechseln die USB-Datenleitungen die Lage
add_track(board, (_xs[0], _y), (_xs[0], _yb), "/VBUS", pcbnew.F_Cu, 0.6)
add_track(board, (_xs[-1], _y), (_xs[-1], _yb), "/VBUS", pcbnew.F_Cu, 0.6)
add_track(board, (_xs[0], _yb), (_xs[-1], _yb), "/VBUS", pcbnew.F_Cu, 0.6)
print("VBUS pins", _vb, "y", _y)
# +3V3-Hauptleitung fest vorgeben (PWR-001: durchgehend 0,5 mm, Autorouter streut sonst)
def _pad(ref, num):
    return [pos(p.GetPosition()) for p in board.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def _rel(x, y):
    return (x + 40.0, y + 40.0)
def _poly(pts, layer, net="/+3V3", w=0.5):
    for a_, c_ in zip(pts, pts[1:]):
        add_track(board, a_, c_, net, layer, w)
_v1, _v2, _v3 = _rel(45.2, 224.1), _rel(24.8, 225.5), _rel(4.6, 229.2)
_j1, _j2, _j3, _j4 = _rel(23.0, 225.3), _rel(4.6, 226.8), _rel(4.6, 231.4), _rel(5.5, 232.3)
_poly([_pad("C3", "1"), _pad("U2", "5"), _rel(49.9, 226.7), _rel(46.6, 226.7), _rel(45.2, 225.3), _v1], pcbnew.B_Cu)
_poly([_v1, _pad("R3", "1")], pcbnew.B_Cu)
_poly([_v1, _rel(26.1, 224.1), _rel(24.7, 225.5), _v2], pcbnew.F_Cu)
_poly([_rel(24.7, 225.5), _rel(8.1, 225.5), _v3], pcbnew.F_Cu)
_poly([_v2, _rel(25.2, 225.7), _pad("U1", "3")], pcbnew.B_Cu)
_poly([_v2, _j1, _pad("C4", "1")], pcbnew.B_Cu)
_poly([_j1, _rel(21.7, 224.0), _pad("R4", "1")], pcbnew.B_Cu)
_poly([_v3, _j2, _pad("R8", "1")], pcbnew.B_Cu)
_poly([_j2, _rel(6.0, 226.8), _pad("R6", "1")], pcbnew.B_Cu)
_poly([_v3, _j3, _pad("R7", "1")], pcbnew.B_Cu)
_poly([_j3, _j4, _pad("C8", "1")], pcbnew.B_Cu)
for _v in (_v1, _v2, _v3):
    add_via(board, _v[0], _v[1], "/+3V3", 0.8, 0.4); added += 1
# U3 Pin 5 (VBUS) auf den Steg oben
_u = _pad("U3", "5"); _vv = (_u[0] + 1.9, _u[1])
add_track(board, _u, _vv, "/VBUS", pcbnew.B_Cu, 0.6)
add_via(board, _vv[0], _vv[1], "/VBUS", 0.8, 0.4); added += 1
_poly([_vv, (_vv[0], _yb), (_xs[-1], _yb)], pcbnew.F_Cu, "/VBUS", 0.6)
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
PWR = {"/+5V", "/GND"}
ROUTE = {n for n in ROUTE if not n.startswith("unconnected")}
print("route nets:", sorted(ROUTE))
for fp in tb.GetFootprints():
    m = fp.GetReference() in MASTER
    for p in fp.Pads():
        n = p.GetNetname()
        if n not in ROUTE or (n in PWR and not m):
            p.SetNet(nonet)
for i, t in enumerate(list(tb.GetTracks())):
    n = t.GetNetname()
    if n not in ROUTE or (n in PWR and t.m_Uuid.AsString() not in CREATED):
        ni = pcbnew.NETINFO_ITEM(tb, "OBST_%d" % i, tb.GetNetCount() + 1)
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
