# -*- coding: utf-8 -*-
"""
WortUhr LED-Board – gemeinsame Definition fuer Schaltplan- und PCB-Generator.

Eine Platine (6x6 Kammern, 2 LED-Plaetze je Kammer) wird 4x bestellt und in
0/90/180/270 Grad unter die vier Gitterteile geschraubt. Die Master-Variante
traegt zusaetzlich ESP32-S3, USB-C, Hohlbuchse, LDO, Pegelwandler und BH1750.

Koordinaten "lokal" (mm): Ursprung = Mittelpunkt der Uhr, x nach rechts,
y nach unten; die Platine liegt in der Master-Orientierung (Gitterteil Q4,
unten rechts) im Bereich x,y = 0.5 ... 234.5.
"""
import uuid

PROJECT = "WortUhr"
ROOT_UUID = "71044415-29e6-47b3-b7ec-feffb4cadb55"

# ---- Raster -----------------------------------------------------------------
PITCH = 38.4607          # Mittel aus 38.5177 (x) und 38.4037 (y) -> 90°-symmetrisch
C0 = 19.23               # Abstand erste Kammermitte zur Schnittkante
BOARD_MIN, BOARD_MAX = 0.5, 234.5
LED_OFF = 7.5            # LED A/B jeweils +-7.5 mm neben Kammermitte


def cell_center(k, j):
    return (C0 + k * PITCH, C0 + j * PITCH)


def wall(i):
    """Mitte der Wand zwischen Kammer i und i+1 (lokal)."""
    return PITCH * (i + 1)


# Datenkette: Start links unten (0,5) -> Ende (5,1); Ein-/Ausgang liegen so,
# dass sie bei 90°-Drehung der Nachbarplatine gegenueberliegen.
PATH = []
for j, d in ((5, +1), (4, -1), (3, +1), (2, -1)):
    ks = range(6) if d > 0 else range(5, -1, -1)
    PATH += [((k, j), d) for k in ks]
PATH += [((0, 1), +1), ((0, 0), +1), ((1, 0), +1), ((1, 1), +1), ((2, 1), +1), ((2, 0), +1),
         ((3, 0), +1), ((3, 1), +1), ((4, 1), +1), ((4, 0), +1), ((5, 0), +1), ((5, 1), +1)]
assert len(PATH) == 36 and len({c for c, _ in PATH}) == 36

CONN_POS = wall(4)       # 192.29: J_IN bei y=CONN_POS am linken Rand, J_OUT bei x=CONN_POS oben
SENSOR_POS = (6.0, 231.0)  # Lichtsensor unter dem Lichtleiter (Rahmen unten, nahe Mitte)
MOUNT_HOLES = [(wall(0), wall(0)), (wall(4), wall(0)), (wall(0), wall(4)), (wall(4), wall(4)),
               (wall(2), wall(4)), (wall(4), wall(2))]   # H5/H6 fuer die Rueckrahmen-Leisten


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "wortuhr/" + name))


# ---- Bauteile ----------------------------------------------------------------
# lib_id, value, footprint, {pin: net}, variante
FP_LED = "LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_JP = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"


class Part:
    def __init__(self, ref, lib_id, value, fp, pins, variant="alle", nc=(), extra=None):
        self.ref, self.lib_id, self.value, self.fp = ref, lib_id, value, fp
        self.pins, self.variant, self.nc = pins, variant, list(nc)
        self.extra = extra or {}
        self.uuid = uid("sym/" + ref)


