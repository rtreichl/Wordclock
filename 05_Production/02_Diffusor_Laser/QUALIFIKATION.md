# Qualifikationsbericht – Diffusor Opal-Acrylglas 2 mm (144 x 30 x 30, 4 x Ø 5,6)

| | |
|---|---|
| Bauteil | Diffusor Opal-Acrylglas 2 mm (144 x 30 x 30, 4 x Ø 5,6) |
| Fertiger | Eigenzuschnitt, Cutworks |
| Datum | 2026-11-08 |
| Stand | Git `8c9f8da` |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **Eigenzuschnitt: FREIGEGEBEN** · **Cutworks: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | Eigenzuschnitt | Cutworks |
|---|---|---|---|---|---|
| Geometrie | Kontur | 1 geschlossene Kontur 30 x 30 mm (+-0,1), keine Doppellinien | geschlossen, 30.00 x 30.00 mm, 0 doppelt | ✅ bestanden | ✅ bestanden |
| Geometrie | Kleinstes Merkmal | >= Materialdicke 2 mm (Laser) | 30 mm (Quadrat ohne Ausschnitte) | ✅ bestanden | ✅ bestanden |
| Passung | Spiel in der Gitter-Tasche | Tasche 30.4 mm: Restspiel je Seite beim Groesstmass >= 0,1 mm | Eigenzuschnitt 29.9 +-0.2 mm -> 0.15 mm; Laser 30,0 +-0.1 mm -> 0.15 mm | ✅ bestanden | ✅ bestanden |
| Passung | Dicke vs. Taschentiefe | Nenndicke 2.0 mm + Toleranz <= Taschentiefe 2.1 mm | 2.0 +- 0.1 mm -> max. 2.1 mm | ✅ bestanden | ✅ bestanden |
| Werkstoff | Acrylglas-Typ fuer den Laser | Laserbar; manche Dienste schneiden kein extrudiertes (XT) Acryl | Plexiglas WN071 XT (extrudiert) | – | ✅ bestanden |
| Menge | Stueckzahl und Zuschnittplan | 144 Stk. 30 x 30 mm | Raster 31 mm (1 mm Saegefuge): 12 x 12 Stk. aus mind. 372 x 372 mm; Cutworks: 144 x 0,83 EUR = 119.52 EUR | ✅ bestanden | ✅ bestanden |
| Passung | Minutenpunkt-Diffusor Ø 5,6 (4 Stk.) | Tasche Ø 5.9 mm: Restspiel je Seite beim Groesstmass >= 0,1 mm | Eigenzuschnitt Ø 5.5 +-0.2 mm -> 0.10 mm; Laser Ø 5.6 +-0.1 mm -> 0.10 mm | ✅ bestanden | ✅ bestanden |
| DXF | Bestell-DXF Minutenpunkt (R12) | 1 Kreis Ø 5,6 mm | 1 Kontur | – | ✅ bestanden |
| DXF | Bestell-DXF (R12) geschrieben und gelesen | 1 Kontur, mm 1:1 | 1 Kontur | – | ✅ bestanden |

## Hinweise und offene Punkte

- **Spiel in der Gitter-Tasche:** Eigenzuschnitt: Anschlag auf 29,9 mm stellen. Ecken bleiben eckig (Tasche hat Eckfreistiche).
- **Dicke vs. Taschentiefe:** Dickentoleranz der gekauften Platte pruefen (extrudiertes XT-Acryl: Datenblatt). Ist sie groesser als +-0,1 mm, Tasche tiefer machen.
- **Acrylglas-Typ fuer den Laser:** Bei Cutworks vor der Bestellung bestaetigen lassen, dass XT-Material geschnitten wird.
- **Stueckzahl und Zuschnittplan:** Eigenzuschnitt: erst Streifen 30 mm, dann Quadrate; Kanten leicht entgraten.
- **Minutenpunkt-Diffusor Ø 5,6 (4 Stk.):** Eigenzuschnitt: 6 x 6 mm zuschneiden und rund auf Ø 5,5 mm schleifen, oder mit den 144 Quadraten bei Cutworks bestellen.

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `Diffusor_30x30_R12.dxf` | `ef93c51eea2e0c7a…` |
| `Diffusor_Minutenpunkt_D5.6_R12.dxf` | `c467ab6fad59d71c…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

- Plattenware (eBay, Artikel 205831697352), Zuschnitt von Hand mit Anschlag
- Cutworks: keine oeffentlichen Konstruktionsregeln gefunden; allgemeine Regeln fuer CO2-Laser in Acrylglas, Angebot laut Nutzer 0,83 EUR/Stk. (2026-11-08)
