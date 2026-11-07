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
POWER_W = {"/VBUS": 0.6, "/VDC": 1.2, "/+3V3": 0.4}
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
r = subprocess.run([JAVA, "-jar", JAR, "-de", dsn, "-do", ses, "-mp", "60", "-l", "en"], capture_output=True, text=True, timeout=1800)
print(r.stdout[-1500:], r.stderr[-800:])
assert os.path.exists(ses), "no SES"
before = {id(t) for t in tb.GetTracks()}
assert pcbnew.ImportSpecctraSES(tb, ses), "SES import failed"

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
POUR = {"/GND": pcbnew.B_Cu, "/+5V": pcbnew.F_Cu}
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
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
print("saved")
