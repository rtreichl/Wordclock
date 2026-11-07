# Qualifikationsbericht – WLED-LED-Maps

| | |
|---|---|
| Bauteil | 03_Software/WLED/ledmap_*.json |
| Fertiger | WLED |
| Datum | 2026-11-08 |
| Stand | Git `8a65c57` |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **WLED: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | WLED |
|---|---|---|---|---|
| Konsistenz | ledmap 1 LED/Kammer | Permutation 0..143 | 144 Eintraege | ✅ bestanden |
| Konsistenz | ledmap 2 LED/Kammer | Permutation 0..287 | 288 Eintraege | ✅ bestanden |
| Konsistenz | Gleiche LED-Reihenfolge wie ESPHome | ledmap = CELL_INDEX | identisch | ✅ bestanden |

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `ledmap_1LED_12x12.json` | `c59317f224f55792…` |
| `ledmap_2LED_24x12.json` | `294a34c44a2a2ac0…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

