# Qualifikationsbericht – WLED-LED-Maps

| | |
|---|---|
| Bauteil | 03_Software/WLED/ledmap_*.json |
| Fertiger | WLED |
| Datum | 2026-11-09 |
| Stand | Git `6b290f5` (mit nicht eingecheckten Aenderungen) |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **WLED: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | WLED |
|---|---|---|---|---|
| Konsistenz | ledmap 1 LED/Kammer | alle 148 LEDs ausser den 4 Minuten-LEDs genau einmal | 144 Eintraege | ✅ bestanden |
| Konsistenz | ledmap 2 LED/Kammer | alle 292 LEDs ausser den 4 Minuten-LEDs genau einmal | 288 Eintraege | ✅ bestanden |
| Konsistenz | Gleiche LED-Reihenfolge wie ESPHome | ledmap = cell_led(CELL_INDEX) | identisch | ✅ bestanden |

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `ledmap_1LED_12x12.json` | `44cb3f86ff16996b…` |
| `ledmap_2LED_24x12.json` | `50f53ff3fbcca1f8…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

