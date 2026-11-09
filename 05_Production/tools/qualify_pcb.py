# -*- coding: utf-8 -*-
"""Qualifikation LED-Platine: Fertigungsdaten erzeugen (Staging) und pruefen.

Aufruf mit KiCad-Python:  python qualify_pcb.py <staging_dir>
Ergebnis: <staging_dir>/PCB/... und <staging_dir>/pcb_result.json
"""
import os, sys, json, re, csv, subprocess, zipfile, hashlib, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(ROOT, "05_Production")):  # Repo-Wurzel (auch ohne .git)
    ROOT = os.path.dirname(ROOT)
KI = os.path.join(ROOT, "02_Electronics", "KiCad")
sys.path.insert(0, os.path.join(KI, "tools"))
import pcbnew  # noqa: E402
import design as D  # noqa: E402

import shutil as _sh
CLI = os.environ.get("KICAD_CLI") or _sh.which("kicad-cli") or r"P:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
STAGE = os.path.join(sys.argv[1], "PCB")
os.makedirs(STAGE, exist_ok=True)
PCB = os.path.join(KI, "WortUhr.kicad_pcb"); SCH = os.path.join(KI, "WortUhr.kicad_sch")
mm = pcbnew.ToMM
checks = []

# JLCPCB 2-Lagen FR-4, 1 oz (jlcpcb.com/capabilities/pcb-capabilities, abgerufen 2026-11-07)
JLC = {"min_track": 0.10, "min_clear": 0.10, "min_via_drill": 0.15, "min_via_dia": 0.25, "min_annular": 0.18,
       "min_pth_drill": 0.15, "min_npth_drill": 0.50, "max_board": (670.0, 600.0), "min_edge": 0.20,
       "min_silk_h": 1.00, "min_silk_w": 0.15, "pcba_max": (460.0, 500.0)}


def check(cat, name, crit, meas, ok, note=""):
    checks.append({"cat": cat, "name": name, "crit": crit, "meas": meas, "ok": bool(ok), "note": note})


