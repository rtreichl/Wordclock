# -*- coding: utf-8 -*-
"""Wandler (SCT2360, nach Datenblatt Figure 22) und USB-Differenzpaar von Hand legen.

Aufruf nach gen_pcb.py (KiCad-Python). Alle Leiterbahnen nur horizontal, vertikal oder in 45 Grad.
Der Rest des Master-Streifens wird danach geroutet.
"""
import os, math
import pcbnew

PCB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "WortUhr.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
mm = pcbnew.FromMM
O = 40.0
NETS = {str(k): v for k, v in b.GetNetsByName().items()}
def N(short):
    for k, v in NETS.items():
        if k == short or k.endswith("/" + short):
            return v
    raise KeyError(short)
def V(p):
    return pcbnew.VECTOR2I(mm(p[0] + O), mm(p[1] + O))
def pad(ref, num):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            q = p.GetPosition(); return (pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O)
    raise KeyError(ref + num)
def poly(pts, net, w, layer=pcbnew.B_Cu):
    for a, c in zip(pts, pts[1:]):
        dx, dy = abs(a[0] - c[0]), abs(a[1] - c[1])
        assert dx < 1e-3 or dy < 1e-3 or abs(dx - dy) < 0.02, ("Winkel", net, a, c)
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(a)); t.SetEnd(V(c)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(N(net)); b.Add(t)
def via(p, net, d=0.7, dr=0.3):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(p)); v.SetWidth(mm(d)); v.SetDrill(mm(dr)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(N(net)); b.Add(v)
def zone(pts, net, layer, prio=1):
    z = pcbnew.ZONE(b); z.SetNet(N(net)); z.SetLayer(layer); z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.2))
    o = z.Outline(); o.NewOutline()
    for x, y in pts:
        o.Append(mm(x + O), mm(y + O))
    b.Add(z)

# ---------------------------------------------------------------- Wandler: Flaechen auf der Unterseite
zone([(82.4, 224.25), (89.6, 224.25), (89.6, 224.85), (88.7, 225.75), (88.7, 226.6), (82.4, 226.6)], "+15V", pcbnew.B_Cu)   # bis unter C29
zone([(91.6, 223.85), (92.6, 223.85), (93.8, 222.65), (95.5, 222.65), (95.5, 227.2), (93.3, 227.2), (93.3, 224.6), (92.9, 224.2), (91.6, 224.2)], "BUCK_SW", pcbnew.B_Cu)
zone([(106.5, 220.6), (111.5, 220.6), (111.5, 227.4), (106.5, 227.4)], "+5V", pcbnew.B_Cu)
# Oertliche Masseflaechen oben (Figure 22: Vias zur zweiten Masselage); durchbrechen dort die +5V-Flaeche
zone([(82.0, 220.5), (94.4, 220.5), (94.4, 230.0), (86.0, 230.0), (86.0, 226.6), (82.0, 226.6)], "GND", pcbnew.F_Cu)
zone([(114.2, 220.4), (115.8, 220.4), (115.8, 227.6), (114.2, 227.6)], "GND", pcbnew.F_Cu)

# ---------------------------------------------------------------- Hot-Loop: GND von C21/C22 direkt zu PGND
c21g, c22g, p2 = pad("C21", "2"), pad("C22", "2"), pad("U7", "2")
poly([c21g, (c21g[0] + 0.7, c21g[1] + 0.7), c22g], "GND", 0.8)
poly([pad("C29", "2"), c21g], "GND", 0.8)          # zweiter Eingangs-C in derselben Masseschleife
d = p2[1] - c22g[1]
poly([c22g, (c22g[0] + d, p2[1]), (89.1, p2[1])], "GND", 0.5)
# Kondensatoren: je mindestens zwei GND-Vias
for ref, vs in (("C29", ((82.8, 221.0), (83.8, 221.0))), ("C21", ((85.2, 221.0), (86.2, 221.0))), ("C22", ((87.35, 222.05), (88.15, 222.05)))):
    g = pad(ref, "2")
    for v in vs:
        poly([(v[0], g[1]), v], "GND", 0.4); via(v, "GND")
