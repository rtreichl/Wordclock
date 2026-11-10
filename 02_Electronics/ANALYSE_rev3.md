# LED-Board rev3 – Analysen zur Stromversorgung

Stand 2026-11-10, Platine nach Commit „C20 moved to U6 pin 1“. Review nach Teil 2 des Leitfadens (`KiCad/ROUTING_GUIDE.md`): Jeder Befund hat die zwölf Pflichtfelder. Gerechnet wurde mit Werten aus den Datenblättern in `06_Datenblätter/` und mit Maßen aus der Platine. Wo ein Wert fehlt, steht das dabei; er wurde nicht ersetzt. Gemessen wurde nichts, die Platine ist noch nicht gebaut.

## Ergebnis

| Nr. | Befund | Schwere | Handlung |
|---|---|---|---|
| A1 | Wandler U7 wird bei 5 A Dauerlast rechnerisch 85 bis 100 K wärmer als die Umgebung | Major | messen; bis dahin Firmware-Grenze senken (Entscheidung offen) |
| A2 | Eingangskondensator: ein 22 µF statt der empfohlenen zwei | Major | rev4: zweiter 22 µF an VIN |
| A3 | Kantenbrücken: kein Bauteil mit belegter Strombelastbarkeit festgelegt | Major | Bauteil festlegen, in die Beschaffungsliste aufnehmen |
| A4 | Ausgangskondensatoren 22 µF / 10 V bei 5 V: wirksame Kapazität nicht belegt | Minor | rev4: 16 V oder 25 V; DC-Bias-Kurve besorgen |
| A5 | Sicherung F1: Datenblatt fehlt, Reserve bei Wärme nicht belegt | Minor | Datenblatt besorgen, Derating prüfen |
| A6 | LED-Strom je Kanal (16 mA) ist eine Annahme der Firmware, kein Datenblattwert | Minor | an einer Platine messen |
| A7 | Spannungsabfall über Flächen, Vias und Brücken ist unkritisch | Information | keine |
| A8 | Kein Überspannungsschutz an +15V | Minor | rev4-Kandidat |
| A9 | Keine Testpunkte | Minor | rev4-Kandidat |

Ohne Befund geprüft: Beschaltung des CH224K entspricht dem Referenzbild des Handbuchs (1 kΩ nach VDD, 10 kΩ am VBUS-Pin, 1 µF an VDD). Teiler R22/R23, Spule 3,3 µH und 66 µF am Ausgang entsprechen Tabelle 3 und 4 des SCT2360-Datenblatts für 5 V bei 400 kHz. VREF ist 0,6 V (0,594 bis 0,606 V), das ergibt 5,01 V. Die Spule SRP1265A-3R3M (Isat 30 A, Irms 18 A) hat reichlich Reserve.

## Rechenwerte

| Größe | Rechnung | Wert |
|---|---|---|
| Größter LED-Strom ohne Grenze | 292 LEDs × 4 Kanäle × 16 mA (Annahme, siehe A6) | 18,7 A |
| Firmware-Grenze / Wandler | – | 5 A / 6 A |
| Rippelstrom der Spule | Vout × (1 − Vout/Vin) / (L × fsw) = 5 × 0,667 / (3,3 µH × 400 kHz) | 2,5 A Spitze-Spitze |
| Spitzenstrom der Spule bei 5 A / 6 A | Iout + Rippel/2 | 6,3 A / 7,3 A |
| Wirkungsgrad bei 5 A, Vin 15 V | abgelesen aus Figure 1 (12 V: etwa 93,5 %) und Figure 4 (24 V: etwa 90 %) | etwa 93 %, ± 1 Punkt |
| Verlust gesamt bei 5 A / 4 A / 2 A | Pout × (1/η − 1) | 1,9 W / 1,2 W / 0,5 W |
| davon Spule bei 5 A | I² × DCR = 25 × 6,8 mΩ | 0,17 W |
| Eingangsstrom bei 5 A / 6 A | Pout / η / 15 V | 1,8 A / 2,2 A |
| Eingangsrippel, ein 22 µF nominal | Iout / (Cin × fsw) × D × (1 − D), D = 1/3 | 126 mV bei 5 A, 152 mV bei 6 A |
| Eingangsrippel, zwei 22 µF nominal | wie oben | 63 mV bei 5 A, 76 mV bei 6 A |
| Ausgangsrippel, 66 µF nominal | Gleichung 7 des Datenblatts | 12 mV |
| Flächenwiderstand 35 µm Kupfer | ρ / d | 0,49 mΩ je Quadrat |
| Ein Via 0,9/0,5 mm, 1,6 mm lang, 20 µm Hülse | ρ × l / (π × d × s) | 0,9 mΩ |

