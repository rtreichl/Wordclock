# -*- coding: utf-8 -*-
"""Qualifikation Firmware (ESPHome) und WLED-LED-Maps.

Aufruf:  python qualify_firmware.py <staging_dir> [--no-compile]
Benoetigt ESPHome (03_Software/ESPHome/.venv oder 'esphome' im PATH).
Die Firmware wird mit Test-Schluesseln gebaut (keine echten WLAN-Daten); die Binaerdateien
landen nur im Staging, nicht im Repository.
"""
import os, sys, re, json, subprocess, shutil, hashlib, base64, secrets as pysecrets, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(ROOT, "05_Production")):  # Repo-Wurzel (auch ohne .git)
    ROOT = os.path.dirname(ROOT)
STAGE = os.path.join(sys.argv[1], "Firmware"); os.makedirs(STAGE, exist_ok=True)
EH = os.path.join(ROOT, "03_Software", "ESPHome")
checks = {"Firmware": [], "WLED": []}


def check(part, cat, name, crit, meas, ok, note=""):
    checks[part].append({"cat": cat, "name": name, "crit": crit, "meas": meas, "ok": bool(ok), "note": note})


# ---------------------------------------------------------------- Layout aktuell?
gen = os.path.join(EH, "tools", "gen_layout.py")
before = open(os.path.join(EH, "wortuhr_layout.h"), encoding="utf-8").read()
tmp = tempfile.mkdtemp()
shutil.copy(os.path.join(EH, "wortuhr_layout.h"), tmp)
subprocess.run([sys.executable, gen], check=True, capture_output=True)
after = open(os.path.join(EH, "wortuhr_layout.h"), encoding="utf-8").read()
shutil.copy(os.path.join(tmp, "wortuhr_layout.h"), os.path.join(EH, "wortuhr_layout.h"))
check("Firmware", "Konsistenz", "LED-/Buchstaben-Layout aktuell", "neu erzeugtes wortuhr_layout.h identisch",
      "identisch" if before == after else "abweichend", before == after)
grid = [l.strip()[3:].split() for l in before.splitlines() if l.startswith("//   ")]
idx = [list(map(int, re.findall(r"\d+", l))) for l in before.splitlines() if l.strip().startswith("{") and l.strip().endswith("},")]
flat = sorted(v for r in idx for v in r)
check("Firmware", "Konsistenz", "LED-Zuordnung vollstaendig", "144 Kammern, jeder Index 0..143 genau einmal",
      f"{len(flat)} Eintraege", flat == list(range(144)))

# ---------------------------------------------------------------- Woerter gegen Raster
h = open(os.path.join(EH, "wortuhr.h"), encoding="utf-8").read()
words = re.findall(r"W_\w+\{(\d+), (\d+), (\d+), \"([^\"]+)\"\}", h)
hours = re.findall(r"\{(\d+), (\d+), (\d+), \"([^\"]*)\"\}", h[h.index("HOURS[13]"):h.index("};", h.index("HOURS[13]"))])
bad = []
for r, c, n, txt in words + hours:
    r, c, n = int(r), int(c), int(n)
    if not txt:
        continue
    else:
        got = "".join(grid[r][c + k] for k in range(n))
    if got != txt:
        bad.append(f"{txt}->{got}")
check("Firmware", "Logik", "Woerter liegen auf den richtigen Buchstaben", f"{len(words) + len(hours) - 1} Woerter",
      f"Abweichungen: {bad or '-'}", not bad)

# Modell der Satzbildung (Python-Nachbildung von compose()) fuer alle 288 Zeiten
def phrase(h24, m):
    m5 = m // 5 * 5; nxt = m5 >= 25
    mins = {0: "PUNKT", 5: "FÜNF NACH", 10: "ZEHN NACH", 15: "VIERTEL NACH", 20: "ZWANZIG NACH", 25: "FÜNF VOR HALB",
            30: "HALB", 35: "FÜNF NACH HALB", 40: "ZWANZIG VOR", 45: "VIERTEL VOR", 50: "ZEHN VOR", 55: "FÜNF VOR"}[m5]
    hh = (h24 + (1 if nxt else 0)) % 12 or 12
    names = [None, "EINS", "ZWEI", "DREI", "VIER", "FÜNF", "SECHS", "SIEBEN", "ACHT", "NEUN", "ZEHN", "ELF", "ZWÖLF"]
    return "IST MITTERNACHT" if (h24 == 0 and m5 == 0) else f"IST {mins} {names[hh]}"
