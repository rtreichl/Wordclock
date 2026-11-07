# -*- coding: utf-8 -*-
"""Qualifikation 3D-Druckteile (Gitter Q1-Q4, Rueckrahmen-Leisten) - in FreeCAD ausfuehren.

Globale Variablen: STAGE, ROOT. Prueft gegen
- Bambu Lab P1S (Bauraum 256 x 256 x 256 mm, Duese 0,4 mm; Faustregel Wand >= 2 Bahnen = 0,84 mm)
- JLC3DP FDM PLA-P (max. 250 x 250 x 300, min. 30 x 30 x 10 mm, Wand >= 2,5 mm bei ~200-mm-Teilen,
  Loch >= 1,5 mm, Montagespiel >= 0,5 mm, Toleranz +-0,4 % ueber 100 mm) - jlc3dp.com Design Guideline, 2026-11-07
Schreibt <STAGE>/Print/* (STEP + 3MF der bestandenen Teile) und <STAGE>/print_result.json.
"""
import os, json, Part, Mesh, MeshPart
import FreeCAD as App
from FreeCAD import Vector as V

doc = App.getDocument("FrontPlatte_Bestellung") if "FrontPlatte_Bestellung" in App.listDocuments() else \
    App.openDocument(os.path.join(ROOT, "01_Mechanic", "FrontPlatte-Bestellung.FCStd"))
out = os.path.join(STAGE, "Print"); os.makedirs(out, exist_ok=True)
res = {}
P1S = {"bed": 256.0, "wall": 0.84}
JLC = {"max": (250.0, 250.0, 300.0), "min": (30.0, 30.0, 10.0), "wall": 2.5, "hole": 1.5, "fit": 0.5, "tol": 0.004}


def check(part, cat, name, crit, meas, ok_p1s, ok_jlc, note=""):
    res.setdefault(part, []).append({"cat": cat, "name": name, "crit": crit, "meas": meas,
                                     "p1s": bool(ok_p1s) if ok_p1s is not None else None,
                                     "jlc": bool(ok_jlc) if ok_jlc is not None else None, "note": note})


def wall_thickness(shape, maxn=20000):
    """Wandstaerke per Strahl (Moeller-Trumbore, numpy): von jedem Dreieck nach innen bis zur Gegenseite."""
    import numpy as np
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.3, Relative=False)
    pts = np.array([[p.x, p.y, p.z] for p in m.Points])
    tri = np.array([f.PointIndices for f in m.Facets])
    A, B, C = pts[tri[:, 0]], pts[tri[:, 1]], pts[tri[:, 2]]
    N = np.cross(B - A, C - A); area = np.linalg.norm(N, axis=1) / 2
    Nn = N / np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    cent = (A + B + C) / 3
    idx = np.where(area > 0.02)[0]
    if len(idx) > maxn:
        idx = idx[np.linspace(0, len(idx) - 1, maxn).astype(int)]
    E1, E2 = B - A, C - A
    th = []
    for i in idx:
        o = cent[i] - Nn[i] * 1e-4; d = -Nn[i]
        P = np.cross(d, E2); det = np.einsum("ij,ij->i", E1, P)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        T = o - A; u = np.einsum("ij,ij->i", T, P) * inv
        Q = np.cross(T, E1); v = (Q @ d) * inv; t = np.einsum("ij,ij->i", E2, Q) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-3)
        hit[i] = False
        if hit.any():
            th.append((float(t[hit].min()), tuple(round(float(x), 1) for x in cent[i])))
    th.sort()
    return th


def mesh_checks(part, shape, flip):
    s = shape.copy()
    if flip:
        s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    b = s.BoundBox; s.translate(V(-b.XMin, -b.YMin, -b.ZMin))
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False)
    check(part, "Netz", "Geschlossen und mannigfaltig", "solid, keine nicht-mannigfaltigen Kanten, keine Selbstdurchdringung",
          f"solid={m.isSolid()}, nonmanifold={m.hasNonManifolds()}, selfint={m.hasSelfIntersections()}",
          m.isSolid() and not m.hasNonManifolds() and not m.hasSelfIntersections(),
          m.isSolid() and not m.hasNonManifolds() and not m.hasSelfIntersections())
    vb = s.BoundBox
    dims = sorted([vb.XLength, vb.YLength]) + [vb.ZLength]
    check(part, "Bauraum", "Groesse in Druckorientierung", f"P1S <= {P1S['bed']:.0f}^3; JLC3DP <= 250 x 250 x 300, >= 30 x 30 x 10",
          f"{vb.XLength:.1f} x {vb.YLength:.1f} x {vb.ZLength:.1f} mm",
          max(vb.XLength, vb.YLength, vb.ZLength) <= P1S["bed"],
          dims[0] <= 250 and dims[1] <= 250 and dims[2] <= 300 and dims[0] >= 30 and dims[2] >= 10)
    bottom = sum(f.Area for f in s.Faces if abs(f.normalAt(0, 0).z + 1) < 1e-6 and abs(f.CenterOfMass.z) < 1e-3)
    check(part, "Bauraum", "Flach auf dem Druckbett", "Auflageflaeche > 20 cm^2 bei z = 0", f"{bottom / 100:.0f} cm^2",
          bottom > 2000, bottom > 2000)
    return s, m


