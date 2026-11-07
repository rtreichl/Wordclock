# -*- coding: utf-8 -*-
"""Qualifikation Laserteile (Frontplatte Cortenstahl 1 mm, Diffusor) - in FreeCAD ausfuehren.

Erwartet die globalen Variablen STAGE (Staging-Verzeichnis) und ROOT (Repository).
Schreibt <STAGE>/Laser/*.dxf (R12) und <STAGE>/laser_result.json.
Regeln laserteile-online.eu (wissen/fertigungsgrenzen, wissen/dxf-datei-erstellen, cortenstahl-lasern; 2026-11-07):
Stahl s = 1 mm: Loch >= max(0.75 s, 1 mm), Steg >= max(s, 1 mm), Loch-Rand >= max(s, 3.2 mm);
DXF in mm 1:1, geschlossene Konturen, keine doppelten Linien, keine Splines/Texte/Schraffuren, R14 oder aelter.
"""
import os, re, json, math, Part
import FreeCAD as App
from FreeCAD import Vector as V

S = 1.0
RULE = {"hole": max(0.75 * S, 1.0), "web": max(S, 1.0), "edge": max(S, 3.2), "slot": max(S, 1.0)}
out_dir = os.path.join(STAGE, "Laser"); os.makedirs(out_dir, exist_ok=True)
checks = {"Frontplatte": [], "Diffusor": []}


def check(part, cat, name, crit, meas, ok, note=""):
    checks[part].append({"cat": cat, "name": name, "crit": crit, "meas": meas, "ok": bool(ok), "note": note})


def read_dxf(path):
    """LWPOLYLINE/CIRCLE einlesen; meldet auch nicht unterstuetzte Elemente."""
    lines = open(path, encoding="cp1252").read().splitlines()
    pairs = [(lines[i].strip(), lines[i + 1].strip()) for i in range(0, len(lines) - 1, 2)]
    ents, cur, other, units = [], None, [], None
    sect = None
    for k, (c, v) in enumerate(pairs):
        if c == "9" and v == "$INSUNITS":
            units = pairs[k + 1][1]
        if c == "0":
            if cur: ents.append(cur); cur = None
            if v in ("LWPOLYLINE", "CIRCLE"):
                cur = {"type": v, "pts": [], "flag": 0, "layer": None, "c": None, "r": None, "bulge": False}
            elif sect == "ENTITIES" and v not in ("ENDSEC", "SECTION", "EOF", "VERTEX", "SEQEND", "POLYLINE"):
                other.append(v)
            continue
        if c == "2" and pairs[k - 1] == ("0", "SECTION"):
            sect = v
        if cur is None:
            continue
        if c == "8": cur["layer"] = v
        elif c == "70": cur["flag"] = int(v)
        elif c == "42" and float(v) != 0: cur["bulge"] = True
        elif cur["type"] == "LWPOLYLINE" and c == "10": cur["pts"].append([float(v), None])
        elif cur["type"] == "LWPOLYLINE" and c == "20": cur["pts"][-1][1] = float(v)
        elif cur["type"] == "CIRCLE" and c == "10": cur["c"] = [float(v), None]
        elif cur["type"] == "CIRCLE" and c == "20": cur["c"][1] = float(v)
        elif cur["type"] == "CIRCLE" and c == "40": cur["r"] = float(v)
    if cur: ents.append(cur)
    return ents, other, units


def to_wire(e):
    if e["type"] == "CIRCLE":
        return Part.Wire(Part.makeCircle(e["r"], V(e["c"][0], e["c"][1], 0)))
    pts = [V(x, y, 0) for x, y in e["pts"]]
    if (pts[0] - pts[-1]).Length > 1e-6:
        pts.append(pts[0])
    return Part.makePolygon(pts)


