# Qualifikationsbericht – Frontplatte Cortenstahl 1 mm

| | |
|---|---|
| Bauteil | Frontplatte Cortenstahl 1 mm |
| Fertiger | laserteile-online.eu |
| Datum | 2026-11-08 |
| Stand | Git `d71eccd` (mit nicht eingecheckten Aenderungen) |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **laserteile-online.eu: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | laserteile-online.eu |
|---|---|---|---|---|
| Lieferant | Werkstoff verfuegbar | Corten (Edelrost) 0,5-15 mm im Kalkulator, 1 mm | Corten 1 mm | ✅ bestanden |
| DXF | Nur unterstuetzte Elemente | nur Konturen (keine Splines, Texte, Schraffuren, Bemassungen) | 156 Konturen, sonstige: - | ✅ bestanden |
| DXF | Einheit / Massstab | mm, 1:1 | $INSUNITS=4 | ✅ bestanden |
| DXF | Aussenkontur | 1 Kontur, 500 x 500 mm (+-0,1) | 1 Kontur, 500.00 x 500.00 mm | ✅ bestanden |
| Lieferant | Blechformat | <= 3000 x 1500 mm | 500 x 500 mm | ✅ bestanden |
| DXF | Geschlossene Konturen | alle Konturen geschlossen | 156/156 | ✅ bestanden |
| DXF | Keine Selbstueberschneidung | alle Konturen gueltig | 0 ungueltig | ✅ bestanden |
| DXF | Keine doppelten Linien | 0 doppelte Konturen | 0 | ✅ bestanden |
| Konstruktion | Keine Inseln (Schablonenschrift) | keine Kontur innerhalb einer anderen | 0 | ✅ bestanden |
| Konstruktion | Ausschnitte innerhalb der Platte | alle innen | 0 ausserhalb | ✅ bestanden |
| Lieferant | Min. Stegbreite zwischen Ausschnitten | >= 1.0 mm (b >= s) | 2.51 mm | ✅ bestanden |
| Lieferant | Min. Abstand Ausschnitt - Aussenkante | >= 3.2 mm | 16.00 mm | ✅ bestanden |
| Lieferant | Min. Schlitz-/Strichbreite der Buchstaben | >= 1.0 mm (kein Flaechenverlust > 3 % beim Oeffnen mit 1.0 mm) | 0 Konturen darunter | ✅ bestanden |
| Lieferant | Min. Lochdurchmesser | >= 1.0 mm | Ø 2.80 mm, Ø 4.00 mm, Ø 4.00 mm, Ø 4.00 mm, Ø 4.00 mm | ✅ bestanden |
| Konstruktion | Lichtleiter-Bohrung | 1 x Ø 2,8 mm an Sollposition (256,63 | 19,00) | 1 x bei (256.63 | 19.00) | ✅ bestanden |
| Konstruktion | Minutenpunkte | 4 x Ø 4,0 mm, je 18 mm von beiden Kanten | 4 x Ø 4,0 mm | ✅ bestanden |
| Passung | Buchstaben ueber den Kammern | jeder Buchstabe innerhalb einer 30-mm-Kammer | 0 ausserhalb | ✅ bestanden |
| Funktion | Alle Uhrzeit-Woerter zusammenhaengend im Raster | 18 Woerter (IST ... ZWÖLF) | fehlend: - | ✅ bestanden |
| DXF | Bestell-DXF (R12) geschrieben und gelesen | 156 Konturen | 156 Konturen | ✅ bestanden |

## Hinweise und offene Punkte

- **Werkstoff verfuegbar:** Lieferung blank/mit Walzhaut - Patina bildet sich erst; ggf. kuenstlich vorrosten.
- **Keine Inseln (Schablonenschrift):** Buchstabeninnenteile wuerden sonst herausfallen.

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `Frontplatte_Corten_1mm_R12.dxf` | `93fdc0618543f92a…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

- [Fertigungsgrenzen](https://www.laserteile-online.eu/wissen/fertigungsgrenzen), [DXF-Datei erstellen](https://www.laserteile-online.eu/wissen/dxf-datei-erstellen), [Cortenstahl lasern](https://www.laserteile-online.eu/cortenstahl-lasern)
