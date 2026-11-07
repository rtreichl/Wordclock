# -*- coding: utf-8 -*-
"""Erzeugt WortUhr.kicad_pcb aus design.py (mit KiCad-Python ausfuehren).

- Platzierung aller Bauteile (LED-Feld oben, Master-Teile unten)
- Routing des kompletten LED-Feldes (Datenkette, GND-Vias, Bruecken)
- +5V-Flaeche oben, GND-Flaeche unten, Antennen-Sperrflaeche
Die Master-Elektronik ist platziert; ihre Signale sind (noch) nicht geroutet.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import design as D

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIFP = r"P:/Program Files/KiCad/10.0/share/kicad/footprints/"
O = 40.0                      # KiCad-Koordinate des Uhrmittelpunkts (x und y)
W_SIG, W_GND = 0.3, 0.4
VIA_D, VIA_DRILL = 0.6, 0.3

mm = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(O + x), mm(O + y))


board = pcbnew.BOARD()
board.SetCopperLayerCount(2)
ds = board.GetDesignSettings()
ds.SetBoardThickness(mm(1.6))
ds.m_TrackMinWidth = mm(0.1)          # JLCPCB 2 Lagen: min. 0.1 mm
ds.m_CopperEdgeClearance = mm(0.45)
nets = {}


def net(name):
    return rawnet("/" + name)


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(PRJ, lib + ".pretty") if lib == "WortUhr" else KIFP + lib + ".pretty"
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


placed = {}


def place(part, x, y, rot, side="F"):
    fp = load_fp(part.fp)
    fp.SetReference(part.ref)
    fp.SetValue(part.value)
    fp.SetPath(pcbnew.KIID_PATH("/" + part.uuid))
    for k, v in dict(part.extra, Variante=part.variant).items():
        f = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, k)
        f.SetText(v); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
        fp.Add(f)
    board.Add(fp)
    fp.SetPosition(V(x, y))
    if side == "B":
        fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        n = PADNET.get((part.ref, p.GetNumber()))
        if n:
            p.SetNet(rawnet(n))
        elif p.GetNumber() not in ("", "MP"):
            pass  # z.B. USB-C SBU-Pads ohne Symbolpin
    placed[part.ref] = fp
    return fp


def pad_xy(ref, num):
    for p in placed[ref].Pads():
        if p.GetNumber() == num:
            q = p.GetPosition()
            return (pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O)
    raise KeyError(ref + "." + num)


def track(pts, netname, layer=pcbnew.F_Cu, w=W_SIG):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2))
        t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net(netname))
        board.Add(t)


def via(x, y, netname, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(net(netname))
    board.Add(v)


def line(layer, a, b, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*b))
    s.SetLayer(layer); s.SetWidth(mm(w)); board.Add(s)


def text(layer, s, x, y, size=1.5, rot=0, mirror=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15))
    t.SetTextAngleDegrees(rot); t.SetMirrored(mirror)
    board.Add(t)


parts = {p.ref: p for p in D.build_parts()}

# Pad-Netze direkt aus der Schaltplan-Netzliste (garantiert Paritaet)
import subprocess, re, tempfile
_nl = os.path.join(tempfile.gettempdir(), "wortuhr_net.net")
subprocess.run([r"P:/Program Files/KiCad/10.0/bin/kicad-cli.exe", "sch", "export", "netlist", "-o", _nl,
                os.path.join(PRJ, "WortUhr.kicad_sch")], check=True, capture_output=True)
_t = open(_nl, encoding="utf-8").read()
PADNET = {}
for _blk in re.split(r"\(net\s+\(code ", _t[_t.find("(nets"):])[1:]:
    _name = re.search(r'\(name "([^"]*)"\)', _blk).group(1)
    for _r, _p in re.findall(r'\(ref "([^"]*)"\)\s*\(pin "([^"]*)"', _blk):
        PADNET[(_r, _p)] = _name


def rawnet(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(board, name, len(nets) + 1)
        board.Add(ni)
        nets[name] = ni
    return nets[name]

# ---------------------------------------------------------------- Umriss
R = 6.0
a, b = D.BOARD_MIN, D.BOARD_MAX
line(pcbnew.Edge_Cuts, (a, a), (b, a)); line(pcbnew.Edge_Cuts, (b, a), (b, b - R))
line(pcbnew.Edge_Cuts, (b - R, b), (a, b)); line(pcbnew.Edge_Cuts, (a, b), (a, a))
arc = pcbnew.PCB_SHAPE(board); arc.SetShape(pcbnew.SHAPE_T_ARC)
arc.SetCenter(V(b - R, b - R)); arc.SetStart(V(b, b - R)); arc.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
arc.SetLayer(pcbnew.Edge_Cuts); arc.SetWidth(mm(0.1)); board.Add(arc)

# ---------------------------------------------------------------- LED-Feld
# Kammer-lokale Geometrie fuer Laufrichtung links->rechts (dir=+1);
# dir=-1 = Punktspiegelung an der Kammermitte (alles um 180° gedreht).
via_in, via_out = {}, {}
for c, ((k, j), d) in enumerate(D.PATH):
    cx, cy = D.cell_center(k, j)
    T = lambda x, y: (cx + d * x, cy + d * y)
    rot = 180 if d > 0 else 0          # LEDs
    rp = 0 if d > 0 else 180           # Kondensatoren / Bruecken
    nA, nB = 2 * c + 1, 2 * c + 2
    pA, pB = parts[f"D{nA}"], parts[f"D{nB}"]
    a_out, b_out = pA.pins["2"], pB.pins["2"]
    a_in = pA.pins["4"]
    place(pA, *T(-D.LED_OFF, 0), rot)
    place(pB, *T(+D.LED_OFF, 0), rot)
    place(parts[f"C{100+nA}"], *T(-7.5, 4.6), rp)      # Pad1 (GND) links, Pad2 (+5V) rechts
    place(parts[f"C{100+nB}"], *T(7.5, -4.6), rp)
    place(parts[f"JP{c+1}"], *T(7.5, 4.4), rp)
    for r in (f"D{nA}", f"D{nB}", f"C{100+nA}", f"C{100+nB}", f"JP{c+1}"):
        placed[r].Reference().SetVisible(False)
    # Daten innerhalb der Kammer: A.DOUT -> B.DIN
    track([T(-5.05, -1.65), T(0.0, -1.65), T(3.3, 1.65), T(5.05, 1.65)], a_out)
    # Ein-/Ausgangs-Vias
    track([T(-9.95, 1.65), T(-11.7, 1.65)], a_in); via(*T(-11.7, 1.65), a_in); via_in[c] = T(-11.7, 1.65)
    track([T(9.95, -1.65), T(11.7, -1.65)], b_out); via(*T(11.7, -1.65), b_out); via_out[c] = T(11.7, -1.65)
    # GND
    track([T(-9.95, -1.65), T(-9.95, -3.5)], "GND", w=W_GND); via(*T(-9.95, -3.5), "GND")
    track([T(5.05, -1.65), T(5.05, -3.5)], "GND", w=W_GND); via(*T(5.05, -3.5), "GND")
    track([T(6.72, -4.6), T(5.05, -3.5)], "GND", w=W_GND)
    track([T(-8.28, 4.6), T(-8.28, 6.1)], "GND", w=W_GND); via(*T(-8.28, 6.1), "GND")
    # Bruecke JP: Pad1 -> B.DIN, Pad2 -> B.DOUT
    track([T(6.85, 4.4), T(5.05, 2.6), T(5.05, 1.65)], a_out)
    track([T(8.15, 4.4), T(11.7, 4.4), T(11.7, -1.65)], b_out)

# Spruenge zwischen den Kammern (Unterseite)
for c in range(35):
    (k1, j1), _ = D.PATH[c]; (k2, j2), _ = D.PATH[c + 1]
    p1, p2 = via_out[c], via_in[c + 1]
    n = parts[f"D{2*c+2}"].pins["2"]
    c1, c2 = D.cell_center(k1, j1), D.cell_center(k2, j2)
    if j1 == j2:
        xm = (c1[0] + c2[0]) / 2
        pts = [p1, (xm, p1[1]), (xm, p2[1]), p2]
    elif abs(p1[0] - p2[0]) < 1e-6:
        pts = [p1, p2]
    else:
        ym = (c1[1] + c2[1]) / 2
        pts = [p1, (p1[0], ym), (p2[0], ym), p2]
    track(pts, n, pcbnew.B_Cu)

# ---------------------------------------------------------------- Verbinder J_IN / J_OUT
# J3 (J_IN) am linken Rand, Steckseite nach links; J4 (J_OUT) am oberen Rand, Steckseite nach oben.
place(parts["J3"], 8.0, D.CONN_POS, 90, "B")
place(parts["J4"], D.CONN_POS, 8.0, 0, "B")


def front_dir(ref):
    """Richtung Signalpads -> Montagepads (= Steckrichtung) zur Kontrolle."""
    fp = placed[ref]
    sig = [p for p in fp.Pads() if p.GetNumber() not in ("MP", "")]
    mp = [p for p in fp.Pads() if p.GetNumber() == "MP"]
    sx = sum(pcbnew.ToMM(p.GetPosition().x) for p in sig) / len(sig); sy = sum(pcbnew.ToMM(p.GetPosition().y) for p in sig) / len(sig)
    mx = sum(pcbnew.ToMM(p.GetPosition().x) for p in mp) / len(mp); my = sum(pcbnew.ToMM(p.GetPosition().y) for p in mp) / len(mp)
    return round(mx - sx, 2), round(my - sy, 2)


print("J3 front", front_dir("J3"), "J4 front", front_dir("J4"))

def conn_5v(ref):
    """+5V-Pads per Via (zwischen Pad und Steckseite) auf die obere +5V-Flaeche."""
    fx, fy = front_dir(ref)
    L = math.hypot(fx, fy); ux, uy = fx / L, fy / L
    for pn in ("1", "2"):
        x, y = pad_xy(ref, pn)
        vxx, vyy = x + ux * 3.4, y + uy * 3.4
        track([(x, y), (vxx, vyy)], "+5V", pcbnew.B_Cu, w=0.8); via(vxx, vyy, "+5V", 0.8, 0.4)


# J_IN: Pin3 -> erster LED-Eingang (Via)
x3, y3 = pad_xy("J3", "3")
vx, vy = via_in[0]
track([(x3, y3), (17.0, y3), (17.0, vy), (vx, vy)], "DIN", pcbnew.B_Cu)
conn_5v("J3")
# J_OUT: letzte Kammer -> Pin3 (rechts am Feld vorbei, dann oberhalb der Kammer (5,0))
x3, y3 = pad_xy("J4", "3")
vx, vy = via_out[35]
xr = D.cell_center(5, 0)[0] + D.C0 - 0.5
track([(vx, vy), (xr, vy), (xr, 14.6), (x3, 14.6), (x3, y3)], "DOUT", pcbnew.B_Cu)
conn_5v("J4")

# Puffer-Elko (jede Platine) unter der Wand nahe J_IN
place(parts["C1"], 26.0, D.CONN_POS, 0, "B")
x, y = pad_xy("C1", "1"); via(x, y - 2.2, "+5V", 0.8, 0.4); track([(x, y), (x, y - 2.2)], "+5V", pcbnew.B_Cu, w=0.8)

# Montageloecher
for i, (x, y) in enumerate(D.MOUNT_HOLES):
    place(parts[f"H{i+1}"], x, y, 0)

# ---------------------------------------------------------------- Master
for ref, (x, y, rot, side) in D.MASTER_PLACE.items():
    place(parts[ref], x, y, rot, side)
for ref in ("J1", "J2"):
    fp = placed[ref]; bb = fp.GetBoundingBox(False)
    print(ref, "bbox y", round(pcbnew.ToMM(bb.GetTop()) - O, 2), round(pcbnew.ToMM(bb.GetBottom()) - O, 2))

assert len(placed) == len(parts), set(parts) - set(placed)

# ---------------------------------------------------------------- Flaechen
def zone(layer, netname, poly, prio=0, clearance=0.3):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(net(netname)); z.SetAssignedPriority(prio)
    ol = z.Outline(); ol.NewOutline()
    for x, y in poly:
        ol.Append(mm(O + x), mm(O + y))
    z.SetLocalClearance(mm(clearance)); z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
    return z


full = [(a, a), (b, a), (b, b), (a, b)]
zone(pcbnew.F_Cu, "+5V", full)
zone(pcbnew.B_Cu, "GND", full)


# ---------------------------------------------------------------- Beschriftung
text(pcbnew.B_SilkS, "WortUhr LED-Board rev2  -  4x identisch", 117.0, 120.0, 2.0, mirror=True)
text(pcbnew.B_SilkS, "Master: U1..U5, J1, J2 bestuecken", 117.0, 124.0, 1.5, mirror=True)
text(pcbnew.B_SilkS, "JPx schliessen wenn LED B fehlt", 117.0, 127.5, 1.5, mirror=True)
text(pcbnew.B_SilkS, "J_IN", 14.0, D.CONN_POS - 9.5, 1.2, mirror=True)
text(pcbnew.B_SilkS, "J_OUT", D.CONN_POS + 11.0, 12.0, 1.2, mirror=True)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
out = os.path.join(PRJ, "WortUhr.kicad_pcb")
pcbnew.SaveBoard(out, board)
print("saved", out, "footprints", len(placed), "tracks", len(board.GetTracks()))
