// Automatisch erzeugt von 03_Software/ESPHome/tools/gen_layout.py - nicht von Hand aendern.
#pragma once
#include <cstdint>

namespace wortuhr {

// Buchstabenraster (Zeile 0 = oben, Spalte 0 = links)
//   P W L A N K G U T E N X
//   F R O H E S R N E U E S
//   M O R G E N M I T T A G
//   I S T P Z E H N F Ü N F
//   D R E I W V I E R T E L
//   P U N K T Z W A N Z I G
//   V O R N A C H L H A L B
//   Z E H N E U N E V I E R
//   Q S I E B E N D R E I U
//   E I N S E C H S Z W E I
//   M I T T E R N A C H T R
//   F Ü N F Z W Ö L F E L F

// Physischer Kammer-Index (0..143) in der Datenkette fuer [Zeile][Spalte].
// LED-Nummer = Index * LEDS_PER_CELL + 0..LEDS_PER_CELL-1
static const uint8_t CELL_INDEX[12][12] = {
  { 77,  76,  75,  74,  73,  72,  70,  71,  54,  53,  42,  41},
  { 78,  79,  80,  81,  82,  83,  69,  68,  55,  52,  43,  40},
  { 89,  88,  87,  86,  85,  84,  66,  67,  56,  51,  44,  39},
  { 90,  91,  92,  93,  94,  95,  65,  64,  57,  50,  45,  38},
  {107, 104, 103, 100,  99,  96,  62,  63,  58,  49,  46,  37},
  {106, 105, 102, 101,  98,  97,  61,  60,  59,  48,  47,  36},
  {108, 119, 120, 131, 132, 133,  25,  26,  29,  30,  33,  34},
  {109, 118, 121, 130, 135, 134,  24,  27,  28,  31,  32,  35},
  {110, 117, 122, 129, 136, 137,  23,  22,  21,  20,  19,  18},
  {111, 116, 123, 128, 139, 138,  12,  13,  14,  15,  16,  17},
  {112, 115, 124, 127, 140, 141,  11,  10,   9,   8,   7,   6},
  {113, 114, 125, 126, 143, 142,   0,   1,   2,   3,   4,   5},
};

}  // namespace wortuhr
