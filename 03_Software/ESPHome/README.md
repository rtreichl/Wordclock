# WortUhr – ESPHome-Firmware

Die Firmware für den ESP32-S3 auf der Master-Platine. Die Uhr bezieht die Uhrzeit **per NTP direkt aus dem Internet**. Sie läuft also auch ohne Home Assistant. Ist HA vorhanden, erscheint sie dort automatisch als ESPHome-Gerät.

## Dateien

| Datei | Inhalt |
|---|---|
| `wortuhr.yaml` | ESPHome-Konfiguration |
| `wortuhr.h` | Uhrzeit → Wörter, Ausgabe auf die LEDs mit Überblendung |
| `wortuhr_layout.h` | Buchstabenraster und LED-Reihenfolge. Wird von `tools/gen_layout.py` aus SVG und Platinendaten erzeugt, nicht von Hand ändern. |
| `secrets.example.yaml` | Vorlage für `secrets.yaml`: WLAN, Schlüssel. `secrets.yaml` wird nicht eingecheckt. |

## Funktionen

- **Uhrzeit:** SNTP über `de.pool.ntp.org` und `time.cloudflare.com`, Zeitzone Europe/Berlin mit Sommerzeit. `api: reboot_timeout: 0s` verhindert, dass der ESP neu startet, wenn HA nicht erreichbar ist.
- **Ohne Home Assistant:** Weboberfläche unter `http://wortuhr.local` mit allen Schaltern und der Farbwahl. Wenn das WLAN fehlt, öffnet die Uhr den Hotspot `WortUhr-Setup` zum Einrichten (Captive Portal).
- **Anzeige** in 5-Minuten-Schritten, z. B. „IST ZWANZIG VOR ZWÖLF“. Zur vollen Stunde „IST PUNKT DREI“, um 0:00 „IST MITTERNACHT“.
- **Begrüßungen** (abschaltbar):
  - GUTEN MORGEN 5–10 Uhr
  - GUTEN MITTAG 11:30–13:30 Uhr
  - GUTE NACHT 22–0:30 Uhr
  - FROHES NEUES am 1. Januar
- **WLAN-Hinweis:** Das Wort **WLAN** leuchtet, solange die Verbindung fehlt. Gibt es noch keine Uhrzeit (z. B. direkt nach dem Einschalten ohne Netz), leuchtet nur WLAN.
- **Automatische Helligkeit** über den BH1750 hinter dem Lichtleiter. Sie wird lokal auf dem ESP berechnet, logarithmisch und geglättet. Einstellbar sind „Mindesthelligkeit“ und „Volle Helligkeit ab … lx“. Die Helligkeit des Licht-Entities ist dabei die Obergrenze.
- **Viertel-Schreibweise** umschaltbar: „VIERTEL NACH/VOR ZWEI“ oder „VIERTEL/DREIVIERTEL ZWEI“.
- **Effekte:** „Uhrzeit“ (Standard), „Uhrzeit Regenbogen“, dazu zwei LED-Tests.
- **BOOT-Taster** (IO0): kurz drücken schaltet die Anzeige an und aus.

## Einrichten und Flashen

1. `secrets.example.yaml` nach `secrets.yaml` kopieren und WLAN-Daten eintragen. Den Schlüssel `api_key` erzeugen. Er verschlüsselt auch die OTA-Updates:
   ```
   python -c "import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())"
   ```
2. Beim ersten Mal per USB-C flashen. Dafür beim Einstecken BOOT gedrückt halten, falls der ESP nicht erkannt wird.
   ```
   .venv\Scripts\esphome.exe run wortuhr.yaml
   ```
3. Danach geht jede Aktualisierung über WLAN (OTA).
4. Home Assistant findet die Uhr automatisch: *Einstellungen → Geräte & Dienste → ESPHome*. Dort den `api_key` angeben.

Die lokale Umgebung wurde mit `uv` erzeugt (Python 3.12, ESPHome in `.venv`, nicht eingecheckt):
```
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe esphome
```

## Bestückungsvarianten

- **2 LEDs je Kammer:** `leds_per_cell: "2"`, `num_leds: "292"` (4 × 72 + 4 Minuten-LEDs). Das ist die Voreinstellung.
- **1 LED je Kammer** (Lötbrücken JP geschlossen): `leds_per_cell: "1"`, `num_leds: "148"`.

## Hinweise zum Buchstabenraster

- Im Raster fehlen **ES** und **UHR**. Die Anzeige beginnt deshalb mit „IST“, das sich abschalten lässt.
- Zeile 8 lautet `Z E H N E U N E V I E R` (ZEHN, NEUN, VIER; das zweite E ist Füllbuchstabe).
- **Minutenpunkte:** Die Minuten zwischen den 5-Minuten-Schritten (Minute mod 5) zeigen 1–4 Punkte in den Ecken, im Uhrzeigersinn ab oben links. Beispiel 11:42 = IST ZWANZIG VOR ZWÖLF + 2 Punkte. Im Text-Sensor steht dann „… +2“.

## Versorgung

Die Uhr braucht ein USB-C-PD-Netzteil mit 15 V (ab 45 W). Ohne PD, zum Beispiel am PC, laufen ESP32 und Flashen, die LEDs bleiben aus (Sensor `USB-PD aktiv`, GPIO38). Die Firmware begrenzt den geschaetzten LED-Strom auf 5 A.
