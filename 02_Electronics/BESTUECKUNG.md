# WortUhr LED-Board rev4 – Bestückung und Montage

Eine Platine (234 × 234 mm, 2 Lagen) wird **4× bestellt**. Jede Platine wird unter ein Gitterteil geschraubt. Die Platinen sind um 0°, 90°, 180° und 270° gedreht:

| Gitterteil | Lage | Drehung ggü. Master | Variante |
|---|---|---|---|
| Q4 | unten rechts | 0° | **Master** |
| Q2 | oben rechts | 90° | Slave |
| Q1 | oben links | 180° | Slave |
| Q3 | unten links | 270° | Slave |

Datenkette: Master (Q4) → Q2 → Q1 → Q3. An jeder Schnittkante liegen sich 5 Pads gegenüber: Bruecke_OUT (J4) der einen und Bruecke_IN (J3) der nächsten Platine, belegt mit GND, +5V, Daten, +5V, GND. Über den Spalt von ca. 1 mm wird je Pad-Paar ein **0-Ω-Widerstand 2512** gelötet. Das geschieht erst, wenn die Gitterteile zusammengesteckt sind.

| Kante | Brücken |
|---|---|
| Q4 → Q2, Q2 → Q1, Q1 → Q3 | alle 5 (GND, +5V, Daten, +5V, GND) |
| Q3 → Q4 | **nur GND und +5V**, die Daten-Brücke (Mitte) **nicht** bestücken, sonst wird die Kette zum Ring |

Insgesamt werden 19× 0 Ω 2512 benötigt. Jede Brücke ist für etwa 3 A ausgelegt; +5V und GND sind je zweifach vorhanden.

## Bestückung

| Bauteil | alle Platinen | nur Master |
|---|---|---|
| D1, D3, … (LED A je Kammer), C101, C103, … | ✓ | |
| D2, D4, … (LED B je Kammer), C102, C104, … | optional | |
| JP1–JP36 (Lötbrücke) | **schließen, wenn LED B nicht bestückt** | |
| D75 Minuten-LED (Außenecke) + C175 (Unterseite) | ✓ | |
| J3/J4 (Kantenbrücken, nur Pads), C1 (100 µF / 10 V) | ✓ | |
| U1 ESP32-S3-MINI-1, U2 AP2112K-3.3, U3 USBLC6, U4 74AHCT1G125, U5 BH1750FVI | | ✓ |
| J1 USB-C, F1, D80 (TVS SMBJ16A), U6 CH224K, U7 SCT2360, L1, SW1/SW2, R3–R8, R20–R25, C2–C9, C20–C29 | | ✓ |
| TP1–TP8 (Testpunkte, Pads auf der Unterseite) | nicht bestückt | |

**Minutenpunkte:** Jede Platine hat an der Außenecke eine Minuten-LED D75. In der Datenkette sitzt sie direkt nach Kammer (5,5). Durch die Drehung der Platinen leuchtet sie in allen vier Ecken unter den Ø-4-mm-Punkten der Frontplatte (18 mm vom Rand). Darüber liegt im Gitter ein runder Diffusor Ø 5,6 × 2 mm.


- **LED:** SK6812 RGBW, 5050. Im Footprint ist die Pinbelegung des WS2812B hinterlegt: 1 VDD, 2 DOUT, 3 VSS, 4 DIN. Vor der Bestellung mit dem Datenblatt des konkreten Herstellers vergleichen.
- **Montage Platine:** Die Platine wird von hinten mit **M3**-Kunststoffschrauben in die Kernlöcher der Gitterkreuzungen geschraubt. Die Kernlöcher haben Ø 2,6 mm und sind 9 mm tief. Je Platine gibt es 6 Löcher. Sie haben Ø 4,3 mm, also ±0,65 mm Spiel für M3. Das gleicht Druck- und Montagetoleranzen des Gitters aus.
  - H4, nahe der Uhrmitte: M3×8 mit Unterlegscheibe M3 (Ø 7 mm, DIN 125/ISO 7089), weil der Kopf direkt auf der Platine sitzt.
  - H1–H3, H5, H6: je **M3×20** durch den Rückrahmen. Der Kopf wird versenkt: bis Ø 6 mm und 3 mm hoch.
- **Rückrahmen:** 8 gerade Leisten, 10 mm dick.
  - Je Viertel eine lange Leiste mit 240 × 56 mm und 3 Schrauben und eine kurze mit 184 × 56 mm und 2 Schrauben.
  - Druck: `01_Mechanic/Rueckrahmen/Rueckrahmen_Druckplatte1_lange_Leisten.3mf` (4 lange Leisten, 244 × 243 mm) und `Rueckrahmen_Druckplatte2_kurze_Leisten.3mf` (4 kurze Leisten, 188 × 243 mm). Die Wandseite liegt auf dem Bett, die Dome zeigen nach oben.
  - In den langen Leisten oben (Q1, Q2) ist je ein Schlüsselloch für die Wandschraube: Kopf bis Ø 8 mm und 3 mm Höhe, Schaft bis 4,5 mm, Abstand 260 mm.
  - Ausschnitte für C1 sowie für USB-C (Q4 unten) und eine Tasche für die Spule L1 (Q4 lang). Die Bauteile bleiben mindestens 2 mm von der Wand entfernt.