def build_parts():
    P = []
    # --- LED-Feld -------------------------------------------------------------
    prev = "DIN"
    for c, ((k, j), d) in enumerate(PATH):
        a_out = f"C{c+1:02d}_A_OUT"
        b_out = "DOUT" if c == 35 else f"C{c+1:02d}_B_OUT"
        nA, nB = 2 * c + 1, 2 * c + 2
        P.append(Part(f"D{nA}", "LED:WS2812B", "SK6812RGBW", FP_LED,
                      {"1": "+5V", "2": a_out, "3": "GND", "4": prev},
                      extra={"Kammer": f"{k},{j}", "LED": "A (immer bestuecken)"}))
        P.append(Part(f"D{nB}", "LED:WS2812B", "SK6812RGBW", FP_LED,
                      {"1": "+5V", "2": b_out, "3": "GND", "4": a_out},
                      extra={"Kammer": f"{k},{j}", "LED": "B (optional, sonst JP schliessen)"}))
        P.append(Part(f"C{100+nA}", "Device:C", "100n", FP_C0603, {"1": "GND", "2": "+5V"}))
        P.append(Part(f"C{100+nB}", "Device:C", "100n", FP_C0603, {"1": "GND", "2": "+5V"},
                      extra={"Hinweis": "nur mit LED B"}))
        P.append(Part(f"JP{c+1}", "Jumper:SolderJumper_2_Open", "Bruecke LED B", FP_JP,
                      {"1": a_out, "2": b_out},
                      extra={"Hinweis": "schliessen wenn LED B nicht bestueckt"}))
        prev = b_out
    # --- Verbindungen / allgemein --------------------------------------------
    FP_BR = "WortUhr:EdgeBridge_5x2512"
    P.append(Part("J3", "Connector_Generic:Conn_01x05", "Bruecke_IN", FP_BR,
                  {"1": "GND", "2": "+5V", "3": "DIN", "4": "+5V", "5": "GND"},
                  extra={"Hinweis": "0R 2512 ueber die Kante zur Nachbarplatine (5x)"}))
    P.append(Part("J4", "Connector_Generic:Conn_01x05", "Bruecke_OUT", FP_BR,
                  {"1": "GND", "2": "+5V", "3": "DOUT", "4": "+5V", "5": "GND"},
                  extra={"Hinweis": "Gegenstueck zu Bruecke_IN der naechsten Platine"}))
    P.append(Part("C1", "Device:C_Polarized", "470u/6.3V", "Capacitor_SMD:CP_Elec_6.3x7.7",
                  {"1": "+5V", "2": "GND"}))
    for i in range(6):
        P.append(Part(f"H{i+1}", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}))
    # --- Master ---------------------------------------------------------------
    M = "Master"
    P.append(Part("J1", "Connector:USB_C_Receptacle_USB2.0_14P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                  {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
                   "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
                   "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN"}, M))
    P.append(Part("R1", "Device:R", "5k1", FP_R0603, {"1": "CC1", "2": "GND"}, M))
    P.append(Part("R2", "Device:R", "5k1", FP_R0603, {"1": "CC2", "2": "GND"}, M))
    P.append(Part("U3", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
                  {"1": "USB_DN", "6": "USB_DN", "3": "USB_DP", "4": "USB_DP", "2": "GND", "5": "VBUS"}, M))
    P.append(Part("D73", "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA", {"1": "+5V", "2": "VBUS"}, M))
    P.append(Part("J2", "Connector:Barrel_Jack_Switch", "5V DC 5.5/2.1", "Connector_BarrelJack:BarrelJack_CUI_PJ-036AH-SMT_Horizontal",
                  {"1": "VDC", "2": "GND"}, M, nc=["3"]))
    P.append(Part("D74", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC", {"1": "+5V", "2": "VDC"}, M))
    P.append(Part("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
                  {"1": "+5V", "3": "+5V", "2": "GND", "5": "+3V3"}, M, nc=["4"]))
    P.append(Part("C2", "Device:C", "10u", FP_C0805, {"1": "+5V", "2": "GND"}, M))
    P.append(Part("C3", "Device:C", "10u", FP_C0805, {"1": "+3V3", "2": "GND"}, M))
    P.append(Part("C4", "Device:C", "100n", FP_C0603, {"1": "+3V3", "2": "GND"}, M))
    esp = {"1": "GND", "2": "GND", "3": "+3V3", "45": "EN", "4": "BOOT", "20": "LED_3V3",
           "21": "SDA", "22": "SCL", "23": "USB_DN", "24": "USB_DP"}
    for n in list(range(42, 44)) + list(range(46, 66)):
        esp[str(n)] = "GND"
    used = set(esp)
    nc = [str(n) for n in range(1, 66) if str(n) not in used]
    P.append(Part("U1", "RF_Module:ESP32-S3-MINI-1", "ESP32-S3-MINI-1-N8", "RF_Module:ESP32-S2-MINI-1", esp, M, nc=nc))
    P.append(Part("R3", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "EN"}, M))
    P.append(Part("C5", "Device:C", "1u", FP_C0603, {"1": "EN", "2": "GND"}, M))
    P.append(Part("SW1", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "EN", "2": "GND"}, M))
    P.append(Part("R4", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "BOOT"}, M))
    P.append(Part("SW2", "Switch:SW_Push", "BOOT", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "BOOT", "2": "GND"}, M))
    P.append(Part("U4", "74xGxx:74AHCT1G125", "74AHCT1G125", "Package_TO_SOT_SMD:SOT-23-5",
                  {"1": "GND", "2": "LED_3V3", "3": "GND", "4": "LED_5V", "5": "+5V"}, M))
    P.append(Part("C6", "Device:C", "100n", FP_C0603, {"1": "+5V", "2": "GND"}, M))
    P.append(Part("R5", "Device:R", "33", FP_R0603, {"1": "LED_5V", "2": "DIN"}, M))
    P.append(Part("U5", "WortUhr:BH1750FVI", "BH1750FVI", "WortUhr:WSOF6I_BH1750",
                  {"1": "+3V3", "2": "GND", "3": "GND", "4": "SDA", "5": "DVI", "6": "SCL"}, M))
    P.append(Part("R6", "Device:R", "1k", FP_R0603, {"1": "+3V3", "2": "DVI"}, M))
    P.append(Part("C7", "Device:C", "1u", FP_C0603, {"1": "DVI", "2": "GND"}, M))
    P.append(Part("C8", "Device:C", "100n", FP_C0603, {"1": "+3V3", "2": "GND"}, M))
    P.append(Part("R7", "Device:R", "4k7", FP_R0603, {"1": "+3V3", "2": "SDA"}, M))
    P.append(Part("R8", "Device:R", "4k7", FP_R0603, {"1": "+3V3", "2": "SCL"}, M))
    return P


