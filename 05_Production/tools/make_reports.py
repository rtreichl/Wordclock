# -*- coding: utf-8 -*-
"""Qualifikationsberichte schreiben und nur freigegebene Daten nach 05_Production kopieren.

Aufruf:  python make_reports.py <staging_dir>
Liest pcb_result.json, laser_result.json, print_result.json, firmware_result.json aus dem Staging.
"""
import os, sys, json, shutil, hashlib, subprocess, datetime

STAGE = sys.argv[1]
ROOT = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(ROOT, "05_Production")):  # Repo-Wurzel (auch ohne .git)
    ROOT = os.path.dirname(ROOT)
PROD = os.path.join(ROOT, "05_Production")
try:
    COMMIT = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    DIRTY = bool(subprocess.run(["git", "status", "--porcelain", "--", "00_Design", "01_Mechanic", "02_Electronics", "03_Software"],
                                cwd=ROOT, capture_output=True, text=True).stdout.strip())
except Exception:
    COMMIT, DIRTY = "?", False
DATE = datetime.date.today().isoformat()

SRC = {
    "JLCPCB": "[JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)",
    "laserteile-online.eu": "[Fertigungsgrenzen](https://www.laserteile-online.eu/wissen/fertigungsgrenzen), [DXF-Datei erstellen](https://www.laserteile-online.eu/wissen/dxf-datei-erstellen), [Cortenstahl lasern](https://www.laserteile-online.eu/cortenstahl-lasern)",
    "P1S": "[Bambu Lab P1S Spezifikation](https://wiki.bambulab.com/en/p1/manual/unboxing-p1s)",
    "JLC3DP": "[JLC3DP 3D Printing Design Guideline](https://jlc3dp.com/help/article/3D-Printing-Design-Guideline)",
    "Cutworks": "Cutworks: keine oeffentlichen Konstruktionsregeln gefunden; allgemeine Regeln fuer CO2-Laser in Acrylglas, Angebot laut Nutzer 0,83 EUR/Stk. (2026-11-08)",
    "Eigenzuschnitt": "Plattenware (eBay, Artikel 205831697352), Zuschnitt von Hand mit Anschlag",
}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def table(checks, cols):
    out = ["| Kategorie | Pruefung | Kriterium | Messwert | " + " | ".join(c[0] for c in cols) + " |",
           "|---|---|---|---|" + "---|" * len(cols)]
    for c in checks:
        res = []
        for _, key in cols:
            v = c.get(key)
            res.append("–" if v is None else ("✅ bestanden" if v else "❌ nicht bestanden"))
        meas = c["meas"] if isinstance(c["meas"], str) else json.dumps(c["meas"], ensure_ascii=False)
        out.append(f"| {c['cat']} | {c['name']} | {c['crit']} | {meas} | " + " | ".join(res) + " |")
    notes = [f"- **{c['name']}:** {c['note']}" for c in checks if c.get("note")]
    return out, notes


