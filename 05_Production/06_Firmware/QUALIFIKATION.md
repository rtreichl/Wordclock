# Qualifikationsbericht – Firmware ESPHome (ESP32-S3)

| | |
|---|---|
| Bauteil | 03_Software/ESPHome/wortuhr.yaml |
| Fertiger | ESPHome |
| Datum | 2026-11-08 |
| Stand | Git `d71eccd` (mit nicht eingecheckten Aenderungen) |
| Pruefung | automatisch, `05_Production/tools/` |
| Ergebnis | **Build: FREIGEGEBEN** |

## Pruefergebnisse

| Kategorie | Pruefung | Kriterium | Messwert | ESPHome |
|---|---|---|---|---|
| Konsistenz | LED-/Buchstaben-Layout aktuell | neu erzeugtes wortuhr_layout.h identisch | identisch | ✅ bestanden |
| Konsistenz | LED-Zuordnung vollstaendig | 144 Kammern, jeder Index 0..143 genau einmal | 144 Eintraege | ✅ bestanden |
| Logik | Woerter liegen auf den richtigen Buchstaben | 31 Woerter | Abweichungen: - | ✅ bestanden |
| Logik | Satzbildung fuer alle 288 Zeiten | jede Zeit endet auf ein Stundenwort | alle ok | ✅ bestanden |
| Konfiguration | ESPHome-Konfiguration gueltig | esphome config ohne Fehler | gueltig | ✅ bestanden |
| Anforderung | Uhrzeit ohne Home Assistant | time: platform sntp; api reboot_timeout 0s | sntp=True, reboot_timeout_0=True | ✅ bestanden |
| Anforderung | Bedienung ohne Home Assistant | web_server + captive_portal + Ersatz-Hotspot | web_server=True, captive_portal=True, ap=True | ✅ bestanden |
| Sicherheit | Keine Zugangsdaten im Repository | secrets.yaml in .gitignore, nur Vorlage eingecheckt | ok | ✅ bestanden |
| Build | Kompiliert (ESP32-S3, ESP-IDF) | erfolgreich | erfolgreich | ✅ bestanden |
| Build | Speicherreserve | RAM < 60 %, Flash < 80 % (Reserve fuer OTA/Erweiterungen) | RAM 32.0 %, Flash 24.0 % | ✅ bestanden |
| Build | Keine Compiler-Warnungen im eigenen Code | 0 | 0 | ✅ bestanden |
| Konsistenz | LED-Anzahl in der Kette | num_leds = 4 x (36 x leds_per_cell + 1) | num_leds 292, leds_per_cell 2 | ✅ bestanden |
| Logik | Minutenpunkte | Minute mod 5 -> 1..4 Punkte im Uhrzeigersinn ab oben links | 1: LED 158 (oben links), 2: LED 85 (oben rechts), 3: LED 12 (unten rechts), 4: LED 231 (unten links) | ✅ bestanden |

## Hinweise und offene Punkte

- **Satzbildung fuer alle 288 Zeiten:** Beispiele: 00:00 IST MITTERNACHT; 00:15 IST VIERTEL NACH ZWÖLF; 00:25 IST FÜNF VOR HALB EINS; 00:30 IST HALB EINS; 00:40 IST ZWANZIG VOR EINS; 00:55 IST FÜNF VOR EINS
- Binaerdateien werden nicht eingecheckt: sie enthalten WLAN-Daten und API-Schluessel aus secrets.yaml. Fuer das Geraet lokal bauen: `03_Software/ESPHome/.venv/Scripts/esphome.exe run wortuhr.yaml`.

## Freigegebene Dateien

Keine – das Bauteil ist fuer keinen Fertiger freigegeben. Die Daten bleiben in ihrem Quellordner.

## Grundlage (Fertigerangaben, abgerufen 2026-11-07)

