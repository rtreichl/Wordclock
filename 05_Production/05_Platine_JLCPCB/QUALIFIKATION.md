# Qualifikationsbericht – LED-Platine (4x identisch, Master/Slave)

| | |
|---|---|
| Bauteil | WortUhr LED-Board rev2, 234 x 234 mm, 2 Lagen |
| Fertiger | JLCPCB |
| Datum | 2026-11-10 |
| Stand | Git `a8529da` |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **JLCPCB: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | JLCPCB |
|---|---|---|---|---|
| Elektrisch | ERC (Schaltplan) | 0 Fehler, 0 Warnungen | 0 Fehler, 0 Warnungen | ✅ bestanden |
| Schaltplan | Generator-Stand (SCH-010) | Dateien im Projekt = Ausgabe von gen_sch.py | 0 abweichend | ✅ bestanden |
| Schaltplan | Netze der Zeichnung | jeder Pin am Netz aus design.py, jedes Netz benannt, kein Kurzschluss | 0 Befunde | ✅ bestanden |
| Schaltplan | Lesbarkeit (SCH-004) | keine ueberlappenden Texte, keine Leitung durch Text oder fremdes Symbol | 0 Befunde | ✅ bestanden |
| Elektrisch | DRC Fehler | 0 | 0 | ✅ bestanden |
| Elektrisch | DRC Warnungen | nur kosmetisch (Bestueckungsdruck, Waermefalle) | {"silk_edge_clearance": 4, "silk_over_copper": 98, "silk_overlap": 17} | ✅ bestanden |
| Elektrisch | Offene Verbindungen | 0 | 0 | ✅ bestanden |
| Elektrisch | Schaltplan-/Layout-Abgleich | 0 Abweichungen | 0 | ✅ bestanden |
| Fertigung | Platinengroesse | <= 670 x 600 mm (Fertigung), <= 460 x 500 mm (Standard-Bestueckung), Soll 234 x 234 mm | 234.00 x 234.00 mm | ✅ bestanden |
| Fertigung | Lagenzahl | 2 | 2 | ✅ bestanden |
| Fertigung | Min. Leiterbahnbreite | >= 0.1 mm | 0.150 mm | ✅ bestanden |
| Fertigung | Via-Bohrung | >= 0.15 mm | 0.30 mm (294 Vias) | ✅ bestanden |
| Fertigung | Via-Durchmesser | >= 0.25 mm | 0.70 mm | ✅ bestanden |
| Fertigung | Restring Via (absolutes Minimum 2 Lagen 1 oz) | >= 0.18 mm | 0.200 mm | ✅ bestanden |
| Fertigung | Min. Bohrung durchkontaktiert (Pads) | >= 0.15 mm | 0.60 mm | ✅ bestanden |
| Fertigung | Min. Bohrung nicht durchkontaktiert | >= 0.5 mm | 0.65 mm (8 Stk.) | ✅ bestanden |
| Fertigung | Kupfer-Randabstand (Regel) | >= 0.2 mm | 0.30 mm | ✅ bestanden |
| Fertigung | Isolationsabstand (Netzklasse Default, vom DRC geprueft) | >= 0.1 mm | 0.20 mm | ✅ bestanden |
| Bestueckung | Passermarken (Standard-PCBA) | >= 3 je bestueckter Seite | oben 3, unten 3 | ✅ bestanden |
| Fertigung | Bestueckungsdruck Text | Hoehe >= 1.0 mm, Strich >= 0.15 mm | Hoehe 1.00 mm, Strich 0.15 mm | ✅ bestanden |
| Layout | Kondensatoren zugeordnet (DEC-010) | jeder Kondensator ist Abblock-C eines Pins oder hat eine benannte andere Aufgabe | 86 Abblock-C, 6 andere, nicht zugeordnet: - | ✅ bestanden |
| Layout | Abblock-C am Versorgungspin (DEC-009) | Pad-Abstand <= 8 mm (C175: Unterseite, ueber Via) | max. 6.7 mm (C29), IC-C: C2 2.9, C3 2.9, C4 3.0, C6 2.6, C8 2.2, C9 5.6, C20 2.3, C21 4.3, C22 2.2, C26 2.2, C27 2.8, C28 1.1, C29 6.7 | ✅ bestanden |
| Layout | Leiterbahnbreite Versorgung (PWR-001) | +15V >= 0.8 mm, VBUS >= 0.6 mm, +3V3 >= 0.5 mm; Ausnahme +3V3 an U5 Pin 1 | eingehalten, Ausnahme +3V3 2.0 mm | ✅ bestanden |
| Layout | Antennenbereich frei (RF-001) | Sperrflaeche an U1 auf beiden Lagen fuer Flaechen, Leiterbahnen, Vias und Bauteile; DRC ohne Fehler | 1 Sperrflaeche(n), DRC-Fehler 0 | ✅ bestanden |
| Schaltplan | ESP32-Pins | Modulpin in design.py traegt im Symbol den Namen des GPIO | BOOT=GPIO0, SDA=GPIO1, SCL=GPIO2, LED_3V3=GPIO8, PD_GOOD=GPIO38 | ✅ bestanden |
| Layout | Kritische Teile gesperrt | Steckverbinder, Kantenbruecken, ESP32, Montageloecher, Passermarken | 16/16 | ✅ bestanden |
| Mechanik | Montageloecher M3 | 6 x Bohrung 4,3 mm (M3 mit +-0,65 mm Spiel) an den Stegkreuzungen | 6 Stk. | ✅ bestanden |
| Layout | Leiterbahnwinkel | nur horizontal, vertikal oder 45 Grad | 0 abweichend | ✅ bestanden |
| Fertigungsdaten | Gerber vollstaendig | 9 Lagen | 12 Dateien, fehlend: - | ✅ bestanden |
| Fertigungsdaten | Bohrdateien | PTH + NPTH Excellon (mm) | WortUhr-NPTH.drl, WortUhr-PTH.drl | ✅ bestanden |
| Fertigungsdaten | Umriss im Gerber | 234 x 234 mm (+-0,1) | 234.00 x 234.00 mm | ✅ bestanden |
| Fertigungsdaten | Gerber-Archiv | ZIP lesbar, alle Dateien enthalten | 14 Dateien | ✅ bestanden |
| Stueckliste | BOM DigiKey (1 Master + 3 Slaves) | Jede Position hat eine DigiKey-Nummer oder steht in der separaten Beschaffungsliste | 26 bei DigiKey, separat: SMBJ16A, USB-C, CH224K, SCT2360FPBR | ✅ bestanden |
| Stueckliste | BOM/CPL Master | jede Position mit Wert, Footprint und Koordinate | 190 Bauteile, 31 Positionen | ✅ bestanden |
| Stueckliste | BOM/CPL Slave | jede Position mit Wert, Footprint und Koordinate | 147 Bauteile, 3 Positionen | ✅ bestanden |
| Stueckliste | LED-Anzahl | 73 je Platine (2 je Kammer + 1 Minutenpunkt) | 73 | ✅ bestanden |
| Fertigungsdaten | 3D-Modell master | STEP-Export erfolgreich | ok | ✅ bestanden |
| Fertigungsdaten | 3D-Modell slave | STEP-Export erfolgreich | ok | ✅ bestanden |
| Fertigungsdaten | Schaltplan-PDF | vorhanden | ok | ✅ bestanden |