def report(folder, title, part, supplier_lines, checks, cols, files, extra_notes=(), released=None):
    """released: dict Fertiger -> bool"""
    d = os.path.join(PROD, folder); os.makedirs(d, exist_ok=True)
    # alte Freigaben entfernen, dann nur bestandene Dateien kopieren
    for f in os.listdir(d):
        if f != "QUALIFIKATION.md" and os.path.isfile(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    copied = []
    if any(released.values()):
        for src in files:
            if "_JLC3DP" in os.path.basename(src) and not released.get("JLC3DP", True):
                continue                      # JLC3DP-Variante nur bei JLC3DP-Freigabe
            if "_JLC3DP" not in os.path.basename(src) and os.path.basename(src).startswith("Gitter_") and not released.get("Bambu Lab P1S", True):
                continue
            dst = os.path.join(d, os.path.basename(src)); shutil.copy(src, dst); copied.append(dst)
    tab, notes = table(checks, cols)
    status = " · ".join(f"**{k}: {'FREIGEGEBEN' if v else 'GESPERRT'}**" for k, v in released.items())
    lines = [f"# Qualifikationsbericht – {title}", "",
             f"| | |", "|---|---|",
             f"| Bauteil | {part} |",
             f"| Fertiger | {', '.join(supplier_lines)} |",
             f"| Datum | {DATE} |",
             f"| Stand | Git `{COMMIT}`{' (mit nicht eingecheckten Aenderungen)' if DIRTY else ''} |",
             f"| Pruefung | automatisch, `05_Production/tools/` |",
             f"| Ergebnis | {status} |", "",
             "## Pruefergebnisse", ""] + tab + [""]
    if notes or extra_notes:
        lines += ["## Hinweise und offene Punkte", ""] + notes + [f"- {n}" for n in extra_notes] + [""]
    lines += ["## Freigegebene Dateien", ""]
    if copied:
        lines += ["| Datei | SHA256 |", "|---|---|"] + [f"| `{os.path.basename(p)}` | `{sha(p)[:16]}…` |" for p in copied]
    else:
        lines += ["Keine – das Bauteil ist fuer keinen Fertiger freigegeben. Die Daten bleiben in ihrem Quellordner."]
    lines += ["", "## Grundlage (Fertigerangaben, abgerufen 2026-11-07)", ""] + [f"- {SRC[s]}" for s in supplier_lines if s in SRC]
    open(os.path.join(d, "QUALIFIKATION.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return {"title": title, "folder": folder, "released": released, "files": len(copied),
            "passed": sum(1 for c in checks for _, k in cols if c.get(k) is True),
            "failed": sum(1 for c in checks for _, k in cols if c.get(k) is False)}


summary = []
J = lambda n: json.load(open(os.path.join(STAGE, n), encoding="utf-8"))

# ---------------------------------------------------------------- Platine
pcb = J("pcb_result.json")
for c in pcb["checks"]:
    c["jlc"] = c["ok"]
ok = all(c["ok"] for c in pcb["checks"])
P = os.path.join(STAGE, "PCB")
summary.append(report("05_Platine_JLCPCB", "LED-Platine (4x identisch, Master/Slave)", "WortUhr LED-Board rev2, 234 x 234 mm, 2 Lagen",
                      ["JLCPCB"], pcb["checks"], [("JLCPCB", "jlc")],
                      [os.path.join(P, f) for f in sorted(os.listdir(P))], pcb["notes"], {"JLCPCB": ok}))

# ---------------------------------------------------------------- Laser
las = J("laser_result.json")
cs = las["Frontplatte"]
for c in cs:
    c["lo"] = c["ok"]
summary.append(report("01_Frontplatte_Laser", "Frontplatte Cortenstahl 1 mm", "Frontplatte Cortenstahl 1 mm", ["laserteile-online.eu"], cs,
                      [("laserteile-online.eu", "lo")], [os.path.join(STAGE, "Laser", "Frontplatte_Corten_1mm_R12.dxf")], (),
                      {"laserteile-online.eu": all(c["ok"] for c in cs)}))
cs = las["Diffusor"]
summary.append(report("02_Diffusor_Laser", "Diffusor Opal-Acrylglas 2 mm (144 x 30 x 30, 4 x Ø 5,6)", "Diffusor Opal-Acrylglas 2 mm (144 x 30 x 30, 4 x Ø 5,6)",
                      ["Eigenzuschnitt", "Cutworks"], cs, [("Eigenzuschnitt", "self"), ("Cutworks", "cw")],
                      [os.path.join(STAGE, "Laser", f) for f in ("Diffusor_30x30_R12.dxf", "Diffusor_Minutenpunkt_D5.6_R12.dxf")], (),
                      {"Eigenzuschnitt": all(c.get("self") is not False for c in cs), "Cutworks": all(c.get("cw") is not False for c in cs)}))

# ---------------------------------------------------------------- 3D-Druck
pr = J("print_result.json")
PD = os.path.join(STAGE, "Print")
grid = [c for k, v in pr.items() if k.startswith("Gitter") for c in [dict(x, name=f"{k}: {x['name']}") for x in v]]
rear = [c for k, v in pr.items() if k.startswith("Rueckrahmen") or k.startswith("Druckplatten") for c in [dict(x, name=f"{k}: {x['name']}") for x in v]]
for cs, folder, title, prefix in ((grid, "03_Gitter_3D-Druck", "Lichtgitter Q1–Q4", "Gitter_"), (rear, "04_Rueckrahmen_3D-Druck", "Rückrahmen (8 Leisten, 2 Druckplatten)", "Rueckrahmen_")):
    rel = {"Bambu Lab P1S": all(c["p1s"] is not False for c in cs), "JLC3DP": all(c["jlc"] is not False for c in cs)}
    files = [os.path.join(PD, f) for f in sorted(os.listdir(PD)) if f.startswith(prefix)]
    summary.append(report(folder, title, title, ["P1S", "JLC3DP"], cs, [("P1S", "p1s"), ("JLC3DP", "jlc")], files,
                          ("Druck: PLA, 0,4-mm-Duese, Gitter mit der Vorderseite (z = 25) auf dem Bett, Rueckrahmen mit der Wandseite auf dem Bett.",), rel))

# ---------------------------------------------------------------- Firmware / WLED
fw = J("firmware_result.json")
cs = fw["Firmware"]
for c in cs:
    c["esp"] = c["ok"]
r = report("06_Firmware", "Firmware ESPHome (ESP32-S3)", "03_Software/ESPHome/wortuhr.yaml", ["ESPHome"], cs, [("ESPHome", "esp")], [],
           ("Binaerdateien werden nicht eingecheckt: sie enthalten WLAN-Daten und API-Schluessel aus secrets.yaml. "
            "Fuer das Geraet lokal bauen: `03_Software/ESPHome/.venv/Scripts/esphome.exe run wortuhr.yaml`.",),
           {"Build": all(c["ok"] for c in cs)})
summary.append(r)
cs = fw["WLED"]
for c in cs:
    c["wled"] = c["ok"]
wl = os.path.join(ROOT, "03_Software", "WLED")
summary.append(report("07_WLED", "WLED-LED-Maps", "03_Software/WLED/ledmap_*.json", ["WLED"], cs, [("WLED", "wled")],
                      [os.path.join(wl, f) for f in sorted(os.listdir(wl)) if f.endswith(".json")], (), {"WLED": all(c["ok"] for c in cs)}))

# ---------------------------------------------------------------- Uebersicht
lines = ["# WortUhr – Produktionsdaten", "",
         f"Stand Git `{COMMIT}`, geprueft am {DATE}. In diesem Ordner liegen nur Daten, die alle Qualifikationspruefungen "
         "fuer den jeweiligen Fertiger bestanden haben. Gesperrte Bauteile haben einen Bericht, aber keine Dateien.", "",
         "| Bauteil | Ordner | Freigabe | Pruefungen | Dateien |", "|---|---|---|---|---|"]
for s in summary:
    rel = ", ".join(f"{k}: {'✅' if v else '❌'}" for k, v in s["released"].items())
    lines.append(f"| {s['title']} | [`{s['folder']}`]({s['folder']}/QUALIFIKATION.md) | {rel} | {s['passed']} ✅ / {s['failed']} ❌ | {s['files']} |")
lines += ["", "Neu erzeugen: siehe `tools/README.md`."]
open(os.path.join(PROD, "README.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
