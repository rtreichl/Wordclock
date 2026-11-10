# WortUhr – Arbeitsregeln für dieses Repository

Wortuhr 500 × 500 mm: Frontplatte, Lichtgitter, Rückrahmen, vier gleiche LED-Platinen (eine davon Master mit ESP32-S3), Firmware. Überblick und Ordner: `README.md`.

## Grundsätze

- **Eine Quelle je Wert.** Bauteile, Netze, Platzierung, ESP32-Pins, Abblock-Zuordnung, Mindestbreiten, Bezugsdaten (MPN, DigiKey, LCSC), Rastermaße, Revision und Datum stehen in `02_Electronics/KiCad/tools/design.py`. Schaltplan, Platine, Prüfungen und Firmware-Abgleich lesen von dort. Keine zweite Kopie anlegen.
- **Erzeugte Dateien nicht von Hand ändern:** `*.kicad_sch`, `WortUhr.kicad_sym` (aus `gen_sch.py`), `03_Software/ESPHome/wortuhr_layout.h` (aus `gen_layout.py`), `03_Software/WLED/ledmap_*.json` (aus `gen_ledmap.py`), alles unter `05_Production/` (aus `make_reports.py`).
- **Regeln mit ID** stehen in `02_Electronics/KiCad/ROUTING_GUIDE.md` (DEC, LAY, PWR, MFG, RF, DES, SCH). Befunde nennen die Rule ID. Neue Regeln erst nach Rückfrage aufnehmen, IDs nie wiederverwenden.
- **Datenblatt zuerst (DES-001):** Vor Änderungen an Schaltplan oder Layout das Datenblatt des betroffenen Bauteils nach Layoutvorgaben und Referenzschaltung durchsuchen. Die Datenblätter liegen lokal in `06_Datenblätter/` (nicht eingecheckt). Was nicht belegt ist, als nicht belegt benennen.
- **Leiterbahnen** nur horizontal, vertikal oder unter 45 Grad.
- **`05_Production` ist der Freigabe-Ordner:** Kopien der geprüften Quelldateien plus Bericht. Dort nie direkt ändern; `05_Production/tools/check_production.py` vergleicht Kopien, Prüfsummen und Quellen.
- **Das FreeCAD-Modell ist nicht parametrisch.** Änderungen an `01_Mechanic/FrontPlatte-Bestellung.FCStd` sind Eingriffe in eine binäre Datei. Erledigte Eingriffe liegen als Skripte in `99_Archive/Einmal-Skripte/`; sie dokumentieren die Änderung und werden nicht erneut ausgeführt.

## Schaltplan ändern

1. Netzliste vorher sichern: `kicad-cli sch export netlist -o vorher.net 02_Electronics/KiCad/WortUhr.kicad_sch`.
2. `design.py` (Elektrik) oder die Funktion `sheet_*` in `gen_sch.py` (Darstellung) ändern, dann `python tools/gen_sch.py`.
3. Der Generator meldet Befunde zu Netzen und Lesbarkeit. Es dürfen keine übrig bleiben.
4. Netzliste nachher exportieren und vergleichen. Bei reinen Darstellungsänderungen muss sie identisch sein. Netznamen sind Teil des Layouts.

## Platine ändern

- Freerouting arbeitet nicht deterministisch. `build_pcb.py` erzeugt eine andere Platine als die eingecheckte. Deshalb: kleine Änderungen in der gerouteten Platine nachziehen **und** die Vorgabe in `design.py` (Platzierung) und `route_master.py` (feste Leiterbahnen) eintragen.
- Routing-Ablauf, Freerouting-Einstellungen und das Power-Integrity-Review stehen im Leitfaden. Routing über den Freerouting-MCP (Port 37864), DRC über den KiCad-MCP oder `kicad-cli`.
- Nach einer Layout-Änderung: DRC mit Schaltplan-Abgleich, `qualify_pcb.py`, `pcb_images.py`, Kollisionsprüfung gegen Gitter und Rückrahmen: `WORTUHR_STEP_DIR=<stage>/PCB freecadcmd 01_Mechanic/tools/update_pcb_model.py` (schreibt das FreeCAD-Modell; ohne die Variable liest es die freigegebenen STEP-Dateien aus `05_Production/05_Platine_JLCPCB`).

## Prüfen

Alles läuft auch im GitHub-Workflow `.github/workflows/production.yml`. Lokal (Staging-Ordner außerhalb des Repos oder `stage/`, der ignoriert ist):

```
"<KiCad>/bin/python" 05_Production/tools/qualify_pcb.py stage          # ERC, DRC, Schaltplan, Layout-Regeln, Fertigungsdaten
03_Software/ESPHome/.venv/Scripts/python 05_Production/tools/qualify_firmware.py stage   # --no-compile spart den Build
freecadcmd 05_Production/tools/run_freecad.py                          # Laser- und Druckteile
python 05_Production/tools/make_reports.py stage                       # Berichte und freigegebene Daten nach 05_Production
python 02_Electronics/KiCad/tools/gen_sch.py --check                   # Schaltplan = Generator?
```

Eine Prüfung, die rot wird, ist ein Befund. Nicht die Grenze anpassen, sondern die Ursache beheben oder die Ausnahme mit Begründung im Leitfaden und in `design.py` eintragen lassen.

## Umgebung

- Pfade zu KiCad und Freerouting löst `02_Electronics/KiCad/tools/kicad_env.py` auf. Keine Installationspfade in andere Skripte schreiben. Variablen: `KICAD_CLI`, `KICAD10_SYMBOL_DIR`, `KICAD10_FOOTPRINT_DIR`, `FREEROUTING_JAR`, `FREEROUTING_JAVA`.
- `pcbnew` gibt es nur im KiCad-Python. `gen_sch.py` und `qualify_firmware.py` laufen mit jedem Python 3.
- `.env` (DigiKey-API) und `03_Software/ESPHome/secrets.yaml` sind lokal und werden nie eingecheckt.
