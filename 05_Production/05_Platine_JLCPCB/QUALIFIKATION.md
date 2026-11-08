# Qualifikationsbericht – LED-Platine (4x identisch, Master/Slave)

| | |
|---|---|
| Bauteil | WortUhr LED-Board rev2, 234 x 234 mm, 2 Lagen |
| Fertiger | JLCPCB |
| Datum | 2026-11-08 |
| Stand | Git `e687f99` |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **JLCPCB: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | JLCPCB |
|---|---|---|---|---|
| Elektrisch | ERC (Schaltplan) | 0 Fehler | 0 Fehler | ✅ bestanden |
| Elektrisch | DRC Fehler | 0 | 0 | ✅ bestanden |
| Elektrisch | DRC Warnungen | nur kosmetisch (Bestueckungsdruck, Waermefalle) | {"silk_edge_clearance": 4, "silk_overlap": 4, "silk_over_copper": 3} | ✅ bestanden |
| Elektrisch | Offene Verbindungen | 0 | 0 | ✅ bestanden |
| Elektrisch | Schaltplan-/Layout-Abgleich | 0 Abweichungen | 0 | ✅ bestanden |
| Fertigung | Platinengroesse | <= 670 x 600 mm (Fertigung), <= 460 x 500 mm (Standard-Bestueckung), Soll 234 x 234 mm | 234.00 x 234.00 mm | ✅ bestanden |
| Fertigung | Lagenzahl | 2 | 2 | ✅ bestanden |
| Fertigung | Min. Leiterbahnbreite | >= 0.1 mm | 0.120 mm | ✅ bestanden |
| Fertigung | Via-Bohrung | >= 0.15 mm | 0.30 mm (232 Vias) | ✅ bestanden |
| Fertigung | Via-Durchmesser | >= 0.25 mm | 0.70 mm | ✅ bestanden |
| Fertigung | Restring Via (absolutes Minimum 2 Lagen 1 oz) | >= 0.18 mm | 0.200 mm | ✅ bestanden |
| Fertigung | Min. Bohrung durchkontaktiert (Pads) | >= 0.15 mm | 0.60 mm | ✅ bestanden |
| Fertigung | Min. Bohrung nicht durchkontaktiert | >= 0.5 mm | 0.65 mm (9 Stk.) | ✅ bestanden |
| Fertigung | Kupfer-Randabstand (Regel) | >= 0.2 mm | 0.30 mm | ✅ bestanden |
| Fertigung | Isolationsabstand (Netzklasse Default, vom DRC geprueft) | >= 0.1 mm | 0.20 mm | ✅ bestanden |
| Bestueckung | Passermarken (Standard-PCBA) | >= 3 je bestueckter Seite | oben 3, unten 3 | ✅ bestanden |
| Fertigung | Bestueckungsdruck Text | Hoehe >= 1.0 mm, Strich >= 0.15 mm | Hoehe 1.00 mm, Strich 0.15 mm | ✅ bestanden |
| Mechanik | Montageloecher M3 | 6 x Bohrung 4,3 mm (M3 mit +-0,65 mm Spiel) an den Stegkreuzungen | 6 Stk. | ✅ bestanden |
| Fertigungsdaten | Gerber vollstaendig | 9 Lagen | 12 Dateien, fehlend: - | ✅ bestanden |
| Fertigungsdaten | Bohrdateien | PTH + NPTH Excellon (mm) | WortUhr-NPTH.drl, WortUhr-PTH.drl | ✅ bestanden |
| Fertigungsdaten | Umriss im Gerber | 234 x 234 mm (+-0,1) | 234.00 x 234.00 mm | ✅ bestanden |
| Fertigungsdaten | Gerber-Archiv | ZIP lesbar, alle Dateien enthalten | 14 Dateien | ✅ bestanden |
| Stueckliste | BOM/CPL Master | jede Position mit Wert, Footprint und Koordinate | 171 Bauteile, 21 Positionen | ✅ bestanden |
| Stueckliste | BOM/CPL Slave | jede Position mit Wert, Footprint und Koordinate | 145 Bauteile, 3 Positionen | ✅ bestanden |
| Stueckliste | LED-Anzahl | 72 je Platine (2 je Kammer) | 72 | ✅ bestanden |
| Fertigungsdaten | 3D-Modell master | STEP-Export erfolgreich | ok | ✅ bestanden |
| Fertigungsdaten | 3D-Modell slave | STEP-Export erfolgreich | ok | ✅ bestanden |
| Fertigungsdaten | Schaltplan-PDF | vorhanden | ok | ✅ bestanden |

## Hinweise und offene Punkte

- Bestueckung: Master = Standard-PCBA (beidseitig, Passermarken vorhanden, Nutzenraender 'by JLCPCB' bestellen). Slave = nur Oberseite bestueckt; C1 (Unterseite) von Hand loeten oder ebenfalls Standard-PCBA.
- Loetstopplack: gruen empfohlen (min. Steg 0,10 mm); bei Schwarz/Weiss gilt 0,13 mm.
- SK6812RGBW: Footprint mit WS2812B-Pinbelegung (1 VDD, 2 DOUT, 3 VSS, 4 DIN) - vor Bestellung mit dem Datenblatt des gewaehlten Herstellers abgleichen.
- BH1750 (U5): Footprint WSOF6I selbst erstellt nach ROHM-Zeichnung, ungetestet.
- LCSC-Teilenummern in BOM leer - bei JLCPCB-Bestueckung zuordnen.
- Die 19 Kantenbruecken (0R 2512) werden nach dem Zusammenbau von Hand geloetet und sind nicht in der BOM.
- Bei > 3 A ueber die Hohlbuchse: 2-oz-Kupfer waehlen oder Strombegrenzung in der Firmware.

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `BOM_Master.csv` | `9d8294990ab9ac32…` |
| `BOM_Slave.csv` | `659a6c9a58c911d4…` |
| `CPL_Master.csv` | `1af49a2669deabbb…` |
| `CPL_Slave.csv` | `ee987d8fe182009d…` |
| `LED-Board_master.step` | `4d9abb74e21af8d8…` |
| `LED-Board_slave.step` | `766fd2dc83f3ab5b…` |
| `WortUhr_LED-Board_Gerber.zip` | `96cb7d020fb79604…` |
| `WortUhr_Schaltplan.pdf` | `0634af93900be182…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

- [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
