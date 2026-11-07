# WortUhr

Wortuhr mit 12 × 12 Buchstaben, 500 × 500 mm. Frontplatte aus 1 mm Cortenstahl, die von Magneten gehalten wird. Lichtgitter aus 4 gedruckten Teilen. Vier gleiche LED-Platinen (SK6812 RGBW, ESP32-S3, WLED). Aufbauhöhe 36 mm.

| Ordner | Inhalt |
|---|---|
| `00_Design/` | Grafik und Buchstabenlayout: Affinity-Datei, Pattern-SVGs, Frontplatten-DXF/-SVG (Schrift Sencilla) |
| `01_Mechanic/` | FreeCAD-Hauptmodell `FrontPlatte-Bestellung.FCStd` und Fertigungsdateien |
| `01_Mechanic/Frontplatte/` | Frontplatte 1 mm (STEP), DXF mit Lichtleiter-Bohrung zum Bestellen |
| `01_Mechanic/Gitter/` | Lichtgitter Q1–Q4 (STEP und druckfertige 3MF) |
| `01_Mechanic/Rueckrahmen/` | 8 Rückrahmen-Leisten (STEP) und 2 Druckplatten (3MF, je ≤ 254 × 254 mm) |
| `01_Mechanic/Diffusor/` | Diffusor 30 × 30 × 2 mm (DXF/STEP), 144 Stück |
| `02_Electronics/KiCad/` | KiCad-Projekt, Generator-Skripte (`tools/`), Projektbibliotheken und Platzhalter-3D-Modelle |
| `02_Electronics/3D-Export/` | 3D-Modelle der Platine, Master- und Slave-Variante |
| `02_Electronics/BESTUECKUNG.md` | Bestückung, Kantenbrücken, Montage, WLED-Einstellungen |
| `03_Software/WLED/` | LED-Maps für WLED (1 oder 2 LEDs je Kammer) |
| `04_Rendering/` | Blender-Skript, Szene, Netze und Renderbilder |
| `99_Archive/` | Ältere Modelle und Zwischenstände |

Ein Bild mit neuen Einstellungen rendern:

```
blender.exe -b -P 04_Rendering/render_wortuhr.py -- --samples 256 --res 2000x2000 --view angle
```
