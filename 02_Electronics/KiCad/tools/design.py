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
REV = "3"                 # Platinen-Revision: einzige Quelle fuer Schriftfeld und Bestueckungsdruck (SCH-010)
REV_DATE = "2026-11-10"   # Datum im Schriftfeld des Schaltplans
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
FIDUCIALS = [(4.0, 4.0, "F"), (230.0, 4.0, "F"), (4.0, 170.0, "F"),
             (4.0, 4.0, "B"), (230.0, 4.0, "B"), (230.0, 170.0, "B")]
# Minuten-LED (1..4 Minuten zwischen den 5-Minuten-Schritten): eine je Platine an der Aussenecke.
# Durch die Drehung der vier Platinen landet sie in allen vier Ecken der Uhr. In der Datenkette
# sitzt sie direkt nach Kammer MINUTE_AFTER (= Kammer (5,5), schon in der Ecke).
MINUTE_LED_POS = (230.0, 230.0)
MINUTE_AFTER = 5
CORNER_R = 3.0           # Radius der Aussenecke der Platine (Platz fuer die Minuten-LED)
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


SHEETS = {"Versorgung": "Versorgung.kicad_sch", "ESP32": "ESP32.kicad_sch", "LED_Feld": "LED_Feld.kicad_sch"}
VERSORGUNG = {"J1", "F1", "U3", "C28", "U6", "R20", "R21", "C20", "U7", "L1", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "R22", "R23", "U2", "C2", "C3", "C1"}
ESP32 = {"U1", "R24", "R25", "R3", "R4", "C4", "C5", "C9", "SW1", "SW2", "U4", "C6", "R5", "U5", "R6", "C7", "C8", "R7", "R8"}


def sheet_of(ref):
    if ref in VERSORGUNG:
        return "Versorgung"
    if ref in ESP32:
        return "ESP32"
    return "LED_Feld"      # LEDs mit ihren Abblock-Kondensatoren (SCH-006), Verbinder, Mechanik


def sheet_uuid(name):
    return uid("sheet/" + name)


# Bezugsdaten: (Wert, Footprint) -> (Hersteller-Teilenummer, DigiKey-Bestellnummer als Cut Tape).
# Nur eintragen, was ueber die DigiKey-API bestaetigt ist. Leere DigiKey-Nummer: dort nicht gefuehrt.
BEZUG = {
    ("100n", "C_0603_1608Metric"): ("C0603C104K5RACTU", "399-C0603C104K5RACTUCT-ND"),
    ("100n/25V", "C_0603_1608Metric"): ("C0603C104K5RACTU", "399-C0603C104K5RACTUCT-ND"),
    ("1u", "C_0603_1608Metric"): ("C0603C105K3RACTU", "399-C0603C105K3RACTUCT-ND"),
    ("1u/25V", "C_0603_1608Metric"): ("C0603C105K3RACTU", "399-C0603C105K3RACTUCT-ND"),
    ("1u/10V", "C_0603_1608Metric"): ("C0603C105K3RACTU", "399-C0603C105K3RACTUCT-ND"),
    ("10u", "C_0805_2012Metric"): ("TMK212BBJ106MG-T", "587-6025-1-ND"),
    ("22u/10V", "C_0805_2012Metric"): ("C0805C226M8PACTU", "399-C0805C226M8PACTUCT-ND"),
    ("22u/25V", "C_1206_3216Metric"): ("CC1206MKX5R8BB226", "311-3522-1-ND"),
    ("100u/10V", "CP_Elec_6.3x7.7"): ("UWT1A101MCL1GB", "493-2165-1-ND"),
    ("10k", "R_0603_1608Metric"): ("ERJ-3EKF1002V", "P10.0KHCT-ND"),
    ("33", "R_0603_1608Metric"): ("ERJ-3EKF33R0V", "P33.0HCT-ND"),
    ("1k", "R_0603_1608Metric"): ("ERJ-3EKF1001V", "P1.00KHCT-ND"),
    ("4k7", "R_0603_1608Metric"): ("ERJ-3EKF4701V", "P4.70KHCT-ND"),
    ("75k", "R_0603_1608Metric"): ("ERJ-3EKF7502V", "P75.0KHCT-ND"),
    ("10.2k", "R_0603_1608Metric"): ("ERJ-3EKF1022V", "P10.2KHCT-ND"),
    ("22", "R_0402_1005Metric"): ("ERJ-2RKF22R0X", "P22.0LCT-ND"),
    ("1k", "R_1206_3216Metric"): ("RC1206FR-071KL", "311-1.00KFRCT-ND"),
    ("RESET", "SW_SPST_TL3342"): ("TL3342F160QG/TR", "EG2531CT-ND"),
    ("BOOT", "SW_SPST_TL3342"): ("TL3342F160QG/TR", "EG2531CT-ND"),
    ("ESP32-S3-MINI-1-N8", "ESP32-S2-MINI-1"): ("ESP32-S3-MINI-1-N8", "5407-ESP32-S3-MINI-1-N8CT-ND"),
    ("SRP1265A-3R3M", "L_Bourns_SRP1245A"): ("SRP1265A-3R3M", "SRP1265A-3R3MCT-ND"),   # gleiche Pads wie SRP1245A
    ("1812L300/24SLER", "Fuse_1812_4532Metric"): ("1812L300/24SLER", "18-1812L300/24SLERCT-ND"),
    ("AP2112K-3.3", "SOT-23-5"): ("AP2112K-3.3TRG1", "AP2112K-3.3TRG1DICT-ND"),
    ("USBLC6-2SC6", "SOT-23-6"): ("USBLC6-2SC6", "497-5235-1-ND"),
    ("74AHCT1G125", "SOT-23-5"): ("SN74AHCT1G125DBVR", "296-4708-1-ND"),
    ("BH1750FVI", "WSOF6I_BH1750"): ("BH1750FVI-TR", "BH1750FVICT-ND"),
    # Bei DigiKey nicht gefuehrt: separat beschaffen
    ("USB-C", "USB_C_Receptacle_HRO_TYPE-C-31-M-12"): ("TYPE-C-31-M-12", ""),
    ("CH224K", "SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm"): ("CH224K", ""),
    ("SCT2360FPBR", "QFN-12_SCT2360"): ("SCT2360FPBR", ""),
}


