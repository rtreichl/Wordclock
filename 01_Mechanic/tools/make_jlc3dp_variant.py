# -*- coding: utf-8 -*-
"""JLC3DP-Variante der Gitterteile erzeugen (freecadcmd make_jlc3dp_variant.py).

JLC3DP (FDM, PLA) verlangt >= 0,5 mm Montagespiel, >= 2,5 mm Wand und hat +-0,4 % Masstoleranz.
Die P1S-Teile (Spiel 0,19-0,28 mm, Teile stossen ohne Fuge) bleiben unveraendert. Die Variante:

1. Fuge: jedes Teil wird an seinen Trennkanten um FUGE/2 = 0,25 mm zurueckgenommen (Fuge 0,5 mm).
2. Zapfen neu: Flanken parallel zur bestehenden Tasche (Hals 5,0 / Spitze 7,6 / Laenge 3,8 mm),
   0,5 mm Abstand normal zur Flanke, 0,5 mm an der Stirn und 0,5 mm unter dem Taschendeckel.
   Die Taschen bleiben, wie sie sind. Hinterschnitt (Halt gegen Auseinanderziehen) 0,5 mm je Seite.
3. Q4: Wand zwischen Bauteil-Aussparung und Kammer von 2,38 auf 2,53 mm (gilt fuer beide Varianten).

Schreibt die Objekte <Teil>_JLC3DP (Gruppe Lichtgitter_JLC3DP) ins Modell und
01_Mechanic/Gitter/JLC3DP/Gitter_<Teil>_JLC3DP.step / _druckfertig.3mf.
"""
import os, math
import FreeCAD as App, Part, MeshPart
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
doc = App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
import sys
sys.path.insert(0, os.path.join(ROOT, "02_Electronics", "KiCad", "tools"))
import design as D  # noqa: E402  Rastermasse: eine Quelle
PX, PY, (XC, YC) = D.GRID_PX, D.GRID_PY, D.CLOCK_CENTER
xs = [XC + (i - 5.5) * PX for i in range(12)]; ys = [YC + (5.5 - j) * PY for j in range(12)]
XS, YS = (xs[5] + xs[6]) / 2, (ys[5] + ys[6]) / 2
rw = [(ys[j] + ys[j + 1]) / 2 for j in range(11)]; cw = [(xs[i] + xs[i + 1]) / 2 for i in range(11)]
J = [("Q1", "Q2", XS, rw[j], 0) for j in (0, 2, 4)] + [("Q3", "Q4", XS, rw[j], 0) for j in (6, 8, 10)] + \
    [("Q1", "Q3", cw[i], YS, -90) for i in (0, 2, 4)] + [("Q2", "Q4", cw[i], YS, -90) for i in (6, 8, 10)]
N = {"Q1": "Q1_obenlinks", "Q2": "Q2_obenrechts", "Q3": "Q3_untenlinks", "Q4": "Q4_untenrechts"}

FUGE, CLR = 0.5, 0.5
S_NECK, S_TIP, S_LEN = 5.0, 7.6, 3.8           # Tasche (gemessen)
Z_TOP_SOCKET = 20.4                            # Taschendeckel
slope = (S_TIP - S_NECK) / 2 / S_LEN
lat = CLR / math.cos(math.atan(slope))         # seitlicher Abstand bei 0,5 mm normal zur Flanke
U0, U1 = -FUGE / 2 - 0.3, S_LEN - CLR          # Zapfen von 0,3 mm im Teil bis 0,5 mm vor die Stirn
hw = lambda u: S_NECK / 2 + slope * u - lat


def put(sh, x, y, ang):
    s = sh.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), ang); s.translate(V(x, y, 0)); return s


def prism(pts, z0, z1):
    return Part.Face(Part.makePolygon([V(u, v, z0) for u, v in pts] + [V(pts[0][0], pts[0][1], z0)])).extrude(V(0, 0, z1 - z0))


# ------------------------------------------------------------------ 3. Q4-Wand (Basismodell)
q4 = doc.getObject(N["Q4"])
fill = Part.makeBox(5.0, 0.15, 1.5, V(348.13, -478.75, 5.0))
if q4.Shape.common(fill).Volume < 0.5 * fill.Volume:
    s = q4.Shape.fuse(fill).removeSplitter()
    assert s.isValid() and len(s.Solids) == 1
    q4.Shape = s
    print("Q4: Wand an der Bauteil-Aussparung auf 2,53 mm")