## Befunde

### A1 – Erwärmung des Wandlers U7

1. **Rule ID:** PWR-004; neue Regel THM-001 vorgeschlagen (Verlustleistung und Sperrschichttemperatur je Leistungsbauteil nachweisen).
2. **Regel:** Thermische Auslegung des Schaltwandlers.
3. **Schwere:** Major.
4. **Einstufung:** ANALYSIS.
5. **Betroffen:** U7 (SCT2360), L1, GND-Fläche unten, +5V.
6. **Ist-Zustand:** U7 sitzt auf der Unterseite, Wärmeabfuhr über die Pads in die GND-Fläche und 8 GND-Vias im Umfeld. Darüber liegt der Rückrahmen mit der Tasche für L1.
7. **Erklärung:** Bei 5 A und 15 V Eingang gehen etwa 1,9 W verloren, davon rund 1,7 W im IC. Das Datenblatt nennt RθJA = 50 K/W als Richtwert für die JEDEC-Platine. Das ergibt 85 K Übertemperatur, bei 1 Prozentpunkt schlechterem Wirkungsgrad 100 K.
8. **Auswirkung:** Bei 25 °C Umgebung liegt die Sperrschicht rechnerisch bei 110 bis 125 °C, im geschlossenen Rückrahmen höher. Die Grenze ist 125 °C. Der Baustein schaltet bei Übertemperatur ab; die Uhr würde dann flackern oder ausgehen. Im Uhrbetrieb (bis etwa 2 A) sind es rund 0,5 W und 20 bis 25 K: unkritisch.
9. **Empfehlung:** An der ersten Platine bei 5 A die Gehäusetemperatur messen. Bis dahin die Firmware-Grenze auf 4 A setzen (1,2 W, etwa 55 K). Für rev4 mehr Kupfer und Vias unter U7 prüfen.
10. **Nachweis:** Temperaturmessung nach 30 Minuten bei 5 A im montierten Zustand.
11. **Quelle:** SCT2360 Rev. 1.0: Thermal Information (RθJA 50), Figure 1 und 4 (Wirkungsgrad), Absolute Maximum Ratings.
12. **Vertrauen:** Mittel. Der Wirkungsgrad ist aus Kurven für 12 V und 24 V abgelesen, RθJA gilt für eine andere Platine.

### A2 – Eingangskondensator des Wandlers

1. **Rule ID:** DEC-010, DEC-008.
2. **Regel:** Abblockung nach Datenblatt; wirksame Kapazität bei Betriebsspannung.
3. **Schwere:** Major.
4. **Einstufung:** CONDITIONAL (Herstellerempfehlung).
5. **Betroffen:** C21 (22 µF / 25 V, 1206), C22 (100 nF), U7 Pin 1, +15V.
6. **Ist-Zustand:** Ein 22-µF-Kondensator und 100 nF an VIN.
7. **Erklärung:** Das Datenblatt empfiehlt „generally two 22uF“ und einen Eingangsrippel unter 100 mV. Mit einem 22 µF nominal sind es 126 mV bei 5 A. Bei 15 V an einem 25-V-Kondensator ist die wirksame Kapazität kleiner; die DC-Bias-Kurve des CC1206MKX5R8BB226 liegt nicht vor.
8. **Auswirkung:** Höherer Rippel auf +15V, mehr Rippelstrom durch C21, mehr Störungen auf der USB-Leitung. Kein Ausfall zu erwarten.
9. **Empfehlung:** rev4: zweiten 22 µF / 25 V (oder 35 V) direkt neben C21 an VIN und PGND setzen. Platz in der Hot-Loop-Anordnung nach Figure 22 prüfen.
10. **Nachweis:** Rippel an C22 mit dem Oszilloskop bei 5 A.
11. **Quelle:** SCT2360, Input Capacitor Selection, Gleichung 4.
12. **Vertrauen:** Hoch für die Abweichung von der Empfehlung, mittel für den Rippelwert.