def bezug(p):
    """Tragt MPN und DigiKey-Nummer als Symboleigenschaften ein, soweit bekannt."""
    mpn, dk = BEZUG.get((p.value, p.fp.split(":")[-1]), ("", ""))
    if mpn:
        p.extra["MPN"] = mpn
    if dk:
        p.extra["DigiKey"] = dk


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
        if c == MINUTE_AFTER:
            P.append(Part("D75", "LED:WS2812B", "SK6812RGBW", FP_LED,
                          {"1": "+5V", "2": "MIN_OUT", "3": "GND", "4": prev},
                          extra={"LED": "Minutenpunkt (Ecke)"}))
            P.append(Part("C175", "Device:C", "100n", FP_C0603, {"1": "GND", "2": "+5V"}))
            prev = "MIN_OUT"
    # --- Verbindungen / allgemein --------------------------------------------
    FP_BR = "WortUhr:EdgeBridge_5x2512"
    P.append(Part("J3", "Connector_Generic:Conn_01x05", "Bruecke_IN", FP_BR,
                  {"1": "GND", "2": "+5V", "3": "DIN", "4": "+5V", "5": "GND"},
                  extra={"Hinweis": "0R 2512 ueber die Kante zur Nachbarplatine (5x)"}))
    P.append(Part("J4", "Connector_Generic:Conn_01x05", "Bruecke_OUT", FP_BR,
                  {"1": "GND", "2": "+5V", "3": "DOUT", "4": "+5V", "5": "GND"},
                  extra={"Hinweis": "Gegenstueck zu Bruecke_IN der naechsten Platine"}))
    P.append(Part("C1", "Device:C_Polarized", "100u/10V", "Capacitor_SMD:CP_Elec_6.3x7.7",
                  {"1": "+5V", "2": "GND"}))
    for i in range(6):
        P.append(Part(f"H{i+1}", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_4.3mm_M4", {}))
    for i in range(6):   # Passermarken fuer die Bestueckung (JLCPCB Standard-PCBA), je 3 oben/unten
        P.append(Part(f"FID{i+1}", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}))
    # --- Master ---------------------------------------------------------------
    M = "Master"
    P.append(Part("J1", "Connector:USB_C_Receptacle_USB2.0_14P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                  {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
                   "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
                   "A5": "CC1", "B5": "CC2", "A6": "USB_D+", "B6": "USB_D+", "A7": "USB_D-", "B7": "USB_D-"}, M))
    P.append(Part("U3", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
                  {"1": "USB_D-", "6": "USB_D-", "3": "USB_D+", "4": "USB_D+", "2": "GND", "5": "+5V"}, M))
    P.append(Part("C28", "Device:C", "100n", FP_C0603, {"1": "+5V", "2": "GND"}, M, extra={"Hinweis": "ST USBLC6-2 Figure 17: C_BUS an Pin 5"}))
    # Espressif: Serienwiderstaende 22/33 Ohm in D+/D- nahe am Chip
    FP_R0402 = "Resistor_SMD:R_0402_1005Metric"
    P.append(Part("R24", "Device:R", "22", FP_R0402, {"1": "USB_D-", "2": "USB_D-_ESP"}, M))
    P.append(Part("R25", "Device:R", "22", FP_R0402, {"1": "USB_D+", "2": "USB_D+_ESP"}, M))
    P.append(Part("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
                  {"1": "+5V", "3": "+5V", "2": "GND", "5": "+3V3"}, M, nc=["4"]))
    P.append(Part("C2", "Device:C", "10u", FP_C0805, {"1": "+5V", "2": "GND"}, M))
    P.append(Part("C3", "Device:C", "10u", FP_C0805, {"1": "+3V3", "2": "GND"}, M))
    P.append(Part("C4", "Device:C", "100n", FP_C0603, {"1": "+3V3", "2": "GND"}, M))
    esp = {"1": "GND", "2": "GND", "3": "+3V3", "45": "EN", "4": "BOOT", "12": "LED_3V3",
           "5": "SDA", "6": "SCL", "34": "PD_GOOD", "23": "USB_D-_ESP", "24": "USB_D+_ESP"}
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
    # --- USB-C Power Delivery + Abwaertswandler 15 V -> 5 V / 6 A (ersetzt Hohlbuchse und Dioden) ---
    FP_L = "Inductor_SMD:L_Bourns_SRP1245A"
    FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
    P.append(Part("F1", "Device:Polyfuse", "1812L300/24SLER", "Fuse:Fuse_1812_4532Metric", {"1": "VBUS", "2": "+15V"}, M))
    P.append(Part("U6", "WortUhr:CH224K", "CH224K", "Package_SO:SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm",
                  {"1": "PD_VDD", "2": "PD_VDD", "3": "PD_VDD", "6": "CC2", "7": "CC1", "8": "PD_SENSE", "9": "GND", "10": "PD_GOOD", "11": "GND"},
                  M, nc=["4", "5"], extra={"Hinweis": "CFG1=0, CFG2=1, CFG3=1: fordert 15 V an"}))
    P.append(Part("R20", "Device:R", "1k", "Resistor_SMD:R_1206_3216Metric", {"1": "+15V", "2": "PD_VDD"}, M))
    P.append(Part("C20", "Device:C", "1u/25V", FP_C0603, {"1": "PD_VDD", "2": "GND"}, M))
    P.append(Part("R21", "Device:R", "10k", FP_R0603, {"1": "+15V", "2": "PD_SENSE"}, M))
    P.append(Part("U7", "WortUhr:SCT2360", "SCT2360FPBR", "WortUhr:QFN-12_SCT2360",
                  {"1": "+15V", "2": "GND", "4": "GND", "5": "+5V", "7": "BUCK_SW", "8": "BUCK_BST",
                   "9": "BUCK_VCC", "10": "GND", "11": "BUCK_FB"}, M, nc=["3", "6", "12"],
                  extra={"Hinweis": "FSEL=GND: 400 kHz; MODE offen: USM; EN offen: Start automatisch"}))
    P.append(Part("L1", "Device:L", "SRP1265A-3R3M", FP_L, {"1": "BUCK_SW", "2": "+5V"}, M))
    P.append(Part("C21", "Device:C", "22u/25V", FP_C1206, {"1": "+15V", "2": "GND"}, M))
    P.append(Part("C22", "Device:C", "100n/25V", FP_C0603, {"1": "+15V", "2": "GND"}, M))
    for i, ref in enumerate(("C23", "C24", "C25")):
        P.append(Part(ref, "Device:C", "22u/10V", FP_C0805, {"1": "+5V", "2": "GND"}, M))
    P.append(Part("C26", "Device:C", "100n/25V", FP_C0603, {"1": "BUCK_BST", "2": "BUCK_SW"}, M))
    P.append(Part("C27", "Device:C", "1u/10V", FP_C0603, {"1": "BUCK_VCC", "2": "GND"}, M))
    P.append(Part("R22", "Device:R", "75k", FP_R0603, {"1": "+5V", "2": "BUCK_FB"}, M))
    P.append(Part("R23", "Device:R", "10.2k", FP_R0603, {"1": "BUCK_FB", "2": "GND"}, M))
    P.append(Part("C9", "Device:C", "22u/10V", FP_C0805, {"1": "+3V3", "2": "GND"}, M))
    for p in P:
        bezug(p)
    return P


