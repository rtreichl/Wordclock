// WortUhr – Uhrzeit in Woerter umsetzen und auf die LED-Kette schreiben.
// Wird von wortuhr.yaml eingebunden (esphome: includes).
#pragma once
#include <array>
#include <cmath>
#include <string>
#include "esphome/core/color.h"
#include "esphome/core/time.h"
#include "esphome/components/light/addressable_light.h"
#include "wortuhr_layout.h"

namespace wortuhr {

static const int ROWS = 12, COLS = 12, CELLS = 144;

struct Word {
  uint8_t row, col, len;
  const char *text;
};

// Woerter im Raster (Zeile, Spalte, Laenge); Zeile/Spalte ab 0, oben links.
static const Word W_WLAN{0, 1, 4, "WLAN"}, W_GUTEN{0, 6, 5, "GUTEN"}, W_GUTE{0, 6, 4, "GUTE"};
static const Word W_FROHES{1, 0, 6, "FROHES"}, W_NEUES{1, 7, 5, "NEUES"};
static const Word W_MORGEN{2, 0, 6, "MORGEN"}, W_MITTAG{2, 6, 6, "MITTAG"};
static const Word W_IST{3, 0, 3, "IST"}, W_M_ZEHN{3, 4, 4, "ZEHN"}, W_M_FUENF{3, 8, 4, "FÜNF"};
static const Word W_DREI_Q{4, 0, 4, "DREI"}, W_VIERTEL{4, 5, 7, "VIERTEL"};
static const Word W_PUNKT{5, 0, 5, "PUNKT"}, W_ZWANZIG{5, 5, 7, "ZWANZIG"};
static const Word W_VOR{6, 0, 3, "VOR"}, W_NACH{6, 3, 4, "NACH"}, W_HALB{6, 8, 4, "HALB"};
static const Word W_MITTERNACHT{10, 0, 11, "MITTERNACHT"}, W_NACHT{10, 6, 5, "NACHT"};

// Stunden 1..12. Zeile 8: Z E H N E U N E V I E R (ZEHN, NEUN, VIER).
struct Hour {
  uint8_t row, col, len;
  const char *text;
};
static const Hour HOURS[13] = {
    {0, 0, 0, ""},        {9, 0, 4, "EINS"}, {9, 8, 4, "ZWEI"},   {8, 7, 4, "DREI"},  {7, 8, 4, "VIER"},
    {11, 0, 4, "FÜNF"},   {9, 3, 5, "SECHS"}, {8, 1, 6, "SIEBEN"}, {10, 7, 4, "ACHT"}, {7, 3, 4, "NEUN"},
    {7, 0, 4, "ZEHN"},    {11, 9, 3, "ELF"},  {11, 4, 5, "ZWÖLF"}};

struct Mask {
  std::array<bool, CELLS> on{};
  uint8_t minutes = 0;        // Minutenpunkte 0..4 (Minute mod 5)
  std::string text;
  void cell(int r, int c) { on[r * COLS + c] = true; }
  void add(const Word &w) {
    for (int i = 0; i < w.len; i++) cell(w.row, w.col + i);
    if (!text.empty()) text += ' ';
    text += w.text;
  }
  void hour(int h12) {
    const Hour &h = HOURS[h12];
    for (int i = 0; i < h.len; i++) cell(h.row, h.col + i);
    if (!text.empty()) text += ' ';
    text += h.text;
  }
};

struct Options {
  bool greetings = true;      // GUTEN MORGEN / GUTEN MITTAG / GUTE NACHT / FROHES NEUES
  bool viertel_ost = false;   // "VIERTEL ZWEI" / "DREIVIERTEL ZWEI" statt "VIERTEL NACH/VOR"
  bool show_ist = true;       // "IST" voranstellen
  bool show_punkt = true;     // "PUNKT" zur vollen Stunde
};

// Uhrzeit -> Woerter (5-Minuten-Schritte, abgerundet) + Minutenpunkte fuer die Minuten dazwischen
inline Mask compose(int hour24, int minute, int day, int month, const Options &o) {
  Mask m;
  int m5 = (minute / 5) * 5;
  int h = hour24;
  bool next = false;

  m.minutes = minute % 5;
  if (o.show_ist) m.add(W_IST);
  if (hour24 == 0 && m5 == 0) {
    m.add(W_MITTERNACHT);
  } else {
    switch (m5) {
      case 0: if (o.show_punkt) m.add(W_PUNKT); break;
      case 5: m.add(W_M_FUENF); m.add(W_NACH); break;
      case 10: m.add(W_M_ZEHN); m.add(W_NACH); break;
      case 15:
        if (o.viertel_ost) { m.add(W_VIERTEL); next = true; } else { m.add(W_VIERTEL); m.add(W_NACH); }
        break;
      case 20: m.add(W_ZWANZIG); m.add(W_NACH); break;
      case 25: m.add(W_M_FUENF); m.add(W_VOR); m.add(W_HALB); next = true; break;
      case 30: m.add(W_HALB); next = true; break;
      case 35: m.add(W_M_FUENF); m.add(W_NACH); m.add(W_HALB); next = true; break;
      case 40: m.add(W_ZWANZIG); m.add(W_VOR); next = true; break;
      case 45:
        if (o.viertel_ost) { m.add(W_DREI_Q); m.add(W_VIERTEL); } else { m.add(W_VIERTEL); m.add(W_VOR); }
        next = true;
        break;
      case 50: m.add(W_M_ZEHN); m.add(W_VOR); next = true; break;
      case 55: m.add(W_M_FUENF); m.add(W_VOR); next = true; break;
    }
    if (next) h++;
    int h12 = h % 12;
    if (h12 == 0) h12 = 12;
    m.hour(h12);
  }

  if (o.greetings) {
    int t = hour24 * 60 + minute;
    if (day == 1 && month == 1) { m.add(W_FROHES); m.add(W_NEUES); }
    else if (t >= 5 * 60 && t < 10 * 60) { m.add(W_GUTEN); m.add(W_MORGEN); }
    else if (t >= 11 * 60 + 30 && t < 13 * 60 + 30) { m.add(W_GUTEN); m.add(W_MITTAG); }
    else if (t >= 22 * 60 || t < 30) { m.add(W_GUTE); m.add(W_NACHT); }
  }
  if (m.minutes) m.text += " +" + std::to_string(m.minutes);
  return m;
}

// Anzeige ohne gueltige Uhrzeit (kein WLAN / noch keine NTP-Antwort)
inline Mask status_wlan() {
  Mask m;
  m.add(W_WLAN);
  return m;
}

// ---------------------------------------------------------------- Stromgrenze
// Wandler 6 A, Firmware begrenzt auf 5 A. Schaetzung: 16 mA je voll angesteuertem LED-Kanal.
constexpr float AMP_PER_CHANNEL = 0.016f;
constexpr float AMP_LIMIT = 5.0f;

// Geschaetzter Strom fuer `leds` LEDs mit der Kanalsumme `channels` (0..4: R + G + B + W, je 0..1).
inline float estimate_amp(float leds, float channels) { return leds * AMP_PER_CHANNEL * channels; }

// Faktor (0..1), mit dem die Helligkeit multipliziert werden muss, damit der Strom unter der Grenze bleibt.
inline float limit_scale(float leds, float channels) {
  float amp = estimate_amp(leds, channels);
  return amp > AMP_LIMIT ? AMP_LIMIT / amp : 1.0f;
}

// ---------------------------------------------------------------- Ausgabe mit Ueberblendung
struct Renderer {
  std::array<float, CELLS> level{};   // aktueller Helligkeitsanteil je Kammer (0..1)
  std::array<float, 4> dot{};         // Minutenpunkte
  uint32_t last_ms = 0;