### A3 – Strom über die Kantenbrücken

1. **Rule ID:** PWR-004; neue Regel PWR-005 vorgeschlagen (jede Kantenbrücke ist ein Bauteil mit belegter Strombelastbarkeit und steht in der Beschaffungsliste).
2. **Regel:** Stromtragfähigkeit im Hauptstromweg.
3. **Schwere:** Major.
4. **Einstufung:** ANALYSIS.
5. **Betroffen:** J3, J4 (je 2 × +5V, 2 × GND, 1 × Daten), 19 × 0 Ω 2512, +5V, GND.
6. **Ist-Zustand:** `BESTUECKUNG.md` nennt „etwa 3 A je Brücke“ ohne Bauteil und ohne Quelle. Die Brücken stehen in keiner Stückliste. Die Versorgung bildet einen Ring über alle vier Kanten. Jedes +5V-Pad hängt über zwei Vias 0,9/0,5 mm an der Fläche oben, die GND-Pads liegen direkt in der Fläche unten.
7. **Erklärung:** Bei 5 A Gesamtstrom und gleichmäßiger Last fließen 1,9 A über jede Kante des Masters, also 0,9 A je Brücke. Zieht eine Nachbarplatine allein den ganzen Strom, sind es 3,75 A über eine Kante und 1,9 A je Brücke. Ist der Ring an einer Kante offen, trägt die andere Kante 5 A, also 2,5 A je Brücke und 1,25 A je Via.
8. **Auswirkung:** Übliche 0-Ω-Widerstände 2512 sind oft nur mit 2 A angegeben. Im Normalbetrieb reicht das, bei einer kalten Lötstelle oder ungleicher Last nicht sicher.
9. **Empfehlung:** Ein Bauteil mit mindestens 2,5 A, besser 5 A festlegen (strombelastbare Brücke, Bauform 2512) und in `BOM_Separat_Beschaffung.csv` aufnehmen. Die Angabe in `BESTUECKUNG.md` danach mit Quelle versehen.
10. **Nachweis:** Datenblatt des gewählten Bauteils; nach dem Aufbau Spannungsabfall je Kante bei 5 A messen.
11. **Quelle:** Rechnung aus der Ringstruktur; Via-Belastbarkeit nach IPC-2221 (etwa 2 A bei 10 K für 0,5 mm Bohrung, 20 µm Hülse).
12. **Vertrauen:** Hoch für die Ströme, niedrig für die Belastbarkeit üblicher Brücken (kein Datenblatt geprüft).

### A4 – Ausgangskondensatoren unter DC-Bias

1. **Rule ID:** DEC-008.
2. **Regel:** Wirksame Kapazität bei Betriebsspannung.
3. **Schwere:** Minor.
4. **Einstufung:** ANALYSIS.
5. **Betroffen:** C23, C24, C25 (22 µF / 10 V, 0805), C9 (22 µF / 10 V an +3V3), C1 (100 µF Elko je Platine).
6. **Ist-Zustand:** 3 × 22 µF nominal wie in Tabelle 3 und 4. Die Kondensatoren laufen bei 5 V, also bei der halben Nennspannung.
7. **Erklärung:** Das Datenblatt des Wandlers warnt ausdrücklich vor dem Kapazitätsverlust unter Gleichspannung und verlangt Reserve bei der Nennspannung. Die DC-Bias-Kurve des C0805C226M8PACTU liegt nicht vor. Die vier Elkos C1 stützen zusätzlich, haben aber einen höheren Innenwiderstand.
8. **Auswirkung:** Mehr Ausgangsrippel und schlechteres Lastsprungverhalten als gerechnet. Mit halber Kapazität wären es rund 24 mV statt 12 mV Rippel: unkritisch für die LEDs.
9. **Empfehlung:** rev4: 22 µF mit 16 V oder 25 V in 1206. Vorher die Kurve des Herstellers besorgen.
10. **Nachweis:** DC-Bias-Kurve; Rippelmessung am Ausgang.
11. **Quelle:** SCT2360, Output Capacitor Selection, Gleichung 7, Tabelle 3 und 4.
12. **Vertrauen:** Mittel.

