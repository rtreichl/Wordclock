# WortUhr – Produktionsdaten

Stand Git `8c9f8da`, geprueft am 2026-11-08. In diesem Ordner liegen nur Daten, die alle Qualifikationspruefungen fuer den jeweiligen Fertiger bestanden haben. Gesperrte Bauteile haben einen Bericht, aber keine Dateien.

| Bauteil | Ordner | Freigabe | Pruefungen | Dateien |
|---|---|---|---|---|
| LED-Platine (4x identisch, Master/Slave) | [`05_Platine_JLCPCB`](05_Platine_JLCPCB/QUALIFIKATION.md) | JLCPCB: ✅ | 30 ✅ / 0 ❌ | 8 |
| Frontplatte Cortenstahl 1 mm | [`01_Frontplatte_Laser`](01_Frontplatte_Laser/QUALIFIKATION.md) | laserteile-online.eu: ✅ | 19 ✅ / 0 ❌ | 1 |
| Diffusor Opal-Acrylglas 2 mm (144 x 30 x 30, 4 x Ø 5,6) | [`02_Diffusor_Laser`](02_Diffusor_Laser/QUALIFIKATION.md) | Eigenzuschnitt: ✅, Cutworks: ✅ | 15 ✅ / 0 ❌ | 2 |
| Lichtgitter Q1–Q4 | [`03_Gitter_3D-Druck`](03_Gitter_3D-Druck/QUALIFIKATION.md) | Bambu Lab P1S: ✅, JLC3DP: ✅ | 88 ✅ / 0 ❌ | 16 |
| Rückrahmen (8 Leisten, 2 Druckplatten) | [`04_Rueckrahmen_3D-Druck`](04_Rueckrahmen_3D-Druck/QUALIFIKATION.md) | Bambu Lab P1S: ✅, JLC3DP: ✅ | 114 ✅ / 0 ❌ | 10 |
| Firmware ESPHome (ESP32-S3) | [`06_Firmware`](06_Firmware/QUALIFIKATION.md) | Build: ✅ | 13 ✅ / 0 ❌ | 0 |
| WLED-LED-Maps | [`07_WLED`](07_WLED/QUALIFIKATION.md) | WLED: ✅ | 3 ✅ / 0 ❌ | 2 |

Neu erzeugen: siehe `tools/README.md`.
