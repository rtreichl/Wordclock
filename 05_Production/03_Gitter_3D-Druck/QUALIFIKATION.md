# Qualifikationsbericht – Lichtgitter Q1–Q4

| | |
|---|---|
| Bauteil | Lichtgitter Q1–Q4 |
| Fertiger | P1S, JLC3DP |
| Datum | 2026-11-08 |
| Stand | Git `8a65c57` |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **Bambu Lab P1S: FREIGEGEBEN** · **JLC3DP: GESPERRT** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | P1S | JLC3DP |
|---|---|---|---|---|---|
| Geometrie | Gitter Q1: Gueltiger Volumenkoerper | 1 gueltiger Solid | valid=True, solids=1 | ✅ bestanden | ✅ bestanden |
| Netz | Gitter Q1: Geschlossen und mannigfaltig | solid, keine nicht-mannigfaltigen Kanten, keine Selbstdurchdringung | solid=True, nonmanifold=False, selfint=False | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q1: Groesse in Druckorientierung | P1S <= 256^3; JLC3DP <= 250 x 250 x 300, >= 30 x 30 x 10 | 244.1 x 243.5 x 25.0 mm | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q1: Flach auf dem Druckbett | Auflageflaeche > 20 cm^2 bei z = 0 | 242 cm^2 | ✅ bestanden | ✅ bestanden |
| Wandstaerke | Gitter Q1: Duennste Wand (Strahlmessung, 20000 Punkte) | P1S >= 0.84 mm (2 Bahnen); JLC3DP >= 2.5 mm | 2.50 mm bei (12.5, -173.3, 1.7) | ✅ bestanden | ✅ bestanden |
| Bohrungen | Gitter Q1: Kleinste Bohrung | JLC3DP >= 1.5 mm | Kernloch M3 2,6 mm; Magnet 3,2 mm; Lichtleiter 2,8 mm | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q1: Ueberschneidung mit Nachbarteilen | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q1: Spiel Schwalbenschwanz | P1S: >= 0,15 mm; JLC3DP: >= 0.5 mm Montagespiel | 0,19 mm (normal zur Flanke) | ✅ bestanden | ❌ nicht bestanden |
| Masshaltigkeit | Gitter Q1: Toleranzkette 4 Teile | Gesamtmass 480 mm, Fuge 0,2 mm | P1S: ~+-0,2 mm je Teil; JLC3DP: +-0,96 mm je Teil | ✅ bestanden | ❌ nicht bestanden |
| Passung | Gitter Q1: Kollision mit Platine (inkl. Bauteile) | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Geometrie | Gitter Q2: Gueltiger Volumenkoerper | 1 gueltiger Solid | valid=True, solids=1 | ✅ bestanden | ✅ bestanden |
| Netz | Gitter Q2: Geschlossen und mannigfaltig | solid, keine nicht-mannigfaltigen Kanten, keine Selbstdurchdringung | solid=True, nonmanifold=False, selfint=False | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q2: Groesse in Druckorientierung | P1S <= 256^3; JLC3DP <= 250 x 250 x 300, >= 30 x 30 x 10 | 239.4 x 243.5 x 25.0 mm | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q2: Flach auf dem Druckbett | Auflageflaeche > 20 cm^2 bei z = 0 | 239 cm^2 | ✅ bestanden | ✅ bestanden |
| Wandstaerke | Gitter Q2: Duennste Wand (Strahlmessung, 20000 Punkte) | P1S >= 0.84 mm (2 Bahnen); JLC3DP >= 2.5 mm | 2.50 mm bei (254.3, -54.5, 22.9) | ✅ bestanden | ✅ bestanden |
| Bohrungen | Gitter Q2: Kleinste Bohrung | JLC3DP >= 1.5 mm | Kernloch M3 2,6 mm; Magnet 3,2 mm; Lichtleiter 2,8 mm | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q2: Ueberschneidung mit Nachbarteilen | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q2: Spiel Schwalbenschwanz | P1S: >= 0,15 mm; JLC3DP: >= 0.5 mm Montagespiel | 0,19 mm (normal zur Flanke) | ✅ bestanden | ❌ nicht bestanden |
| Masshaltigkeit | Gitter Q2: Toleranzkette 4 Teile | Gesamtmass 480 mm, Fuge 0,2 mm | P1S: ~+-0,2 mm je Teil; JLC3DP: +-0,96 mm je Teil | ✅ bestanden | ❌ nicht bestanden |
| Passung | Gitter Q2: Kollision mit Platine (inkl. Bauteile) | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Geometrie | Gitter Q3: Gueltiger Volumenkoerper | 1 gueltiger Solid | valid=True, solids=1 | ✅ bestanden | ✅ bestanden |
| Netz | Gitter Q3: Geschlossen und mannigfaltig | solid, keine nicht-mannigfaltigen Kanten, keine Selbstdurchdringung | solid=True, nonmanifold=False, selfint=False | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q3: Groesse in Druckorientierung | P1S <= 256^3; JLC3DP <= 250 x 250 x 300, >= 30 x 30 x 10 | 244.1 x 240.0 x 25.0 mm | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q3: Flach auf dem Druckbett | Auflageflaeche > 20 cm^2 bei z = 0 | 242 cm^2 | ✅ bestanden | ✅ bestanden |
| Wandstaerke | Gitter Q3: Duennste Wand (Strahlmessung, 20000 Punkte) | P1S >= 0.84 mm (2 Bahnen); JLC3DP >= 2.5 mm | 2.50 mm bei (54.4, -253.5, 22.9) | ✅ bestanden | ✅ bestanden |
| Bohrungen | Gitter Q3: Kleinste Bohrung | JLC3DP >= 1.5 mm | Kernloch M3 2,6 mm; Magnet 3,2 mm; Lichtleiter 2,8 mm | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q3: Ueberschneidung mit Nachbarteilen | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q3: Spiel Schwalbenschwanz | P1S: >= 0,15 mm; JLC3DP: >= 0.5 mm Montagespiel | 0,19 mm (normal zur Flanke) | ✅ bestanden | ❌ nicht bestanden |
| Masshaltigkeit | Gitter Q3: Toleranzkette 4 Teile | Gesamtmass 480 mm, Fuge 0,2 mm | P1S: ~+-0,2 mm je Teil; JLC3DP: +-0,96 mm je Teil | ✅ bestanden | ❌ nicht bestanden |
| Passung | Gitter Q3: Kollision mit Platine (inkl. Bauteile) | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Geometrie | Gitter Q4: Gueltiger Volumenkoerper | 1 gueltiger Solid | valid=True, solids=1 | ✅ bestanden | ✅ bestanden |
| Netz | Gitter Q4: Geschlossen und mannigfaltig | solid, keine nicht-mannigfaltigen Kanten, keine Selbstdurchdringung | solid=True, nonmanifold=False, selfint=False | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q4: Groesse in Druckorientierung | P1S <= 256^3; JLC3DP <= 250 x 250 x 300, >= 30 x 30 x 10 | 239.4 x 240.0 x 25.0 mm | ✅ bestanden | ✅ bestanden |
| Bauraum | Gitter Q4: Flach auf dem Druckbett | Auflageflaeche > 20 cm^2 bei z = 0 | 239 cm^2 | ✅ bestanden | ✅ bestanden |
| Wandstaerke | Gitter Q4: Duennste Wand (Strahlmessung, 20000 Punkte) | P1S >= 0.84 mm (2 Bahnen); JLC3DP >= 2.5 mm | 2.38 mm bei (351.5, -478.6, 5.5) | ✅ bestanden | ❌ nicht bestanden |
| Bohrungen | Gitter Q4: Kleinste Bohrung | JLC3DP >= 1.5 mm | Kernloch M3 2,6 mm; Magnet 3,2 mm; Lichtleiter 2,8 mm | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q4: Ueberschneidung mit Nachbarteilen | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |
| Passung | Gitter Q4: Spiel Schwalbenschwanz | P1S: >= 0,15 mm; JLC3DP: >= 0.5 mm Montagespiel | 0,19 mm (normal zur Flanke) | ✅ bestanden | ❌ nicht bestanden |
| Masshaltigkeit | Gitter Q4: Toleranzkette 4 Teile | Gesamtmass 480 mm, Fuge 0,2 mm | P1S: ~+-0,2 mm je Teil; JLC3DP: +-0,96 mm je Teil | ✅ bestanden | ❌ nicht bestanden |
| Passung | Gitter Q4: Kollision mit Platine (inkl. Bauteile) | 0 mm^3 | 0.000 mm^3 | ✅ bestanden | ✅ bestanden |