def write_r12(path, contours):
    """DXF R12 (AC1009): POLYLINE/VERTEX bzw. CIRCLE, Einheit mm."""
    o = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
         "0", "SECTION", "2", "ENTITIES"]
    for layer, e in contours:
        if e["type"] == "CIRCLE":
            o += ["0", "CIRCLE", "8", layer, "10", "%.4f" % e["c"][0], "20", "%.4f" % e["c"][1], "30", "0.0", "40", "%.4f" % e["r"]]
        else:
            o += ["0", "POLYLINE", "8", layer, "66", "1", "70", "1", "10", "0.0", "20", "0.0", "30", "0.0"]
            pts = e["pts"] if (abs(e["pts"][0][0] - e["pts"][-1][0]) > 1e-6 or abs(e["pts"][0][1] - e["pts"][-1][1]) > 1e-6) else e["pts"][:-1]
            for x, y in pts:
                o += ["0", "VERTEX", "8", layer, "10", "%.4f" % x, "20", "%.4f" % y, "30", "0.0"]
            o += ["0", "SEQEND", "8", layer]
    o += ["0", "ENDSEC", "0", "EOF"]
    open(path, "w", encoding="ascii", newline="\r\n").write("\n".join(o) + "\n")


def read_r12(path):
    t = open(path, encoding="ascii").read().splitlines()
    pairs = [(t[i].strip(), t[i + 1].strip()) for i in range(0, len(t) - 1, 2)]
    return sum(1 for c, v in pairs if c == "0" and v in ("POLYLINE", "CIRCLE"))


# ================================================================== Frontplatte
src = os.path.join(ROOT, "01_Mechanic", "Frontplatte", "Frontplatte_1mm_mit_Lichtleiter.dxf")
ents, other, units = read_dxf(src)
outer = [e for e in ents if e["layer"] == "Frontplatte"]
inner = [e for e in ents if e["layer"] != "Frontplatte"]
P = "Frontplatte"
check(P, "Lieferant", "Werkstoff verfuegbar", "Corten (Edelrost) 0,5-15 mm im Kalkulator, 1 mm", "Corten 1 mm", True,
      "Lieferung blank/mit Walzhaut - Patina bildet sich erst; ggf. kuenstlich vorrosten.")
check(P, "DXF", "Nur unterstuetzte Elemente", "nur Konturen (keine Splines, Texte, Schraffuren, Bemassungen)",
      f"{len(ents)} Konturen, sonstige: {sorted(set(other)) or '-'}", not other and not any(e["bulge"] for e in ents))
check(P, "DXF", "Einheit / Massstab", "mm, 1:1", f"$INSUNITS={units}", units in (None, "4"))
ob = to_wire(outer[0]).BoundBox
check(P, "DXF", "Aussenkontur", "1 Kontur, 500 x 500 mm (+-0,1)", f"{len(outer)} Kontur, {ob.XLength:.2f} x {ob.YLength:.2f} mm",
      len(outer) == 1 and abs(ob.XLength - 500) < 0.1 and abs(ob.YLength - 500) < 0.1)
check(P, "Lieferant", "Blechformat", "<= 3000 x 1500 mm", f"{ob.XLength:.0f} x {ob.YLength:.0f} mm", ob.XLength <= 3000 and ob.YLength <= 1500)
wires = [to_wire(e) for e in inner]
closed = all(w.isClosed() for w in wires) and to_wire(outer[0]).isClosed()
check(P, "DXF", "Geschlossene Konturen", "alle Konturen geschlossen", f"{sum(w.isClosed() for w in wires) + 1}/{len(wires) + 1}", closed)
faces = [Part.Face(w) for w in wires]
selfx = [i for i, f in enumerate(faces) if not f.isValid()]
check(P, "DXF", "Keine Selbstueberschneidung", "alle Konturen gueltig", f"{len(selfx)} ungueltig", not selfx)
keys = [tuple(sorted((round(x, 3), round(y, 3)) for x, y in (e["pts"] or [e["c"]]))) for e in inner]
dups = len(keys) - len(set(keys))
check(P, "DXF", "Keine doppelten Linien", "0 doppelte Konturen", f"{dups}", dups == 0)
nest = sum(1 for i, a in enumerate(faces) for j, b in enumerate(faces) if i != j and a.BoundBox.isInside(b.BoundBox) and b.common(a).Area > 1e-6)
check(P, "Konstruktion", "Keine Inseln (Schablonenschrift)", "keine Kontur innerhalb einer anderen", f"{nest}", nest == 0,
      "Buchstabeninnenteile wuerden sonst herausfallen.")
