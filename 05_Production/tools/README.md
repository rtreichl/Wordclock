# Qualifikation der Produktionsdaten

Jedes Bauteil wird gegen die Fertigungsgrenzen seines Fertigers geprüft. Nur Daten, die alle Prüfungen bestehen, landen in `05_Production/<Bauteil>/`. Jedes Bauteil bekommt dort einen Bericht `QUALIFIKATION.md` mit SHA256-Prüfsummen der Dateien.

| Skript | Prüft | Fertiger / Grundlage | Läuft mit |
|---|---|---|---|
| `qualify_pcb.py <stage>` | ERC, DRC, Abgleich Schaltplan/Layout, Leiterbahnen, Vias, Restring, Bohrungen, Randabstand, Bestückungsdruck, Passermarken. Erzeugt Gerber, Bohrdaten, BOM und CPL (Master/Slave), Schaltplan-PDF und STEP. | JLCPCB (PCB + PCBA) | KiCad-Python |
| `qualify_laser.py` | Frontplatte und Diffusor: DXF-Format, geschlossene Konturen, doppelte Linien, Inseln, Stegbreite, Schlitzbreite, Lochgröße, Randabstand, Lichtleiterbohrung, Buchstabenraster. Schreibt die Bestell-DXF im Format R12. | laserteile-online.eu | FreeCAD (`STAGE`, `ROOT` setzen) |
| `qualify_print.py` | Gitter Q1–Q4 und Rückrahmen: Netz geschlossen, Bauraum, Auflagefläche, Wandstärke per Strahlmessung, Bohrungen, Passungen (Teile untereinander, Platine, Rahmen), Spiel und Toleranzen. | Bambu Lab P1S, JLC3DP | FreeCAD (`STAGE`, `ROOT` setzen) |
| `qualify_firmware.py <stage>` | Layout aktuell, Wortpositionen, Satzbildung, ESPHome-Konfiguration, Build, Speicher, Anforderungen (NTP ohne HA, lokale Bedienung), Secrets, WLED-LED-Maps. | ESPHome / WLED | Python 3.12 mit ESPHome |
| `make_reports.py <stage>` | Schreibt die Berichte und kopiert nur freigegebene Dateien. | – | Python |

Lokal, mit FreeCAD und laufender MCP-Bridge, oder auf der Kommandozeile mit `freecadcmd`:

```
python 05_Production/tools/qualify_pcb.py stage                     # KiCad-Python
freecadcmd -c "STAGE='stage'; ROOT='.'; exec(open('05_Production/tools/qualify_laser.py').read())"
freecadcmd -c "STAGE='stage'; ROOT='.'; exec(open('05_Production/tools/qualify_print.py').read())"
python 05_Production/tools/qualify_firmware.py stage                # Python mit ESPHome
python 05_Production/tools/make_reports.py stage
```

Automatisch: Der GitHub-Workflow `.github/workflows/production.yml` führt bei jedem Push alle Schritte in sauberen Umgebungen aus. Er nutzt den Container `kicad/kicad:10.0-full`, das FreeCAD-1.1.2-AppImage und ESPHome 2026.10.2. Die Ergebnisse stellt er als Artefakte „WortUhr-Produktion“ und „WortUhr-Firmware“ bereit.