## Hinweise und offene Punkte

- **Gitter Q1: Duennste Wand (Strahlmessung, 20000 Punkte):** Duenne Stellen: Waende der Schwalbenschwanz-Taschen und um die Magnetbohrungen.
- **Gitter Q1: Kleinste Bohrung:** FDM-Bohrungen fallen etwas kleiner aus: Magnetbohrungen ggf. mit 3,2-mm-Bohrer nacharbeiten.
- **Gitter Q1: Spiel Schwalbenschwanz:** Fuer JLC3DP zu eng (Toleranz +-0,4 % = +-1 mm auf 240 mm). Fuer eine Fremdfertigung Spiel auf >= 0,5 mm erhoehen.
- **Gitter Q2: Duennste Wand (Strahlmessung, 20000 Punkte):** Duenne Stellen: Waende der Schwalbenschwanz-Taschen und um die Magnetbohrungen.
- **Gitter Q2: Kleinste Bohrung:** FDM-Bohrungen fallen etwas kleiner aus: Magnetbohrungen ggf. mit 3,2-mm-Bohrer nacharbeiten.
- **Gitter Q2: Spiel Schwalbenschwanz:** Fuer JLC3DP zu eng (Toleranz +-0,4 % = +-1 mm auf 240 mm). Fuer eine Fremdfertigung Spiel auf >= 0,5 mm erhoehen.
- **Gitter Q3: Duennste Wand (Strahlmessung, 20000 Punkte):** Duenne Stellen: Waende der Schwalbenschwanz-Taschen und um die Magnetbohrungen.
- **Gitter Q3: Kleinste Bohrung:** FDM-Bohrungen fallen etwas kleiner aus: Magnetbohrungen ggf. mit 3,2-mm-Bohrer nacharbeiten.
- **Gitter Q3: Spiel Schwalbenschwanz:** Fuer JLC3DP zu eng (Toleranz +-0,4 % = +-1 mm auf 240 mm). Fuer eine Fremdfertigung Spiel auf >= 0,5 mm erhoehen.
- **Gitter Q4: Duennste Wand (Strahlmessung, 20000 Punkte):** Duenne Stellen: Waende der Schwalbenschwanz-Taschen und um die Magnetbohrungen.
- **Gitter Q4: Kleinste Bohrung:** FDM-Bohrungen fallen etwas kleiner aus: Magnetbohrungen ggf. mit 3,2-mm-Bohrer nacharbeiten.
- **Gitter Q4: Spiel Schwalbenschwanz:** Fuer JLC3DP zu eng (Toleranz +-0,4 % = +-1 mm auf 240 mm). Fuer eine Fremdfertigung Spiel auf >= 0,5 mm erhoehen.
- Druck: PLA, 0,4-mm-Duese, Gitter mit der Vorderseite (z = 25) auf dem Bett, Rueckrahmen mit der Wandseite auf dem Bett.

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `Gitter_Q1_obenlinks.step` | `222792215ee259d2…` |
| `Gitter_Q1_obenlinks_druckfertig.3mf` | `c512cc4f20b8e9e9…` |
| `Gitter_Q2_obenrechts.step` | `fa64acc04ee9a894…` |
| `Gitter_Q2_obenrechts_druckfertig.3mf` | `c497366ba2daddcc…` |
| `Gitter_Q3_untenlinks.step` | `6a3e61f23e66309d…` |
| `Gitter_Q3_untenlinks_druckfertig.3mf` | `f2b7cf264af943e5…` |
| `Gitter_Q4_untenrechts.step` | `269a55af3e87e167…` |
| `Gitter_Q4_untenrechts_druckfertig.3mf` | `2b1b72dd3c403de2…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

- [Bambu Lab P1S Spezifikation](https://wiki.bambulab.com/en/p1/manual/unboxing-p1s)
- [JLC3DP 3D Printing Design Guideline](https://jlc3dp.com/help/article/3D-Printing-Design-Guideline)