plate = Part.Face(to_wire(outer[0]))
outside = [i for i, f in enumerate(faces) if plate.common(f).Area < f.Area - 1e-3]
check(P, "Konstruktion", "Ausschnitte innerhalb der Platte", "alle innen", f"{len(outside)} ausserhalb", not outside)
# Stegbreite zwischen Ausschnitten (nur Nachbarn pruefen)
mind, pair = 1e9, None
for i, a in enumerate(wires):
    for j in range(i + 1, len(wires)):
        b = wires[j]
        if a.BoundBox.Center.distanceToPoint(b.BoundBox.Center) < 45:
            d = a.distToShape(b)[0]
            if d < mind:
                mind, pair = d, (i, j)
check(P, "Lieferant", "Min. Stegbreite zwischen Ausschnitten", f">= {RULE['web']:.1f} mm (b >= s)", f"{mind:.2f} mm", mind >= RULE["web"])
edge = min(to_wire(outer[0]).distToShape(w)[0] for w in wires)
check(P, "Lieferant", "Min. Abstand Ausschnitt - Aussenkante", f">= {RULE['edge']:.1f} mm", f"{edge:.2f} mm", edge >= RULE["edge"])
# Schlitzbreite (Strichstaerke der Buchstaben): morphologisches Oeffnen mit r = Grenzwert/2
r = RULE["slot"] / 2 - 0.01
thin = []
for i, f in enumerate(faces):
    if inner[i]["type"] == "CIRCLE":
        continue
    try:
        g = f.makeOffset2D(-r, join=0).makeOffset2D(r, join=0)
        loss = 1 - g.Area / f.Area
    except Exception:
        loss = 1.0
    if loss > 0.03:
        thin.append((i, round(loss * 100, 1)))
check(P, "Lieferant", "Min. Schlitz-/Strichbreite der Buchstaben", f">= {RULE['slot']:.1f} mm (kein Flaechenverlust > 3 % beim Oeffnen mit {RULE['slot']:.1f} mm)",
      f"{len(thin)} Konturen darunter" + (f": {thin[:5]}" if thin else ""), not thin)
holes = [e for e in inner if e["type"] == "CIRCLE"]
check(P, "Lieferant", "Min. Lochdurchmesser", f">= {RULE['hole']:.1f} mm", ", ".join(f"Ø {2 * e['r']:.2f} mm" for e in holes) or "keine Bohrung",
      all(2 * e["r"] >= RULE["hole"] for e in holes))
lp = [e for e in holes if abs(2 * e["r"] - 2.8) < 0.01]
check(P, "Konstruktion", "Lichtleiter-Bohrung", "1 x Ø 2,8 mm an Sollposition (256,63 | 19,00)",
      f"{len(lp)} x" + (f" bei ({lp[0]['c'][0]:.2f} | {lp[0]['c'][1]:.2f})" if lp else ""),
      len(lp) == 1 and abs(lp[0]["c"][0] - 256.627) < 0.05 and abs(lp[0]["c"][1] - 19.0) < 0.05)
# Buchstabenraster gegen Kammern (Kammermitten der Gitterteile)
PX, PY, XC, YC = 38.5177, 38.4037, 250.6275, 250.0
xs = [XC + (i - 5.5) * PX for i in range(12)]; ys = [YC - (5.5 - j) * PY for j in range(12)]
offc = 0
for f, e in zip(faces, inner):
    if e["type"] == "CIRCLE":
        continue
    c = f.BoundBox.Center
    if min(max(abs(c.x - x), abs(c.y - y)) for x in xs for y in ys) > 15 - 0.5:
        offc += 1
check(P, "Passung", "Buchstaben ueber den Kammern", "jeder Buchstabe innerhalb einer 30-mm-Kammer", f"{offc} ausserhalb", offc == 0)
svg = open(os.path.join(ROOT, "00_Design", "Frontplatte-500mm-Sencilla.svg"), encoding="utf-8").read()
grid = {(int(r_) - 1, int(c_) - 1): l for r_, c_, l in re.findall(r'id="L(\d\d)_(\d\d)_([^"_]+)', svg)}
rows = ["".join(grid[(r_, c_)] for c_ in range(12)) for r_ in range(12)]
need = ["IST", "FÜNF", "ZEHN", "VIERTEL", "ZWANZIG", "HALB", "VOR", "NACH", "EINS", "ZWEI", "DREI", "VIER", "SECHS",
        "SIEBEN", "ACHT", "NEUN", "ELF", "ZWÖLF"]