g = [p for p in (pad("C27", "1"), pad("C27", "2")) if p[0] > 92.5][0]
for v in ((92.45, 229.4), (93.2, 229.4)):
    poly([(v[0], g[1]), v], "GND", 0.4); via(v, "GND")
for ref in ("C23", "C24", "C25"):
    g = max((pad(ref, "1"), pad(ref, "2")), key=lambda q: q[0])
    for dy in (-0.4, 0.4):
        v = (115.0, g[1] + dy)                      # oestlich der 1206-Pads
        poly([(g[0], v[1]), v], "GND", 0.4); via(v, "GND")

# ---------------------------------------------------------------- Signale am Wandler
b8, c1 = pad("U7", "8"), pad("C26", "1")
poly([b8, (c1[0], b8[1] + (c1[0] - b8[0])), c1], "BUCK_BST", 0.3)
p9 = pad("U7", "9"); poly([p9, (p9[0], pad("C27", "1")[1])], "BUCK_VCC", 0.25)
p11, r22, r23 = pad("U7", "11"), pad("R22", "2"), pad("R23", "1")
poly([p11, (p11[0], 226.3), (r23[0] + (r23[1] - 226.3), 226.3), r23, r22], "BUCK_FB", 0.2)
p10, r23g = pad("U7", "10"), pad("R23", "2")
poly([p10, (p10[0], 226.9), (r23g[0] + (r23g[1] - 226.9), 226.9), r23g], "GND", 0.25)
for v in ((r23g[0] - 0.35, r23g[1] + 1.2), (r23g[0] + 0.45, r23g[1] + 1.2)):
    poly([(v[0], r23g[1]), v], "GND", 0.25); via(v, "GND")
p4 = pad("U7", "4")
poly([p4, (p4[0], 222.2), (p4[0] - 0.75, 221.45)], "GND", 0.25)
p5, l2 = pad("U7", "5"), pad("L1", "2")
poly([p5, (p5[0], 221.2)], "+5V", 0.25)
poly([(p5[0], 221.2), (p5[0], 217.2), (l2[0], 217.2), l2], "+5V", 0.65)
# Ausgang auf die +5V-Flaeche oben
for i in range(6):
    via((109.5, 221.0 + i * 1.2), "+5V", 0.9, 0.5)

# ---------------------------------------------------------------- USB von der Buchse zur Schutzdiode (ohne Vias)
DP, DN = "USB_D+", "USB_D-"
b6, a7, a6, b7 = pad("J1", "B6"), pad("J1", "A7"), pad("J1", "A6"), pad("J1", "B7")
W = 0.45
# D+ verbindet B6 und A6 unterhalb der Pads, D- verbindet A7 und B7 oberhalb
poly([b6, (b6[0], 227.5), (b6[0] + 0.39, 227.89), (a6[0] - 0.39, 227.89), (a6[0], 227.5), a6], DP, 0.2)
poly([a7, (a7[0], 225.6), (a7[0] + 0.39, 225.21), (b7[0] - 0.39, 225.21), (b7[0], 225.6), b7], DN, 0.2)
xp, xn = b6[0] + 0.51, b7[0] - 0.39
u1, u3, u6, u4 = pad("U3", "1"), pad("U3", "3"), pad("U3", "6"), pad("U3", "4")
poly([b6, (b6[0], 225.55), (xp, 225.55 - 0.51), (xp, 224.7)], DP, 0.2)
poly([(xp, 224.7), (xp, u3[1] + 0.55), (xp - 0.55, u3[1]), u3], DP, W)
poly([(xn, 225.21), (xn, 224.7)], DN, 0.2)
poly([(xn, 224.7), (xn, u1[1] + 0.65), (xn - 0.65, u1[1]), u1], DN, W)
poly([u3, u4], DP, 0.25); poly([u1, u6], DN, 0.25)
# ---------------------------------------------------------------- USB von der Schutzdiode zum ESP32
d1, d2 = pad("U1", "23"), pad("U1", "24")
xe = u6[0] - 1.36
def rp(ref, net):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNetname() == net or p.GetNetname().endswith("/" + net):
            q = p.GetPosition(); return (pcbnew.ToMM(q.x) - O, pcbnew.ToMM(q.y) - O)
    raise KeyError(ref + net)