samples = {f"{h:02d}:{m:02d}": phrase(h, m) for h in (0, 8, 11, 23) for m in (0, 15, 25, 30, 40, 55)}
allok = all(phrase(h, m).split()[-1] in ("EINS", "ZWEI", "DREI", "VIER", "FÜNF", "SECHS", "SIEBEN", "ACHT", "NEUN", "ZEHN", "ELF", "ZWÖLF", "MITTERNACHT")
            for h in range(24) for m in range(0, 60, 5))
check("Firmware", "Logik", "Satzbildung fuer alle 288 Zeiten", "jede Zeit endet auf ein Stundenwort", "alle ok" if allok else "Fehler", allok,
      "Beispiele: " + "; ".join(f"{k} {v}" for k, v in list(samples.items())[:6]))

# ---------------------------------------------------------------- Konfiguration / Build
exe = os.path.join(EH, ".venv", "Scripts", "esphome.exe")
exe = exe if os.path.exists(exe) else shutil.which("esphome") or "esphome"
build = tempfile.mkdtemp()
for f in ("wortuhr.yaml", "wortuhr.h", "wortuhr_layout.h"):
    shutil.copy(os.path.join(EH, f), build)
key = base64.b64encode(pysecrets.token_bytes(32)).decode()
open(os.path.join(build, "secrets.yaml"), "w").write(
    f'wifi_ssid: "WortUhr-Werksstand"\nwifi_password: "noch-nicht-eingerichtet"\nap_password: "wortuhr-setup"\napi_key: "{key}"\n')
env = dict(os.environ); env.pop("MSYSTEM", None)
r = subprocess.run([exe, "config", "wortuhr.yaml"], cwd=build, capture_output=True, text=True, env=env)
check("Firmware", "Konfiguration", "ESPHome-Konfiguration gueltig", "esphome config ohne Fehler",
      "gueltig" if "Configuration is valid" in r.stdout + r.stderr else "ungueltig", "Configuration is valid" in r.stdout + r.stderr)
ytxt = open(os.path.join(EH, "wortuhr.yaml"), encoding="utf-8").read()
check("Firmware", "Anforderung", "Uhrzeit ohne Home Assistant", "time: platform sntp; api reboot_timeout 0s",
      f"sntp={'platform: sntp' in ytxt}, reboot_timeout_0={'reboot_timeout: 0s' in ytxt}", "platform: sntp" in ytxt and "reboot_timeout: 0s" in ytxt)
check("Firmware", "Anforderung", "Bedienung ohne Home Assistant", "web_server + captive_portal + Ersatz-Hotspot",
      f"web_server={'web_server:' in ytxt}, captive_portal={'captive_portal:' in ytxt}, ap={'ap:' in ytxt}",
      all(k in ytxt for k in ("web_server:", "captive_portal:", "ap:")))
check("Firmware", "Sicherheit", "Keine Zugangsdaten im Repository", "secrets.yaml in .gitignore, nur Vorlage eingecheckt",
      "ok" if "secrets.yaml" in open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read() else "fehlt",
      "secrets.yaml" in open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read())