  // it: LED-Kette, base: Farbe/Helligkeit des Light-Entities, factor: Umgebungslicht-Faktor (0..1)
  void draw(esphome::light::AddressableLight &it, const Mask &m, esphome::Color base, float factor,
            int leds_per_cell, float fade_s, bool rainbow, uint32_t now_ms) {
    float dt = last_ms ? (now_ms - last_ms) / 1000.0f : 1.0f;
    last_ms = now_ms;
    float step = fade_s > 0.01f ? dt / fade_s : 1.0f;
    // Stromgrenze. Im Regenbogen leuchten je LED bis zu zwei Kanaele voll.
    int lit = m.minutes;
    for (bool b : m.on) lit += b ? leds_per_cell : 0;
    float channels = rainbow ? 2.0f : (base.r + base.g + base.b + base.w) / 255.0f;
    factor *= limit_scale(lit, channels * factor);
    for (int r = 0; r < ROWS; r++) {
      for (int c = 0; c < COLS; c++) {
        int i = r * COLS + c;
        float target = m.on[i] ? 1.0f : 0.0f;
        if (level[i] < target) level[i] = std::min(target, level[i] + step);
        else if (level[i] > target) level[i] = std::max(target, level[i] - step);
        esphome::Color col = base;
        if (rainbow) {
          float hue = std::fmod((now_ms / 60000.0f) * 360.0f + (r + c) * 12.0f, 360.0f);
          col = hsv(hue);
        }
        float f = level[i] * factor;
        esphome::Color out(uint8_t(col.r * f), uint8_t(col.g * f), uint8_t(col.b * f), uint8_t(col.w * f));
        int base_idx = cell_led(CELL_INDEX[r][c], leds_per_cell);
        for (int k = 0; k < leds_per_cell; k++) {
          if (base_idx + k < it.size()) it[base_idx + k] = out;
        }
      }
    }
    for (int n = 0; n < 4; n++) {     // Minutenpunkte 1..4 im Uhrzeigersinn ab oben links
      float target = n < m.minutes ? 1.0f : 0.0f;
      if (dot[n] < target) dot[n] = std::min(target, dot[n] + step);
      else if (dot[n] > target) dot[n] = std::max(target, dot[n] - step);
      esphome::Color col = rainbow ? hsv(std::fmod((now_ms / 60000.0f) * 360.0f + n * 90.0f, 360.0f)) : base;
      float f = dot[n] * factor;
      int idx = minute_led(n, leds_per_cell);
      if (idx < it.size())
        it[idx] = esphome::Color(uint8_t(col.r * f), uint8_t(col.g * f), uint8_t(col.b * f), uint8_t(col.w * f));
    }
  }

  static esphome::Color hsv(float h) {
    float x = 1 - std::fabs(std::fmod(h / 60.0f, 2.0f) - 1);
    float r = 0, g = 0, b = 0;
    if (h < 60) { r = 1; g = x; } else if (h < 120) { r = x; g = 1; } else if (h < 180) { g = 1; b = x; }
    else if (h < 240) { g = x; b = 1; } else if (h < 300) { r = x; b = 1; } else { r = 1; b = x; }
    return esphome::Color(uint8_t(r * 255), uint8_t(g * 255), uint8_t(b * 255), 0);
  }
};

}  // namespace wortuhr