## Hinweise und offene Punkte

- **BOM DigiKey (1 Master + 3 Slaves):** LEDs sind nicht enthalten.
- Bestueckung: Master = Standard-PCBA (beidseitig, Passermarken vorhanden, Nutzenraender 'by JLCPCB' bestellen). Slave = nur Oberseite bestueckt; C1 (Unterseite) von Hand loeten oder ebenfalls Standard-PCBA.
- Loetstopplack: gruen empfohlen (min. Steg 0,10 mm); bei Schwarz/Weiss gilt 0,13 mm.
- SK6812RGBW: Footprint mit WS2812B-Pinbelegung (1 VDD, 2 DOUT, 3 VSS, 4 DIN) - vor Bestellung mit dem Datenblatt des gewaehlten Herstellers abgleichen.
- BH1750 (U5): Footprint WSOF6I selbst erstellt nach ROHM-Zeichnung, ungetestet.
- DigiKey: BOM_DigiKey.csv (Cut Tape, Satz aus 1 Master + 3 Slaves) direkt in den BOM Manager laden; J1, U6, U7 fuehrt DigiKey nicht, siehe BOM_Separat_Beschaffung.csv. LCSC-Teilenummern: ICs, Spule und USB-C eingetragen; Passive ordnet das JLCPCB-BOM-Tool zu. L1 (SRP1265A-3R3M) und F1 (1812L300/24SLER) ueber DigiKey beschaffen.
- Die 19 Kantenbruecken (0R 2512) werden nach dem Zusammenbau von Hand geloetet und sind nicht in der BOM.
- Schaltwandler U7 (SCT2360): Footprint gegen Package-Zeichnung geprueft, ungetestet. LEDs: SK6812 RGBNW (Pinbelegung des Angebots passt zum Footprint) werden separat beschafft.
- Versorgung: USB-C PD 15 V, Schaltwandler 5 V / 6 A, Firmware begrenzt auf geschaetzte 5 A.

## Freigegebene Dateien

| Datei | SHA256 |
|---|---|
| `BOM_DigiKey.csv` | `5ebf0bfc81d8e95c…` |
| `BOM_Master.csv` | `9da5644d183aec43…` |
| `BOM_Separat_Beschaffung.csv` | `a1ebdcee51e5f1ae…` |
| `BOM_Slave.csv` | `824dc6c89fba55fb…` |
| `CPL_Master.csv` | `407bc20657526c69…` |
| `CPL_Slave.csv` | `732dff21bc40172b…` |
| `LED-Board_master.step` | `31829997a1269e06…` |
| `LED-Board_slave.step` | `acc8e049925cd6bd…` |
| `WortUhr_LED-Board_Gerber.zip` | `b46be10b605b2426…` |
| `WortUhr_Schaltplan.pdf` | `7b70f90a1132c6c2…` |

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

- [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