base = {q: doc.getObject(n).Shape.copy() for q, n in N.items()}
sh = dict(base)

# ------------------------------------------------------------------ alte Zapfen entfernen, Hoehe merken
zr = {}
for k, (f, t, x, y, a) in enumerate(J):
    env = put(Part.makeBox(4.5, 9.0, 40, V(0, -4.5, -5)), x, y, a)
    ten = sh[f].common(env)
    zr[k] = (ten.BoundBox.ZMin, ten.BoundBox.ZMax)
    sh[f] = sh[f].cut(env)

# ------------------------------------------------------------------ 1. Fuge an den Trennkanten
L = 600
trim = {"Q1": [Part.makeBox(L, L, 40, V(XS - FUGE / 2, -L, -5)), Part.makeBox(L, L, 40, V(-L / 2, YS - L + FUGE / 2, -5))],
        "Q2": [Part.makeBox(L, L, 40, V(XS + FUGE / 2 - L, -L, -5)), Part.makeBox(L, L, 40, V(0, YS - L + FUGE / 2, -5))],
        "Q3": [Part.makeBox(L, L, 40, V(XS - FUGE / 2, -L, -5)), Part.makeBox(L, L, 40, V(-L / 2, YS - FUGE / 2, -5))],
        "Q4": [Part.makeBox(L, L, 40, V(XS + FUGE / 2 - L, -L, -5)), Part.makeBox(L, L, 40, V(0, YS - FUGE / 2, -5))]}
for q in sh:
    sh[q] = sh[q].cut(Part.makeCompound(trim[q]))

# ------------------------------------------------------------------ 2. neue Zapfen
for k, (f, t, x, y, a) in enumerate(J):
    z0, _ = zr[k]
    pts = [(U0, -hw(U0)), (U1, -hw(U1)), (U1, hw(U1)), (U0, hw(U0))]
    tenon = put(prism(pts, z0, Z_TOP_SOCKET - CLR), x, y, a)
    sh[f] = sh[f].fuse(tenon)

out = os.path.join(ROOT, "01_Mechanic", "Gitter", "JLC3DP"); os.makedirs(out, exist_ok=True)
grp = doc.getObject("Lichtgitter_JLC3DP") or doc.addObject("App::DocumentObjectGroup", "Lichtgitter_JLC3DP")
for q, n in N.items():
    s = sh[q].removeSplitter()
    assert s.isValid() and len(s.Solids) == 1, q
    name = n + "_JLC3DP"
    o = doc.getObject(name) or doc.addObject("Part::Feature", name)
    o.Shape = s
    if o not in grp.Group:
        grp.addObject(o)
    if hasattr(o, "Visibility"):
        o.Visibility = False
    print(q, "JLC3DP ok", round(s.Volume))
# Spiel pruefen: kleinster Abstand Zapfen <-> Nachbarteil
mind = min(sh[f].distToShape(sh[t])[0] for f, t, *_ in J)
print("kleinster Abstand zwischen Nachbarteilen %.3f mm" % mind)
assert mind >= CLR - 0.02
doc.recompute(); doc.save()


def export(o, path_step, path_3mf):
    Part.export([o], path_step)
    s = o.Shape.copy(); s.rotate(V(0, 0, 0), V(1, 0, 0), 180); b = s.BoundBox; s.translate(V(-b.XMin, -b.YMin, -b.ZMin))
    MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False).write(path_3mf)


for q, n in N.items():
    export(doc.getObject(n + "_JLC3DP"), os.path.join(out, f"Gitter_{n}_JLC3DP.step"), os.path.join(out, f"Gitter_{n}_JLC3DP_druckfertig.3mf"))
gdir = os.path.join(ROOT, "01_Mechanic", "Gitter")
export(q4, os.path.join(gdir, f"Gitter_{N['Q4']}.step"), os.path.join(gdir, f"Gitter_{N['Q4']}_druckfertig.3mf"))
print("JLC3DP VARIANT DONE")