- **Aufbauhöhe:** Frontplatte 1 mm, Gitter 25 mm, Rückrahmen 10 mm, zusammen **36 mm**. Von der Rückseite der Frontplatte bis zur Wand sind es 35 mm.
- **3D-Modelle:** Für ESP32-S3-MINI-1, USB-C (HRO TYPE-C-31-M-12) und BH1750 liegen in `3dmodels/` maßgenaue Platzhalter. In der KiCad-Bibliothek gibt es für diese Teile keine Modelle. Die 0-Ω-Brücken werden am Footprint J_OUT dargestellt.
- **Lichtsensor:** Der BH1750 (U5) sitzt oben unter dem Lichtleiter Mentor 1282.1000. Der Lichtleiter wird von vorn in das 2,8-mm-Loch im Gitter (Q4, unterer Rahmen) gedrückt.
- **ESP32-Pins:** LED-Daten IO8 (über 74AHCT1G125 auf 5 V), I2C SDA IO1, SCL IO2, PD-Status IO38, BOOT IO0.
- **Versorgung:** Nur USB-C. Der CH224K fordert 15 V an (Netzteil ab 45 W), der SCT2360 erzeugt daraus 5 V. An einem normalen USB-Port (5 V) laufen Logik und Flashen, die LEDs bleiben aus.

## Testpunkte (ab rev4)

| Pad | Netz | Lage auf der Unterseite |
|---|---|---|
| TP1 | +15V | zwischen F1 und dem Wandler |
| TP2 | +5V | an der VOUT-Leitung des Wandlers |
| TP3 | +3V3 | unter C3 |
| TP4, TP5 | GND | am Wandler, am ESP32 |
| TP6 | DIN | hinter R5, vor der ersten LED |
| TP7 | PD_GOOD | unter U6 |
| TP8 | EN | neben SW1 |

Die Pads haben keinen Bestückungsdruck. Die genauen Koordinaten stehen in `KiCad/tools/design.py` (`MASTER_PLACE`). Die Befunde, die zu rev4 geführt haben, stehen in `ANALYSE_rev3.md`.

## Bilder zum Pruefen ohne KiCad

In `02_Electronics/Bilder/` (und bei jedem Push im Workflow-Artefakt **WortUhr-Platine-Bilder**):

- `Platine_3D_oben.png`, `Platine_3D_unten.png`, `Platine_3D_schraeg_*.png`: 3D-Ansichten (Master mit allen Bauteilen)
- `Platine_Lagen.pdf`: eine Seite je Lage (Kupfer, Bestueckungsdruck, Loetstopp, Fab), beliebig zoombar
- `Platine_Kupfer_oben.svg`, `Platine_Kupfer_unten.svg` (gespiegelt, Blick von unten): Kupferlagen im Browser

Neu erzeugen: `python tools/pcb_images.py` (KiCad-Python).

## WLED

- LED-Typ: *SK6812/WS2814 RGBW*, Datenpin GPIO8, LED-Anzahl **292** (2 LEDs je Kammer) bzw. **148** (1 LED je Kammer): je Platine 36 Kammern + 1 Minuten-LED
- 2D-Matrix: bei 2 LEDs je Kammer 24×12 mit `03_Software/WLED/ledmap_2LED_24x12.json`, bei 1 LED je Kammer 12×12 mit `ledmap_1LED_12x12.json` (als `ledmap.json` hochladen). Die 4 Minuten-LEDs gehören nicht zur Matrix und bleiben in WLED aus.
- Stromgrenze (ABL) einstellen: höchstens 5 A (der Wandler liefert 6 A). WLED wertet PD_GOOD (GPIO38) nicht aus. Ohne PD-Netzteil liegen nur 5 V vom USB-Port an; dann die Stromgrenze auf diesen Port abstimmen.
- Lichtsensor: Usermod BH1750, I2C SDA 1 / SCL 2

## Erzeugung und Prüfung

Schaltplan und Platine entstehen per Skript aus `02_Electronics/KiCad/tools/design.py`. Die Dateien `.kicad_sch` nicht von Hand ändern. Regeln und Ablauf stehen in `02_Electronics/KiCad/ROUTING_GUIDE.md`.

```
python tools/gen_sch.py           # Schaltplan und Projekt-Symbolbibliothek; --check vergleicht nur
python tools/gen_ledmap.py        # 03_Software/WLED/ledmap_*.json
python tools/pcb_images.py        # Bilder der Platine (KiCad-Python)
python tools/build_pcb.py         # Platine komplett neu erzeugen und routen (KiCad-Python)
```

Achtung: `build_pcb.py` überschreibt die Platine, und Freerouting liefert bei jedem Lauf ein anderes Ergebnis. Kleine Änderungen werden deshalb in der gerouteten Platine nachgezogen.

Ob die Daten fertigungsreif sind, prüft `05_Production/tools/qualify_pcb.py`. Der aktuelle Stand steht in `05_Production/05_Platine_JLCPCB/QUALIFIKATION.md`.