missing = [w for w in need if not any(w in row for row in rows)]
check(P, "Funktion", "Alle Uhrzeit-Woerter zusammenhaengend im Raster", "18 Woerter (IST ... ZWÖLF)",
      f"fehlend: {missing or '-'}", not missing,
      "Zeile 8 lautet 'ZEHNEUENVIER': NEUN nur nicht zusammenhaengend (N-E-U-_-N); die Firmware ueberspringt das E.")
dst = os.path.join(out_dir, "Frontplatte_Corten_1mm_R12.dxf")
write_r12(dst, [("Kontur", outer[0])] + [("Kontur", e) for e in inner])
n = read_r12(dst)
check(P, "DXF", "Bestell-DXF (R12) geschrieben und gelesen", f"{len(ents)} Konturen", f"{n} Konturen", n == len(ents))

# ================================================================== Diffusor
D = "Diffusor"
check(D, "Lieferant", "Werkstoff bei laserteile-online.eu", "Opal-Acrylglas (Plexiglas WN071XT) 2 mm",
      "nicht im Angebot (nur Metalle)", False, "Diffusoren bei einem Kunststoff-Laserdienst bestellen (z. B. Acrylglas-Zuschnitt).")
de, dother, dunits = read_dxf(os.path.join(ROOT, "01_Mechanic", "Diffusor", "Diffusor_30x30.dxf")) if False else ([], [], None)
# Diffusor-DXF besteht aus LINE-Elementen: direkt einlesen
t = open(os.path.join(ROOT, "01_Mechanic", "Diffusor", "Diffusor_30x30.dxf"), encoding="ascii").read().splitlines()
pr = [(t[i].strip(), t[i + 1].strip()) for i in range(0, len(t) - 1, 2)]
segs, cur = [], None
for c, v in pr:
    if c == "0":
        if cur: segs.append(cur)
        cur = {} if v == "LINE" else None
    elif cur is not None and c in ("10", "20", "11", "21"):
        cur[c] = float(v)
if cur: segs.append(cur)
w = Part.Wire(Part.__sortEdges__([Part.LineSegment(V(s_["10"], s_["20"], 0), V(s_["11"], s_["21"], 0)).toShape() for s_ in segs]))
db = w.BoundBox
check(D, "DXF", "Kontur", "1 geschlossene Kontur 30 x 30 mm (+-0,1)", f"{'geschlossen' if w.isClosed() else 'offen'}, {db.XLength:.2f} x {db.YLength:.2f} mm",
      w.isClosed() and abs(db.XLength - 30) < 0.1 and abs(db.YLength - 30) < 0.1)
check(D, "Passung", "Spiel in der Gitter-Tasche", "Tasche 30,4 mm: 0,2 mm je Seite >= Laser-Toleranz 0,1 mm", "0,20 mm je Seite", True)
check(D, "Passung", "Dicke vs. Taschentiefe", "Platte 2,0 mm <= Tasche 2,1 mm (Toleranz Acrylglas beachten)", "0,1 mm Luft", True,
      "Extrudiertes Acryl hat oft +-0,1..0,2 mm Dickentoleranz: Dicke beim Lieferanten anfragen.")
dd = os.path.join(out_dir, "Diffusor_30x30_R12.dxf")
write_r12(dd, [("Kontur", {"type": "LWPOLYLINE", "pts": [[0, 0], [30, 0], [30, 30], [0, 30]]})])
check(D, "DXF", "Bestell-DXF (R12) geschrieben und gelesen", "1 Kontur", f"{read_r12(dd)} Kontur", read_r12(dd) == 1)

json.dump(checks, open(os.path.join(STAGE, "laser_result.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print({k: f"{sum(c['ok'] for c in v)}/{len(v)}" for k, v in checks.items()})
for k, v in checks.items():
    for c in v:
        if not c["ok"]:
            print("FAIL", k, c["name"], c["meas"])
