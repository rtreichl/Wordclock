# Qualifikationsbericht – LED-Platine (4x identisch, Master/Slave)

| | |
|---|---|
| Bauteil | WortUhr LED-Board rev2, 234 x 234 mm, 2 Lagen |
| Fertiger | JLCPCB |
| Datum | 2026-11-08 |
| Stand | Git `d71eccd` (mit nicht eingecheckten Aenderungen) |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **JLCPCB: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | JLCPCB |
|---|---|---|---|---|
| Elektrisch | ERC (Schaltplan) | 0 Fehler | 0 Fehler | ✅ bestanden |
| Elektrisch | DRC Fehler | 0 | 0 | ✅ bestanden |
| Elektrisch | DRC Warnungen | nur kosmetisch (Bestueckungsdruck, Waermefalle) | {"silk_edge_clearance": 4, "silk_over_copper": 91, "silk_overlap": 15} | ✅ bestanden |
| Elektrisch | Offene Verbindungen | 0 | 0 | ✅ bestanden |
| Elektrisch | Schaltplan-/Layout-Abgleich | 0 Abweichungen | 0 | ✅ bestanden |
| Fertigung | Platinengroesse | <= 670 x 600 mm (Fertigung), <= 460 x 500 mm (Standard-Bestueckung), Soll 234 x 234 mm | 234.00 x 234.00 mm | ✅ bestanden |
| Fertigung | Lagenzahl | 2 | 2 | ✅ bestanden |
| Fertigung | Min. Leiterbahnbreite | >= 0.1 mm | 0.150 mm | ✅ bestanden |
| Fertigung | Via-Bohrung | >= 0.15 mm | 0.30 mm (282 Vias) | ✅ bestanden |
| Fertigung | Via-Durchmesser | >= 0.25 mm | 0.70 mm | ✅ bestanden |
| Fertigung | Restring Via (absolutes Minimum 2 Lagen 1 oz) | >= 0.18 mm | 0.200 mm | ✅ bestanden |
| Fertigung | Min. Bohrung durchkontaktiert (Pads) | >= 0.15 mm | 0.60 mm | ✅ bestanden |
| Fertigung | Min. Bohrung nicht durchkontaktiert | >= 0.5 mm | 0.65 mm (8 Stk.) | ✅ bestanden |
| Fertigung | Kupfer-Randabstand (Regel) | >= 0.2 mm | 0.30 mm | ✅ bestanden |
| Fertigung | Isolationsabstand (Netzklasse Default, vom DRC geprueft) | >= 0.1 mm | 0.20 mm | ✅ bestanden |
| Bestueckung | Passermarken (Standard-PCBA) | >= 3 je bestueckter Seite | oben 3, unten 3 | ✅ bestanden |
| Fertigung | Bestueckungsdruck Text | Hoehe >= 1.0 mm, Strich >= 0.15 mm | Hoehe 1.00 mm, Strich 0.15 mm | ✅ bestanden |
| Layout | Abblock-C am Versorgungspin | Pad-Abstand <= 8 mm (C175: Unterseite, ueber Via) | max. 6.4 mm (C175), IC-C: C2 2.9, C3 2.9, C4 3.0, C6 2.6, C8 2.2 | ✅ bestanden |
| Layout | Kritische Teile gesperrt | Steckverbinder, Kantenbruecken, ESP32, Montageloecher, Passermarken | 16/16 | ✅ bestanden |
| Mechanik | Montageloecher M3 | 6 x Bohrung 4,3 mm (M3 mit +-0,65 mm Spiel) an den Stegkreuzungen | 6 Stk. | ✅ bestanden |
| Fertigungsdaten | Gerber vollstaendig | 9 Lagen | 12 Dateien, fehlend: - | ✅ bestanden |
| Fertigungsdaten | Bohrdateien | PTH + NPTH Excellon (mm) | WortUhr-NPTH.drl, WortUhr-PTH.drl | ✅ bestanden |
| Fertigungsdaten | Umriss im Gerber | 234 x 234 mm (+-0,1) | 234.00 x 234.00 mm | ✅ bestanden |
| Fertigungsdaten | Gerber-Archiv | ZIP lesbar, alle Dateien enthalten | 14 Dateien | ✅ bestanden |
| Stueckliste | BOM/CPL Master | jede Position mit Wert, Footprint und Koordinate | 185 Bauteile, 28 Positionen | ✅ bestanden |
| Stueckliste | BOM/CPL Slave | jede Position mit Wert, Footprint und Koordinate | 147 Bauteile, 3 Positionen | ✅ bestanden |
| Stueckliste | LED-Anzahl | 73 je Platine (2 je Kammer + 1 Minutenpunkt) | 73 | ✅ bestanden |
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
| `BOM_Master.csv` | `c0eebceb345d8078…` |
| `BOM_Slave.csv` | `824dc6c89fba55fb…` |
| `CPL_Master.csv` | `53eb4810f600e6aa…` |
| `CPL_Slave.csv` | `beb01b59540d24ad…` |
| `LED-Board_master.step` | `ef629840de8503cd…` |
| `LED-Board_slave.step` | `8248fea5e82ac849…` |
| `WortUhr_LED-Board_Gerber.zip` | `1f78223667f21a75…` |
| `WortUhr_Schaltplan.pdf` | `328ccea06022335b…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

- [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