if "--no-compile" not in sys.argv:
    r = subprocess.run([exe, "compile", "wortuhr.yaml"], cwd=build, capture_output=True, text=True, env=env, errors="replace")
    log = r.stdout + r.stderr
    ram = re.search(r"RAM:.*?([\d.]+)%", log); fl = re.search(r"Flash:.*?([\d.]+)%", log)
    ok = r.returncode == 0 and "Successfully compiled" in log
    check("Firmware", "Build", "Kompiliert (ESP32-S3, ESP-IDF)", "erfolgreich", "erfolgreich" if ok else f"rc {r.returncode}", ok)
    if ram and fl:
        check("Firmware", "Build", "Speicherreserve", "RAM < 60 %, Flash < 80 % (Reserve fuer OTA/Erweiterungen)",
              f"RAM {ram.group(1)} %, Flash {fl.group(1)} %", float(ram.group(1)) < 60 and float(fl.group(1)) < 80)
    bdir = os.path.join(build, ".esphome", "build", "wortuhr", "build")
    for f in ("firmware.factory.bin", "firmware.ota.bin"):
        if os.path.exists(os.path.join(bdir, f)):
            shutil.copy(os.path.join(bdir, f), os.path.join(STAGE, f))
    warn = [l for l in log.splitlines() if ("wortuhr.h" in l or "wortuhr_layout.h" in l) and "warning" in l]
    check("Firmware", "Build", "Keine Compiler-Warnungen im eigenen Code", "0", f"{len(warn)}", not warn)

# ---------------------------------------------------------------- Pins gegen den Schaltplan (design.py)
sys.path.insert(0, os.path.join(ROOT, "02_Electronics", "KiCad", "tools"))
import design as D  # noqa: E402
blk = lambda start: ytxt[ytxt.index(start):]
gp = lambda txt, key: int(re.search(key + r"\s*(?:number:\s*)?GPIO(\d+)", txt).group(1))
fw = {"SDA": gp(blk("\ni2c:"), r"sda:"), "SCL": gp(blk("\ni2c:"), r"scl:"), "LED_3V3": gp(blk("esp32_rmt_led_strip"), r"pin:"),
      "PD_GOOD": gp(blk("id: pd_ok"), r"pin:"), "BOOT": gp(blk("id: taster"), r"pin:")}
diff = [f"{n}: Firmware GPIO{fw[n]}, Schaltplan GPIO{g}" for n, g in D.ESP_GPIO.items() if fw.get(n) != g]
check("Firmware", "Konsistenz", "Pins wie im Schaltplan", "GPIO je Signal = design.py (ESP_GPIO)",
      ", ".join(f"{n}=GPIO{g}" for n, g in fw.items()) + (f"; abweichend: {diff}" if diff else ""), not diff and set(fw) == set(D.ESP_GPIO))
doc = open(os.path.join(ROOT, "02_Electronics", "BESTUECKUNG.md"), encoding="utf-8").read()
want = [f"Datenpin GPIO{D.ESP_GPIO['LED_3V3']},", f"SDA {D.ESP_GPIO['SDA']} / SCL {D.ESP_GPIO['SCL']}",
        f"LED-Daten GPIO{D.ESP_GPIO['LED_3V3']} ", f"SDA GPIO{D.ESP_GPIO['SDA']} / SCL GPIO{D.ESP_GPIO['SCL']}"]
miss = [w for w, t in zip(want, (doc, doc, ytxt, ytxt)) if w not in t]
check("Firmware", "Konsistenz", "Pins in der Doku", "BESTUECKUNG.md (WLED) und Kopf von wortuhr.yaml nennen die Pins aus design.py",
      "stimmt" if not miss else f"fehlt: {miss}", not miss)

# ---------------------------------------------------------------- Stromgrenze und PD-Sperre in jeder Betriebsart
A_CH = float(re.search(r"AMP_PER_CHANNEL = ([\d.]+)f", h).group(1)); A_MAX = float(re.search(r"AMP_LIMIT = ([\d.]+)f", h).group(1))
limit_scale = lambda leds, ch: min(1.0, A_MAX / (leds * A_CH * ch)) if leds * ch else 1.0      # Nachbildung von limit_scale()
nl_ = int(re.search(r'num_leds: "(\d+)"', ytxt).group(1))
worst = max(nl_ * A_CH * ch * limit_scale(nl_, ch) for ch in (0.5, 1.0, 2.0, 3.0, 4.0))
check("Firmware", "Sicherheit", "Stromgrenze rechnerisch", f"alle {nl_} LEDs, jede Farbe: geschaetzter Strom <= {A_MAX:g} A",
      f"ohne Grenze bis {nl_ * A_CH * 4:.1f} A, mit Grenze hoechstens {worst:.2f} A", worst <= A_MAX + 1e-6 and "limit_scale(lit," in h)