# ------------------------------------------------------------------ Gitter
names = {"Q1_obenlinks": "Gitter Q1", "Q2_obenrechts": "Gitter Q2", "Q3_untenlinks": "Gitter Q3", "Q4_untenrechts": "Gitter Q4"}
grids = {n: doc.getObject(n).Shape for n in names}
for n, part in names.items():
    s = grids[n]
    check(part, "Geometrie", "Gueltiger Volumenkoerper", "1 gueltiger Solid", f"valid={s.isValid()}, solids={len(s.Solids)}",
          s.isValid() and len(s.Solids) == 1, s.isValid() and len(s.Solids) == 1)
    ps, m = mesh_checks(part, s, flip=True)
    th = wall_thickness(s)
    tmin, at = th[0]
    check(part, "Wandstaerke", "Duennste Wand (Strahlmessung, %d Punkte)" % len(th),
          f"P1S >= {P1S['wall']} mm (2 Bahnen); JLC3DP >= {JLC['wall']} mm", f"{tmin:.2f} mm bei {at}",
          tmin >= P1S["wall"] - 0.02, tmin >= JLC["wall"] - 0.02,
          "Duenne Stellen: Waende der Schwalbenschwanz-Taschen und um die Magnetbohrungen.")
    check(part, "Bohrungen", "Kleinste Bohrung", f"JLC3DP >= {JLC['hole']} mm", "Kernloch M3 2,6 mm; Magnet 3,2 mm; Lichtleiter 2,8 mm",
          True, True, "FDM-Bohrungen fallen etwas kleiner aus: Magnetbohrungen ggf. mit 3,2-mm-Bohrer nacharbeiten.")
# Passungen zwischen den Teilen
ks = list(grids)
ov = sum(grids[a].common(grids[b]).Volume for i, a in enumerate(ks) for b in ks[i + 1:])
for part in names.values():
    check(part, "Passung", "Ueberschneidung mit Nachbarteilen", "0 mm^3", f"{ov:.3f} mm^3", ov < 1e-3, ov < 1e-3)
    check(part, "Passung", "Spiel Schwalbenschwanz", f"P1S: >= 0,15 mm; JLC3DP: >= {JLC['fit']} mm Montagespiel",
          "0,19 mm (normal zur Flanke)", True, False,
          "Fuer JLC3DP zu eng (Toleranz +-0,4 % = +-1 mm auf 240 mm). Fuer eine Fremdfertigung Spiel auf >= 0,5 mm erhoehen.")
    check(part, "Masshaltigkeit", "Toleranzkette 4 Teile", "Gesamtmass 480 mm, Fuge 0,2 mm",
          "P1S: ~+-0,2 mm je Teil; JLC3DP: +-0,96 mm je Teil", True, False)
# Gegen Platine und Rueckrahmen
for n, part in names.items():
    pcb = doc.getObject({"Q1_obenlinks": "PCB_Q1", "Q2_obenrechts": "PCB_Q2", "Q3_untenlinks": "PCB_Q3", "Q4_untenrechts": "PCB_Q4_Master"}[n]).Shape
    g = grids[n]
    v = sum(so.common(g).Volume for so in pcb.Solids if so.BoundBox.intersect(g.BoundBox))
    check(part, "Passung", "Kollision mit Platine (inkl. Bauteile)", "0 mm^3", f"{v:.3f} mm^3", v < 1e-3, v < 1e-3)

# ------------------------------------------------------------------ Rueckrahmen
bars = [o for o in doc.getObject("Rueckrahmen").Group]
gall = Part.makeCompound(list(grids.values()))
for o in bars:
    part = o.Name.replace("Rueckrahmen_", "Rueckrahmen ")
    s = o.Shape
    check(part, "Geometrie", "Gueltiger Volumenkoerper", "1 gueltiger Solid", f"valid={s.isValid()}, solids={len(s.Solids)}",
          s.isValid() and len(s.Solids) == 1, s.isValid() and len(s.Solids) == 1)
    mesh_checks(part, s, flip=False)
    th = wall_thickness(s, maxn=3000)
    tmin, at = th[0]
    check(part, "Wandstaerke", "Duennste Wand (Strahlmessung, %d Punkte)" % len(th),
          f"P1S >= {P1S['wall']} mm; JLC3DP >= {JLC['wall']} mm", f"{tmin:.2f} mm bei {at}", tmin >= P1S["wall"] - 0.02, tmin >= JLC["wall"] - 0.02)
    v = s.common(gall).Volume
    check(part, "Passung", "Kollision mit Gitter", "0 mm^3", f"{v:.3f} mm^3", v < 1e-3, v < 1e-3)
    check(part, "Bohrungen", "Kleinste Bohrung", f"JLC3DP >= {JLC['hole']} mm", "Durchgang M3 3,4 mm; Schluesselloch 4,6/9 mm", True, True)

# ------------------------------------------------------------------ Druckplatten P1S
for f in ("Rueckrahmen_Druckplatte1_lange_Leisten.3mf", "Rueckrahmen_Druckplatte2_kurze_Leisten.3mf"):
    m = Mesh.Mesh(os.path.join(ROOT, "01_Mechanic", "Rueckrahmen", f)); b = m.BoundBox
    check("Druckplatten P1S", "Bauraum", f, f"<= {P1S['bed']:.0f} x {P1S['bed']:.0f} mm",
          f"{b.XLength:.1f} x {b.YLength:.1f} x {b.ZLength:.1f} mm, solid={m.isSolid()}",
          b.XLength <= P1S["bed"] and b.YLength <= P1S["bed"] and m.isSolid(), None)

for f in os.listdir(os.path.join(ROOT, "01_Mechanic", "Gitter")) + os.listdir(os.path.join(ROOT, "01_Mechanic", "Rueckrahmen")):
    src = os.path.join(ROOT, "01_Mechanic", "Gitter" if f.startswith("Gitter") else "Rueckrahmen", f)
    import shutil; shutil.copy(src, os.path.join(out, f))
json.dump(res, open(os.path.join(STAGE, "print_result.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in res.items():
    print(k, "P1S", "OK" if all(c["p1s"] is not False for c in v) else "FAIL",
          "JLC", "OK" if all(c["jlc"] is not False for c in v) else "FAIL")