def run(args):
    r = subprocess.run([CLI] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------- ERC / DRC / Paritaet
rc, out = run(["sch", "erc", "--format", "json", "--severity-error", "-o", os.path.join(STAGE, "erc.json"), SCH])
erc = json.load(open(os.path.join(STAGE, "erc.json"), encoding="utf-8"))
n_erc = sum(len(s["violations"]) for s in erc["sheets"])
check("Elektrisch", "ERC (Schaltplan)", "0 Fehler", f"{n_erc} Fehler", n_erc == 0)
rc, out = run(["pcb", "drc", "--schematic-parity", "--format", "json", "-o", os.path.join(STAGE, "drc.json"), PCB])
drc = json.load(open(os.path.join(STAGE, "drc.json"), encoding="utf-8"))
sev = collections.Counter(v["severity"] for v in drc["violations"])
cosmetic = collections.Counter(v["type"] for v in drc["violations"] if v["severity"] != "error")
check("Elektrisch", "DRC Fehler", "0", f"{sev.get('error', 0)}", sev.get("error", 0) == 0)
check("Elektrisch", "DRC Warnungen", "nur kosmetisch (Bestueckungsdruck, Waermefalle)", dict(cosmetic),
      all(t.startswith("silk") or t == "starved_thermal" for t in cosmetic))
check("Elektrisch", "Offene Verbindungen", "0", f"{len(drc['unconnected_items'])}", len(drc["unconnected_items"]) == 0)
check("Elektrisch", "Schaltplan-/Layout-Abgleich", "0 Abweichungen", f"{len(drc['schematic_parity'])}", len(drc["schematic_parity"]) == 0)

# ---------------------------------------------------------------- Fertigungsgrenzen
b = pcbnew.LoadBoard(PCB)
ds = b.GetDesignSettings()
bb = b.GetBoardEdgesBoundingBox()
ew = max(mm(s.GetWidth()) for s in b.GetDrawings() if s.GetLayer() == pcbnew.Edge_Cuts)
W, H = mm(bb.GetWidth()) - ew, mm(bb.GetHeight()) - ew      # Umrisslinie: Mitte der Linie zaehlt
check("Fertigung", "Platinengroesse", "<= 670 x 600 mm (Fertigung), <= 460 x 500 mm (Standard-Bestueckung), Soll 234 x 234 mm",
      f"{W:.2f} x {H:.2f} mm", W <= JLC["pcba_max"][0] and H <= JLC["pcba_max"][1] and abs(W - 234) < 0.05 and abs(H - 234) < 0.05)
check("Fertigung", "Lagenzahl", "2", str(b.GetCopperLayerCount()), b.GetCopperLayerCount() == 2)
tw = [mm(t.GetWidth()) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
check("Fertigung", "Min. Leiterbahnbreite", f">= {JLC['min_track']} mm", f"{min(tw):.3f} mm", min(tw) >= JLC["min_track"] - 1e-6)
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
vd = min(mm(v.GetDrillValue()) for v in vias); vD = min(mm(v.GetWidth(pcbnew.F_Cu)) for v in vias)
ar = min((mm(v.GetWidth(pcbnew.F_Cu)) - mm(v.GetDrillValue())) / 2 for v in vias)
check("Fertigung", "Via-Bohrung", f">= {JLC['min_via_drill']} mm", f"{vd:.2f} mm ({len(vias)} Vias)", vd >= JLC["min_via_drill"] - 1e-6)
check("Fertigung", "Via-Durchmesser", f">= {JLC['min_via_dia']} mm", f"{vD:.2f} mm", vD >= JLC["min_via_dia"] - 1e-6)
check("Fertigung", "Restring Via (absolutes Minimum 2 Lagen 1 oz)", f">= {JLC['min_annular']} mm", f"{ar:.3f} mm", ar >= JLC["min_annular"] - 1e-6)
pth, npth = [], []
for fp in b.GetFootprints():
    for p in fp.Pads():
        d = mm(p.GetDrillSize().x)
        if d > 0:
            (npth if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else pth).append(d)
check("Fertigung", "Min. Bohrung durchkontaktiert (Pads)", f">= {JLC['min_pth_drill']} mm",
      f"{min(pth):.2f} mm" if pth else "keine", (min(pth) >= JLC["min_pth_drill"]) if pth else True)
check("Fertigung", "Min. Bohrung nicht durchkontaktiert", f">= {JLC['min_npth_drill']} mm",
      f"{min(npth):.2f} mm ({len(npth)} Stk.)", min(npth) >= JLC["min_npth_drill"])
check("Fertigung", "Kupfer-Randabstand (Regel)", f">= {JLC['min_edge']} mm", f"{mm(ds.m_CopperEdgeClearance):.2f} mm",
      mm(ds.m_CopperEdgeClearance) >= JLC["min_edge"] - 1e-6)
clr = mm(ds.m_NetSettings.GetDefaultNetclass().GetClearance())
check("Fertigung", "Isolationsabstand (Netzklasse Default, vom DRC geprueft)", f">= {JLC['min_clear']} mm", f"{clr:.2f} mm",
      clr >= JLC["min_clear"] - 1e-6)
fids = {fp.GetReference(): fp.GetLayer() for fp in b.GetFootprints() if fp.GetReference().startswith("FID")}
nf, nb = sum(1 for l in fids.values() if l == pcbnew.F_Cu), sum(1 for l in fids.values() if l == pcbnew.B_Cu)
check("Bestueckung", "Passermarken (Standard-PCBA)", ">= 3 je bestueckter Seite", f"oben {nf}, unten {nb}", nf >= 3 and nb >= 3)
texts = [d for d in b.GetDrawings() if d.GetClass() == "PCB_TEXT" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
for fp in b.GetFootprints():
    for f in (fp.Reference(), fp.Value()):
        if f.IsVisible() and f.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            texts.append(f)
th = min(mm(t.GetTextHeight()) for t in texts); tw_ = min(mm(t.GetTextThickness()) for t in texts)
check("Fertigung", "Bestueckungsdruck Text", f"Hoehe >= {JLC['min_silk_h']} mm, Strich >= {JLC['min_silk_w']} mm",
      f"Hoehe {th:.2f} mm, Strich {tw_:.2f} mm", th >= JLC["min_silk_h"] - 1e-6 and tw_ >= JLC["min_silk_w"] - 1e-6)
# ROUTING_GUIDE.md: Abblock-Kondensatoren nah am Versorgungspin, kritische Teile gesperrt
def _pad(ref, num):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            return p.GetPosition()
DEC = {"C2": ("U2", "1"), "C3": ("U2", "5"), "C4": ("U1", "3"), "C6": ("U4", "5"), "C8": ("U5", "1"), "C9": ("U1", "3"), "C175": ("D75", "1"), "C22": ("U7", "1"), "C28": ("U3", "5")}
DEC.update({f"C{100 + n}": (f"D{n}", "1") for n in range(1, 73)})
dist = {}
for cref, (ic, pin) in DEC.items():
    cfp = b.FindFootprintByReference(cref)
    tgt = _pad(ic, pin)
    dist[cref] = min(mm((p.GetPosition() - tgt).EuclideanNorm()) for p in cfp.Pads() if p.GetNetname() == b.FindFootprintByReference(ic).FindPadByNumber(pin).GetNetname())
worst = max(dist, key=dist.get)
check("Layout", "Abblock-C am Versorgungspin", "Pad-Abstand <= 8 mm (C175: Unterseite, ueber Via)",
      f"max. {dist[worst]:.1f} mm ({worst}), IC-C: " + ", ".join(f"{k} {dist[k]:.1f}" for k in ("C2", "C3", "C4", "C6", "C8")),
      all(v <= 8.0 for v in dist.values()))
LOCK = {"J1", "J3", "J4", "U1"} | {fp.GetReference() for fp in b.GetFootprints() if fp.GetReference().startswith(("H", "FID"))}
unl = sorted(r for r in LOCK if not b.FindFootprintByReference(r).IsLocked())
check("Layout", "Kritische Teile gesperrt", "Steckverbinder, Kantenbruecken, ESP32, Montageloecher, Passermarken", f"{len(LOCK) - len(unl)}/{len(LOCK)}", not unl)
holes = [(fp.GetReference(), round(mm(fp.GetPosition().x) - 40, 2), round(mm(fp.GetPosition().y) - 40, 2))
         for fp in b.GetFootprints() if fp.GetReference().startswith("H")]
check("Mechanik", "Montageloecher M3", "6 x Bohrung 4,3 mm (M3 mit +-0,65 mm Spiel) an den Stegkreuzungen", f"{len(holes)} Stk.",
      len(holes) == 6 and all(abs(d - 4.3) < 0.01 for d in npth if d > 3.0))

import math
_off = []
for _t in b.GetTracks():
    if _t.GetClass() != "PCB_TRACK" or _t.GetStart() == _t.GetEnd():
        continue
    _dx, _dy = abs(_t.GetEnd().x - _t.GetStart().x), abs(_t.GetEnd().y - _t.GetStart().y)
    _w = math.degrees(math.atan2(_dy, _dx))
    # Kurze Stuecke auf dem Fertigungsraster duerfen wegen Rundung etwas abweichen
    if min(abs(_w - x) for x in (0, 45, 90)) > 0.5 and abs(_dx - _dy) > 30000 and min(_dx, _dy) > 30000:
        _off.append(_t.GetNetname())
check("Layout", "Leiterbahnwinkel", "nur horizontal, vertikal oder 45 Grad", f"{len(_off)} abweichend" + (f" ({sorted(set(_off))[:5]})" if _off else ""), not _off)

# ---------------------------------------------------------------- Fertigungsdaten erzeugen
g = os.path.join(STAGE, "gerber"); os.makedirs(g, exist_ok=True)
layers = "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
rc1, o1 = run(["pcb", "export", "gerbers", "-o", g, "--layers", layers, "--subtract-soldermask", "--no-x2", PCB])
rc2, o2 = run(["pcb", "export", "drill", "-o", g + os.sep, "--format", "excellon", "--drill-origin", "absolute",
               "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", PCB])
files = sorted(os.listdir(g))
need = ["F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_Paste", "B_Paste", "F_Silkscreen", "B_Silkscreen", "Edge_Cuts"]
miss = [n for n in need if not any(n in f for f in files)]
drills = [f for f in files if f.endswith(".drl")]
check("Fertigungsdaten", "Gerber vollstaendig", "9 Lagen", f"{len(files) - len(drills)} Dateien, fehlend: {miss or '-'}",
      rc1 == 0 and not miss)
check("Fertigungsdaten", "Bohrdateien", "PTH + NPTH Excellon (mm)", ", ".join(drills), rc2 == 0 and len(drills) >= 2)
# Umriss-Gerber auslesen und Masse pruefen
ec = open(os.path.join(g, [f for f in files if "Edge_Cuts" in f][0]), encoding="utf-8").read()
fs = re.search(r"%FSLAX(\d)(\d)Y", ec); dec = int(fs.group(2)) if fs else 6
xy = re.findall(r"X(-?\d+)Y(-?\d+)(?:I-?\d+J-?\d+)?D0[12]\*", ec)
xs = [int(a) / 10 ** dec for a, _ in xy]; ys = [int(b_) / 10 ** dec for _, b_ in xy]
gw, gh = max(xs) - min(xs), max(ys) - min(ys)
check("Fertigungsdaten", "Umriss im Gerber", "234 x 234 mm (+-0,1)", f"{gw:.2f} x {gh:.2f} mm", abs(gw - 234) < 0.1 and abs(gh - 234) < 0.1)
zf = os.path.join(STAGE, "WortUhr_LED-Board_Gerber.zip")
with zipfile.ZipFile(zf, "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(os.path.join(g, f), f)
check("Fertigungsdaten", "Gerber-Archiv", "ZIP lesbar, alle Dateien enthalten",
      f"{len(zipfile.ZipFile(zf).namelist())} Dateien", zipfile.ZipFile(zf).testzip() is None and len(zipfile.ZipFile(zf).namelist()) == len(files))

# Stueckliste + Bestueckung (JLCPCB-Format) fuer beide Varianten
MASTER = set(D.MASTER_PLACE)
NO_ASSY = lambda ref: ref.startswith(("H", "JP", "J3", "J4", "FID"))
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}


def variant(name, refs):
    rows = collections.OrderedDict()
    for r in sorted(refs, key=lambda s: (re.sub(r"\d", "", s), int(re.sub(r"\D", "", s) or 0))):
        fp = fps[r]
        key = (fp.GetValue(), fp.GetFPIDAsString().split(":")[-1])
        rows.setdefault(key, []).append(r)
    bom = os.path.join(STAGE, f"BOM_{name}.csv")
    with open(bom, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "Quantity", "LCSC Part #"])
        for (val, foot), rs in rows.items():
            w.writerow([val, ",".join(rs), foot, len(rs), ""])
    cpl = os.path.join(STAGE, f"CPL_{name}.csv")
    with open(cpl, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in refs:
            fp = fps[r]
            w.writerow([r, f"{mm(fp.GetPosition().x):.3f}mm", f"{-mm(fp.GetPosition().y):.3f}mm",
                        "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom", f"{fp.GetOrientationDegrees():.1f}"])
    return bom, cpl, rows


assy = [r for r in fps if not NO_ASSY(r)]
for vname, refs in (("Master", assy), ("Slave", [r for r in assy if r not in MASTER])):
    bom, cpl, rows = variant(vname, refs)
    noval = [r for r in refs if not fps[r].GetValue() or fps[r].GetValue() in ("~", "")]
    nfp = [r for r in refs if not fps[r].GetFPIDAsString()]
    n = len(refs)
    check("Stueckliste", f"BOM/CPL {vname}", "jede Position mit Wert, Footprint und Koordinate",
          f"{n} Bauteile, {len(rows)} Positionen", not noval and not nfp and sum(1 for _ in open(cpl, encoding='utf-8')) == n + 1)
leds = sum(1 for r in assy if fps[r].GetValue() == "SK6812RGBW")
check("Stueckliste", "LED-Anzahl", "73 je Platine (2 je Kammer + 1 Minutenpunkt)", f"{leds}", leds == 73)

# Schaltplan-PDF, 3D
run(["sch", "export", "pdf", "-o", os.path.join(STAGE, "WortUhr_Schaltplan.pdf"), SCH])
# 3D-Modelle frisch aus der aktuellen Platine (Slave = ohne Master-Teile)
import shutil, tempfile
tmpd = tempfile.mkdtemp()
shutil.copytree(os.path.join(KI, "3dmodels"), os.path.join(tmpd, "3dmodels"))
sb = pcbnew.LoadBoard(PCB)
for fp in list(sb.GetFootprints()):
    if fp.GetReference() in MASTER:
        sb.Remove(fp)
pcbnew.SaveBoard(os.path.join(tmpd, "slave.kicad_pcb"), sb)
for v, src in (("master", PCB), ("slave", os.path.join(tmpd, "slave.kicad_pcb"))):
    rc, _ = run(["pcb", "export", "step", "--force", "--subst-models", "--no-unspecified", "-o",
                 os.path.join(STAGE, f"LED-Board_{v}.step"), src])
    check("Fertigungsdaten", f"3D-Modell {v}", "STEP-Export erfolgreich", "ok" if rc == 0 else f"rc {rc}", rc == 0)
check("Fertigungsdaten", "Schaltplan-PDF", "vorhanden", "ok" if os.path.exists(os.path.join(STAGE, "WortUhr_Schaltplan.pdf")) else "fehlt",
      os.path.exists(os.path.join(STAGE, "WortUhr_Schaltplan.pdf")))

# Hinweise (nicht blockierend)
notes = ["Bestueckung: Master = Standard-PCBA (beidseitig, Passermarken vorhanden, Nutzenraender 'by JLCPCB' bestellen). Slave = nur Oberseite bestueckt; C1 (Unterseite) von Hand loeten oder ebenfalls Standard-PCBA.",
         "Loetstopplack: gruen empfohlen (min. Steg 0,10 mm); bei Schwarz/Weiss gilt 0,13 mm.",
"SK6812RGBW: Footprint mit WS2812B-Pinbelegung (1 VDD, 2 DOUT, 3 VSS, 4 DIN) - vor Bestellung mit dem Datenblatt des gewaehlten Herstellers abgleichen.",
         "BH1750 (U5): Footprint WSOF6I selbst erstellt nach ROHM-Zeichnung, ungetestet.",
         "LCSC-Teilenummern in BOM leer - bei JLCPCB-Bestueckung zuordnen.",
         "Die 19 Kantenbruecken (0R 2512) werden nach dem Zusammenbau von Hand geloetet und sind nicht in der BOM.",
         "Schaltwandler U7 (SCT2360): Footprint nach Datenblatt erstellt, ungetestet. L1, F1 und SK6812-Typ vor der Bestellung festlegen.",
         "Versorgung: USB-C PD 15 V, Schaltwandler 5 V / 6 A, Firmware begrenzt auf geschaetzte 5 A."]
json.dump({"checks": checks, "notes": notes}, open(os.path.join(sys.argv[1], "pcb_result.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for f in ("erc.json", "drc.json"):
    os.replace(os.path.join(STAGE, f), os.path.join(sys.argv[1], f))
import shutil; shutil.rmtree(g)
print("PCB checks:", sum(c["ok"] for c in checks), "/", len(checks), "passed")
for c in checks:
    if not c["ok"]:
        print("FAIL", c["name"], c["meas"])