# Platzierung Master-Teile (lokal, Unterseite ausser U5), (x, y, rot, seite)
MASTER_PLACE = {
    "U1": (33.0, 224.0, 0, "B"),      # ESP32-S3: Antenne zum unteren Rand
    "C4": (23.3, 226.3, 90, "B"),     # 100n: Versorgung kommt aussen an, laeuft durch den C zum Pin 3
    "C9": (20.6, 226.3, 90, "B"),     # 22u nach Espressif-Referenz
    "U2": (51.0, 223.5, 0, "B"),      # LDO 3.3V
    "C2": (47.0, 223.5, 90, "B"),
    "C3": (55.0, 223.5, 90, "B"),
    "R3": (43.5, 223.0, 90, "B"),     # EN-Pullup direkt am EN-Pin
    "C5": (43.5, 227.0, 90, "B"),     # 1u am EN-Pin 45
    "R4": (22.5, 221.5, 0, "B"),      # BOOT-Pullup
    "SW1": (82.0, 217.0, 0, "B"),     # RESET
    "SW2": (5.4, 218.6, 0, "B"),      # BOOT
    "J1": (63.0, 230.6, 180, "B"),    # USB-C
    "U3": (60.4, 221.5, 180, "B"),    # nah an J1; D- oben, D+ unten: passt zur Lage am ESP32
    "C28": (60.9, 222.2, 0, "F"),     # C_BUS oben direkt ueber U3
    "R24": (36.0, 211.9, 180, "B"),     # USB-Serienwiderstaende nahe U1
    "R25": (36.0, 212.9, 180, "B"),
    "F1": (72.0, 230.5, 0, "B"),      # Eingangssicherung
    "U6": (71.5, 222.0, 0, "B"),      # PD-Controller
    "R20": (76.9, 224.0, 90, "B"),     # 1206: 137 mW bei 15 V
    "C20": (76.5, 220.0, 90, "B"),
    "R21": (79.0, 224.0, 90, "B"),
    "C21": (85.7, 224.0, 90, "B"),     # Figure 22: Eingangs-C ueber VIN (Pin 1) und PGND (Pin 2)
    "C22": (87.75, 224.0, 90, "B"),    # Figure 22: 100n direkt an Pin 1/2 (Hot-Loop)
    "U7": (90.5, 224.0, 0, "B"),      # Abwaertswandler, SW zur Spule
    "C26": (93.0, 226.7, 0, "B"),      # BST direkt zwischen Pin 8 und SW
    "C27": (92.03, 228.2, 0, "B"),     # VCC direkt unter Pin 9
    "R22": (85.9, 227.7, 0, "B"),      # Rueckfuehrung an der Pinreihe 9-12
    "R23": (88.9, 227.7, 0, "B"),
    "L1": (102.0, 224.0, 0, "B"),     # so nah wie moeglich an SW
    "C23": (111.3, 221.5, 0, "B"),     # Ausgangs-Cs direkt am Spulenanschluss
    "C24": (111.3, 224.0, 0, "B"),
    "C25": (111.3, 226.5, 0, "B"),
    "U4": (19.0, 218.5, 180, "B"),    # Pegelwandler: A zum ESP32, Y zu R5
    "C6": (19.0, 215.0, 0, "B"),
    "R5": (14.5, 219.0, 90, "B"),
    "U5": (SENSOR_POS[0], SENSOR_POS[1], 270, "F"),   # SDA/SCL zum ESP32 gedreht
    "C8": (3.5, 229.5, 0, "B"),
    "R6": (9.5, 225.5, 90, "B"),
    "C7": (3.0, 224.5, 90, "B"),
    "R7": (11.5, 225.5, 90, "B"),
    "R8": (13.5, 225.5, 90, "B"),
}