### A5 – Sicherung F1

1. **Rule ID:** DES-001.
2. **Regel:** Datenblatt vor der Auslegung.
3. **Schwere:** Minor.
4. **Einstufung:** ANALYSIS.
5. **Betroffen:** F1 (1812L300/24SLER), VBUS, +15V.
6. **Ist-Zustand:** Haltestrom laut Typbezeichnung 3,0 A, 24 V. Ein Datenblatt liegt in `06_Datenblätter/` nicht vor (die Datei `f1dffd65…pdf` ist eine zweite Kopie des SCT2360-Datenblatts).
7. **Erklärung:** Der Eingangsstrom ist 1,8 A bei 5 A am Ausgang und 2,2 A bei 6 A. Der Haltestrom einer PTC-Sicherung sinkt mit der Temperatur; die Kurve ist nicht belegt.
8. **Auswirkung:** Bei Wärme im Rückrahmen und voller Last kann die Sicherung ansprechen, obwohl kein Fehler vorliegt.
9. **Empfehlung:** Datenblatt ablegen und den Haltestrom bei 60 °C gegen 2,2 A prüfen.
10. **Nachweis:** Derating-Kurve des Herstellers.
11. **Quelle:** Rechnung; Typbezeichnung.
12. **Vertrauen:** Mittel.

### A6 – Annahme zum LED-Strom

1. **Rule ID:** DES-001.
2. **Regel:** Auslegung auf belegte Werte.
3. **Schwere:** Minor.
4. **Einstufung:** ANALYSIS.
5. **Betroffen:** D1 bis D75, Firmware (`AMP_PER_CHANNEL` in `wortuhr.h`), alle Stromangaben in diesem Bericht.
6. **Ist-Zustand:** Die Firmware rechnet mit 16 mA je voll angesteuertem Kanal. Der Leitfaden nennt an anderer Stelle 60 mA je LED.
7. **Erklärung:** Das SK6812-Datenblatt nennt nur „0.25 Watt“ und keinen Strom je Kanal. Die Stromgrenze der Firmware ist eine Schätzung auf dieser Annahme.
8. **Auswirkung:** Ist der wirkliche Strom höher, liegt die wirkliche Grenze über 5 A. Der Wandler begrenzt dann selbst.
9. **Empfehlung:** An einer bestückten Platine den Strom für Rot, Grün, Blau und Weiß einzeln messen und den Wert in `wortuhr.h` eintragen.
10. **Nachweis:** Strommessung mit 73 LEDs je Farbe.
11. **Quelle:** SK6812RGBW-Spezifikation, Abschnitt 7 und 8.
12. **Vertrauen:** Hoch, dass der Wert nicht belegt ist.

### A7 – Spannungsabfall

1. **Rule ID:** PWR-004.
2. **Regel:** Keine Einschnürung im Hauptstromweg.
3. **Schwere:** Information.
4. **Einstufung:** ANALYSIS.
5. **Betroffen:** +5V oben, GND unten, 6 Vias am Wandlerausgang, Kantenbrücken.
6. **Ist-Zustand:** Der Wandlerausgang geht über 6 Vias 0,9/0,5 mm auf die +5V-Fläche. Je Kante zwei Brücken je Netz.
7. **Erklärung:** Die 6 Vias haben zusammen 0,15 mΩ (unter 1 mV bei 5 A, je Via 0,8 A). Eine Kante hat je Netz etwa 1,2 mΩ Flächenanteil plus die halbe Brücke. Im ungünstigsten Fall (5 A auf der gegenüberliegenden Platine) sind das je Netz 31 mV bei 10 mΩ je Brücke und 131 mV bei 50 mΩ je Brücke.
8. **Auswirkung:** Höchstens etwa 0,26 V weniger an der fernsten Platine. Die LEDs sind für 4,5 bis 5,5 V spezifiziert, der Wandler liefert 5,01 V.
9. **Empfehlung:** Keine Änderung. Brücken mit niedrigem Widerstand wählen (siehe A3).
10. **Nachweis:** Spannung an C1 der fernsten Platine bei 5 A.
11. **Quelle:** Rechnung; die Brückenwiderstände sind angenommen.
12. **Vertrauen:** Mittel.