DNE, DPE = "USB_D-_ESP", "USB_D+_ESP"
ne, nw, pe, pw = rp("R24", DN), rp("R24", DNE), rp("R25", DP), rp("R25", DPE)
assert ne[0] > nw[0] and pe[0] > pw[0], "R24/R25: Pad zum Stecker muss oestlich liegen"
poly([u6, (xe, u6[1]), (xe - (u6[1] - 217.2), 217.2), (43.0, 217.2), (42.6, 216.8), (42.6, 213.0), (42.2, 212.6), (ne[0] + 0.9, 212.6), (ne[0] + 0.2, 211.9), ne], DN, W)
poly([nw, (nw[0] - 0.2, 211.9), (nw[0] - 0.9, 212.6), (33.4, 212.6), (33.0, 213.0), d1], DNE, W)
poly([u4, (xe, u4[1]), (xe - (u4[1] - 217.8), 217.8), (42.4, 217.8), (42.0, 217.4), (42.0, 213.6), (41.6, 213.2), (pe[0] + 0.5, 213.2), (pe[0] + 0.2, 212.9), pe], DP, W)
poly([pw, (pw[0] - 0.2, 212.9), (pw[0] - 0.5, 213.2), (34.25, 213.2), (33.85, 213.6), d2], DPE, W)
# U3: Versorgung und Masse
u5 = pad("U3", "5"); uv = (58.4, u5[1]); poly([u5, uv], "+5V", 0.4); via(uv, "+5V")
# ST: GND-Weg von Pin 2 kurz. J1 traegt den Eingangs-Rueckstrom: breite Bruecke oben, Vias zur Flaeche.
u2 = pad("U3", "2"); g1 = (62.4, u2[1]); YB = 223.3
poly([u2, g1], "GND", 0.3); via(g1, "GND")
poly([g1, (g1[0], YB)], "GND", 0.6, pcbnew.F_Cu)
poly([(66.4, 221.9), (66.4, YB), (60.2, YB)], "GND", 0.8, pcbnew.F_Cu)
for v in ((66.4, 221.9), (66.4, YB), (61.6, YB), (60.2, YB)):
    via(v, "GND")
# C_BUS oben: +5V zum Via von Pin 5, GND auf den Steg
c1p, c2p = pad("C28", "1"), pad("C28", "2")
poly([c1p, (uv[0] + (c1p[1] - uv[1]), c1p[1]), uv], "+5V", 0.4, pcbnew.F_Cu)
poly([c2p, (g1[0], c2p[1])], "GND", 0.4, pcbnew.F_Cu)
# C4/C9 (ESP32-Abblockung): GND direkt zu U4 und zur Hauptflaeche, damit I2C und BOOT sie nicht abschneiden
c9g, u43 = pad("C9", "2"), pad("U4", "3")
poly([c9g, (c9g[0], u43[1] + (c9g[0] - u43[0])), u43], "GND", 0.5)
c4g = pad("C4", "2")
poly([c4g, (c4g[0], c9g[1]), c9g], "GND", 0.5)
# Linke Ecke: Masseflaeche ueber die Oberseite verbinden, egal wo die DIN-Leitung spaeter verlaeuft
poly([(12.0, 203.0), (22.0, 203.0)], "GND", 0.4, pcbnew.F_Cu)
for v in ((12.0, 203.0), (22.0, 203.0)):
    via(v, "GND")
# R22 an die +5V-Flaeche oben (ausserhalb der oertlichen GND-Flaeche)
r1 = pad("R22", "1"); rv = (r1[0] - 0.9, r1[1]); poly([r1, rv], "+5V", 0.3); via(rv, "+5V")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("buck+usb done", d1, d2, u1, u3)