# Platzierung Master-Teile (lokal, Unterseite ausser U5), (x, y, rot, seite)
MASTER_PLACE = {
    "U1": (33.0, 224.0, 0, "B"),      # ESP32-S3: Antenne zum unteren Rand
    "C4": (44.5, 219.0, 90, "B"),
    "U2": (51.0, 223.5, 0, "B"),      # LDO 3.3V
    "C2": (47.0, 223.5, 90, "B"),
    "C3": (55.0, 223.5, 90, "B"),
    "R3": (22.5, 224.0, 0, "B"),      # EN-Pullup
    "C5": (22.5, 226.5, 0, "B"),
    "R4": (22.5, 221.5, 0, "B"),      # BOOT-Pullup
    "SW1": (78.0, 219.0, 0, "B"),     # RESET
    "SW2": (5.4, 218.6, 0, "B"),      # BOOT
    "J1": (63.0, 230.6, 180, "B"),    # USB-C
    "U3": (63.0, 219.5, 0, "B"),
    "R1": (57.0, 223.0, 90, "B"),
    "R2": (69.0, 223.0, 90, "B"),
    "D73": (72.0, 230.0, 0, "B"),     # SS34 USB
    "J2": (100.0, 224.0, 180, "B"),   # Hohlbuchse 5.5/2.1
    "D74": (114.0, 219.0, 0, "B"),    # SS54 Hohlbuchse
    "U4": (19.0, 218.5, 0, "B"),      # Pegelwandler 3.3 -> 5V
    "C6": (19.0, 215.0, 0, "B"),
    "R5": (14.5, 219.0, 90, "B"),
    "U5": (SENSOR_POS[0], SENSOR_POS[1], 90, "F"),
    "C8": (3.5, 225.5, 90, "B"),
    "R6": (6.5, 225.5, 90, "B"),
    "C7": (9.5, 225.5, 90, "B"),
    "R7": (3.5, 231.5, 90, "B"),
    "R8": (8.0, 231.5, 90, "B"),
}