### A8 – Überspannungsschutz an +15V

1. **Rule ID:** keine; Kandidat für rev4.
2. **Regel:** Schutz des Eingangs.
3. **Schwere:** Minor.
4. **Einstufung:** SOFT.
5. **Betroffen:** VBUS, +15V, U7 (VIN höchstens 32 V, Betrieb bis 28 V), U6 (VBUS-Pin 13,5 V, deshalb R21).
6. **Ist-Zustand:** ESD-Schutz U3 nur an den Datenleitungen. An VBUS und +15V gibt es keine Schutzdiode.
7. **Erklärung:** Der Wandler hat gegenüber 15 V Reserve. Liefert ein Netzteil fälschlich 20 V, bleibt U7 innerhalb seiner Grenzen. Überschwinger beim Einstecken entstehen bei 5 V, weil PD erst danach hochschaltet.
8. **Auswirkung:** Ohne Diode kein Schutz gegen Stoßspannungen über das Kabel.
9. **Empfehlung:** rev4: TVS-Diode an +15V hinter F1, Sperrspannung mindestens 16 V, Klemmspannung unter 28 V. Bauteil nach Datenblatt auswählen.
10. **Nachweis:** Datenblatt der Diode gegen die Grenzen von U7.
11. **Quelle:** SCT2360 Absolute Maximum Ratings; CH224-Handbuch Abschnitt 7.1.
12. **Vertrauen:** Mittel.

### A9 – Testpunkte

1. **Rule ID:** keine; neue Regel TST-001 vorgeschlagen (jede Versorgung und jedes Signal für die Inbetriebnahme hat einen Testpunkt).
2. **Regel:** Prüfbarkeit.
3. **Schwere:** Minor.
4. **Einstufung:** SOFT.
5. **Betroffen:** +15V, +5V, +3V3, GND, DIN, PD_GOOD, EN, TXD0/RXD0 (Pins 39/40, heute unbeschaltet).
6. **Ist-Zustand:** Kein Testpunkt. Gemessen werden kann nur an Bauteil-Pads.
7. **Erklärung:** Die Messungen aus A1, A2, A3 und A6 brauchen Zugang zu diesen Netzen. Ohne USB-Verbindung gibt es keinen zweiten Weg zur Konsole.
8. **Auswirkung:** Inbetriebnahme und Fehlersuche sind mühsamer und riskanter (Abrutschen an feinen Pads).
9. **Empfehlung:** rev4: Testpads 1,5 mm im Master-Streifen auf der Unterseite, je eines für die genannten Netze, zwei für GND.
10. **Nachweis:** Sichtprüfung, Prüfung in `qualify_pcb.py`.
11. **Quelle:** Erfahrungsregel.
12. **Vertrauen:** Hoch.

## Vorschlag für rev4

| Änderung | aus Befund | Aufwand |
|---|---|---|
| Zweiter 22 µF an VIN von U7 | A2 | Schaltplan, Platzierung am Wandler, Handrouting |
| Ausgangskondensatoren 16 V oder 25 V | A4 | nur Bauteilwahl, wenn die Bauform bleibt |
| TVS-Diode an +15V | A8 | Schaltplan, Platzierung an F1 |
| Testpunkte | A9 | Schaltplan, Platzierung, wenig Routing |
| Mehr Kupfer und Vias unter U7 | A1 | Layout am Wandler, nach der Messung entscheiden |
| Netznamen `Cnn_A_OUT` umbenennen | SCH-009 | nur Namen, aber Platine und Schaltplan gemeinsam |

Ohne neue Platine möglich: Bauteil für die Kantenbrücken festlegen (A3), Firmware-Grenze anpassen (A1), Datenblätter für F1 und die Kondensatoren ablegen (A4, A5).
