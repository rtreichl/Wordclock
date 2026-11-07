# WortUhr LED-Board rev2 – Bestückung und Montage

Eine Platine (234 × 234 mm, 2 Lagen) wird **4× bestellt**. Jede Platine wird unter ein Gitterteil geschraubt. Die Platinen sind um 0°, 90°, 180° und 270° gedreht:

| Gitterteil | Lage | Drehung ggü. Master | Variante |
|---|---|---|---|
| Q4 | unten rechts | 0° | **Master** |
| Q2 | oben rechts | 90° | Slave |
| Q1 | oben links | 180° | Slave |
| Q3 | unten links | 270° | Slave |

Datenkette: Master (Q4) → J_OUT → J_IN von Q2 → Q1 → Q3. Die Kabel sind 6-polig, JST XH, Pin 1 bis 1. Ausgang und Eingang benachbarter Platinen liegen sich an der Schnittkante direkt gegenüber.

## Bestückung

| Bauteil | alle Platinen | nur Master |
|---|---|---|
| D1, D3, … (LED A je Kammer), C101, C103, … | ✓ | |
| D2, D4, … (LED B je Kammer), C102, C104, … | optional | |
| JP1–JP36 (Lötbrücke) | **schließen, wenn LED B nicht bestückt** | |
| J3 (J_IN), J4 (J_OUT), C1 (470 µF) | ✓ | |
| U1 ESP32-S3-MINI-1, U2 AP2112K-3.3, U3 USBLC6, U4 74AHCT1G125, U5 BH1750FVI | | ✓ |
| J1 USB-C, J2 Hohlbuchse 5 V, D73 SS34, D74 SS54, SW1/SW2, R1–R8, C2–C8 | | ✓ |

- **LED:** SK6812 RGBW, 5050. Im Footprint ist die Pinbelegung des WS2812B hinterlegt: 1 VDD, 2 DOUT, 3 VSS, 4 DIN. Vor der Bestellung mit dem Datenblatt des konkreten Herstellers vergleichen.
- **Montage:** 4× M2-Kunststoffschraube (z. B. M2×8) von hinten durch H1–H4 in die Kernlöcher der Gitterkreuzungen.
- **Lichtsensor:** Der BH1750 (U5) sitzt oben unter dem Lichtleiter Mentor 1282.1000. Der Lichtleiter wird von vorn in das 2,8-mm-Loch im Gitter (Q4, unterer Rahmen) gedrückt.
- **ESP32-Pins:** LED-Daten IO16 (über 74AHCT1G125 auf 5 V), I2C SDA IO17, SCL IO18, BOOT IO0.

## WLED

- LED-Typ: *SK6812/WS2814 RGBW*, Datenpin GPIO16
- 2D-Matrix: bei 2 LEDs je Kammer 24×12 mit `WLED/ledmap_2LED_24x12.json`, bei 1 LED je Kammer 12×12 mit `ledmap_1LED_12x12.json` (als `ledmap.json` hochladen)
- Stromgrenze (ABL) einstellen: USB-C 2,5 A, Netzteil je nach Leistung, z. B. 4 A
- Lichtsensor: Usermod BH1750, I2C SDA 17 / SCL 18

## Erzeugung

Schaltplan und Platine werden per Skript erzeugt (KiCad-Python):

```
python tools/gen_sch.py      # WortUhr.kicad_sch + WortUhr.kicad_sym
python tools/gen_pcb.py      # WortUhr.kicad_pcb (Platzierung, LED-Feld geroutet, Flächen)
python tools/route_master.py # Master-Elektronik mit Freerouting routen
python tools/gen_ledmap.py   # WLED/ledmap_*.json
```

`route_master.py` erwartet Freerouting unter `~/.kicad-mcp/freerouting.jar` und eine Java-25-Laufzeit unter `~/.kicad-mcp/jre/`. Achtung: `gen_pcb.py` überschreibt die Platine. Manuelle Änderungen am Layout gehen dabei verloren.

Stand der Prüfung: ERC 0 Fehler. DRC 0 Fehler, 0 offene Verbindungen, Schaltplan-Abgleich 0. Es bleiben 11 kosmetische Hinweise zum Bestückungsdruck. Regeln: Leiterbahnen ab 0,1 mm (JLCPCB), Randabstand 0,45 mm.