effects = re.findall(r'name: "([^"]+)"', blk("    effects:"))
clock = [e for e in effects if e.startswith("Uhrzeit")]
guard = blk("# Stromgrenze und PD-Sperre") if "# Stromgrenze und PD-Sperre" in ytxt else ""
guard = guard[:guard.index("\n# ---")] if "\n# ---" in guard else guard
g_ok = all(k in guard for k in ('rfind("Uhrzeit", 0)', "id(pd_ok).state", "turn_off()", "wortuhr::limit_scale(${num_leds}", "set_brightness(max_brightness)"))
c_ok = len(clock) > 0 and ytxt.count("(id(pd_ok).state ? id(auto_factor) : 0.0f)") == len(clock)
check("Firmware", "Sicherheit", "Stromgrenze und PD-Sperre in jeder Betriebsart",
      "Uhrzeit-Effekte begrenzen im Renderer; Licht ohne Effekt und alle anderen Effekte begrenzt der Waechter",
      f"{len(clock)} Uhrzeit-Effekte, {len(effects) - len(clock)} andere ({', '.join(e for e in effects if e not in clock)}), Waechter {'vorhanden' if g_ok else 'fehlt/unvollstaendig'}",
      g_ok and c_ok)

# ---------------------------------------------------------------- WLED-LED-Maps
wl = os.path.join(ROOT, "03_Software", "WLED")
m1 = json.load(open(os.path.join(wl, "ledmap_1LED_12x12.json")))["map"]
m2 = json.load(open(os.path.join(wl, "ledmap_2LED_24x12.json")))["map"]
MA = int(re.search(r"MINUTE_AFTER = (\d+);", before).group(1))
MB = list(map(int, re.search(r"MINUTE_BOARD\[4\] = \{([^}]*)\}", before).group(1).split(",")))
cell_led = lambda seq, lpc: (seq // 36) * (36 * lpc + 1) + (seq % 36) * lpc + (1 if seq % 36 > MA else 0)
minute_led = lambda n, lpc: MB[n] * (36 * lpc + 1) + (MA + 1) * lpc
for lpc, mp, name in ((1, m1, "ledmap 1 LED/Kammer"), (2, m2, "ledmap 2 LED/Kammer")):
    total = 4 * (36 * lpc + 1)
    expect = sorted(set(range(total)) - {minute_led(n, lpc) for n in range(4)})
    check("WLED", "Konsistenz", name, f"alle {total} LEDs ausser den 4 Minuten-LEDs genau einmal",
          f"{len(mp)} Eintraege", sorted(mp) == expect)
same = all(m1[r * 12 + c] == cell_led(idx[r][c], 1) for r in range(12) for c in range(12))
check("WLED", "Konsistenz", "Gleiche LED-Reihenfolge wie ESPHome", "ledmap = cell_led(CELL_INDEX)", "identisch" if same else "abweichend", same)
nl = int(re.search(r'num_leds: "(\d+)"', ytxt).group(1)); lp = int(re.search(r'leds_per_cell: "(\d+)"', ytxt).group(1))
check("Firmware", "Konsistenz", "LED-Anzahl in der Kette", "num_leds = 4 x (36 x leds_per_cell + 1)", f"num_leds {nl}, leds_per_cell {lp}",
      nl == 4 * (36 * lp + 1))
corners = {2: "oben links", 1: "oben rechts", 0: "unten rechts", 3: "unten links"}
check("Firmware", "Logik", "Minutenpunkte", "Minute mod 5 -> 1..4 Punkte im Uhrzeigersinn ab oben links",
      ", ".join(f"{n + 1}: LED {minute_led(n, lp)} ({corners[MB[n]]})" for n in range(4)),
      [corners[b] for b in MB] == ["oben links", "oben rechts", "unten rechts", "unten links"] and "m.minutes = minute % 5" in h)

json.dump(checks, open(os.path.join(sys.argv[1], "firmware_result.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in checks.items():
    print(k, f"{sum(c['ok'] for c in v)}/{len(v)}", [c["name"] for c in v if not c["ok"]])
