# -*- coding: utf-8 -*-
"""Erzeugt WortUhr.kicad_sch (+ Projekt-Symbolbibliothek) aus design.py."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import design as D

KI = r"P:/Program Files/KiCad/10.0/share/kicad/symbols/"
PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BH1750_SYM = '''(symbol "BH1750FVI" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
 (property "Reference" "U" (at 0 10.16 0) (effects (font (size 1.27 1.27))))
 (property "Value" "BH1750FVI" (at 0 -12.7 0) (effects (font (size 1.27 1.27))))
 (property "Footprint" "WortUhr:WSOF6I_BH1750" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
 (property "Datasheet" "https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
 (property "Description" "Umgebungslichtsensor I2C, WSOF6I" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
 (symbol "BH1750FVI_0_1" (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background))))
 (symbol "BH1750FVI_1_1"
  (pin power_in line (at -10.16 5.08 0) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
  (pin input line (at -10.16 -5.08 0) (length 2.54) (name "ADDR" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
  (pin power_in line (at 0 -10.16 90) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
  (pin bidirectional line (at 10.16 2.54 180) (length 2.54) (name "SDA" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
  (pin input line (at -10.16 0 0) (length 2.54) (name "DVI" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
  (pin input line (at 10.16 -2.54 180) (length 2.54) (name "SCL" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
 )
 (embedded_fonts no)
)'''


CH224_SYM = '(symbol "CH224K" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n (property "Reference" "U" (at 0 12.70 0) (effects (font (size 1.27 1.27))))\n (property "Value" "CH224K" (at 0 -12.70 0) (effects (font (size 1.27 1.27))))\n (property "Footprint" "Package_SO:SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n (property "Datasheet" "https://www.wch-ic.com/products/CH224.html" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n (property "Description" "USB-PD Sink-Controller" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n (symbol "CH224K_0_1" (rectangle (start -10.16 10.16) (end 10.16 -10.16) (stroke (width 0.254) (type default)) (fill (type background))))\n (symbol "CH224K_1_1"\n  (pin passive line (at -12.70 7.62 0) (length 2.54) (name "VDD" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 5.08 0) (length 2.54) (name "VBUS" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 2.54 0) (length 2.54) (name "CFG1" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 0.00 0) (length 2.54) (name "CFG2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 -2.54 0) (length 2.54) (name "CFG3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))\n  (pin power_in line (at -12.70 -5.08 0) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27)))))\n  (pin bidirectional line (at 12.70 7.62 180) (length 2.54) (name "CC1" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))\n  (pin bidirectional line (at 12.70 5.08 180) (length 2.54) (name "CC2" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))\n  (pin passive line (at 12.70 2.54 180) (length 2.54) (name "DP" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))\n  (pin passive line (at 12.70 0.00 180) (length 2.54) (name "DM" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))\n  (pin open_collector line (at 12.70 -2.54 180) (length 2.54) (name "PG" (effects (font (size 1.27 1.27)))) (number "10" (effects (font (size 1.27 1.27)))))\n )\n (embedded_fonts no)\n)'
SCT2360_SYM = '(symbol "SCT2360" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n (property "Reference" "U" (at 0 13.97 0) (effects (font (size 1.27 1.27))))\n (property "Value" "SCT2360FPBR" (at 0 -13.97 0) (effects (font (size 1.27 1.27))))\n (property "Footprint" "WortUhr:QFN-12_SCT2360" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n (property "Datasheet" "https://www.silicontent.com/" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n (property "Description" "Abwaertswandler 4-28 V, 6 A" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n (symbol "SCT2360_0_1" (rectangle (start -10.16 11.43) (end 10.16 -11.43) (stroke (width 0.254) (type default)) (fill (type background))))\n (symbol "SCT2360_1_1"\n  (pin power_in line (at -12.70 8.89 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 6.35 0) (length 2.54) (name "EN" (effects (font (size 1.27 1.27)))) (number "12" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 3.81 0) (length 2.54) (name "FSEL" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))\n  (pin input line (at -12.70 1.27 0) (length 2.54) (name "MODE" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))\n  (pin power_out line (at -12.70 -1.27 0) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))\n  (pin power_in line (at -12.70 -3.81 0) (length 2.54) (name "AGND" (effects (font (size 1.27 1.27)))) (number "10" (effects (font (size 1.27 1.27)))))\n  (pin power_in line (at -12.70 -6.35 0) (length 2.54) (name "PGND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))\n  (pin passive line (at 12.70 8.89 180) (length 2.54) (name "BST" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))\n  (pin power_out line (at 12.70 6.35 180) (length 2.54) (name "SW" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))\n  (pin power_in line (at 12.70 3.81 180) (length 2.54) (name "VOUT" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))\n  (pin input line (at 12.70 1.27 180) (length 2.54) (name "FB" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27)))))\n  (pin open_collector line (at 12.70 -1.27 180) (length 2.54) (name "PG" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))\n )\n (embedded_fonts no)\n)'


def sexpr_block(txt, start):
    """Return the balanced (...) block starting at index start (string aware)."""
    d, i, ins = 0, start, False
    while i < len(txt):
        ch = txt[i]
        if ins:
            if ch == '\\':
                i += 2; continue
            if ch == '"':
                ins = False
        else:
            if ch == '"':
                ins = True
            elif ch == '(':
                d += 1
            elif ch == ')':
                d -= 1
                if d == 0:
                    return txt[start:i + 1]
        i += 1
    raise ValueError("unbalanced")


_libcache = {}


def lib_text(lib):
    if lib not in _libcache:
        if lib == "WortUhr":
            _libcache[lib] = "(kicad_symbol_lib " + BH1750_SYM + CH224_SYM + SCT2360_SYM + ")"
        else:
            _libcache[lib] = open(KI + lib + ".kicad_sym", encoding="utf-8").read()
    return _libcache[lib]


def raw_symbol(lib, name):
    t = lib_text(lib)
    m = re.search(r'\(symbol "%s"\s' % re.escape(name), t)
    if not m:
        raise KeyError(lib + ":" + name)
    return sexpr_block(t, m.start())


def prop(block, key):
    m = re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % key, block)
    return m.group(1) if m else None


def flat_symbol(lib_id):
    lib, name = lib_id.split(":")
    b = raw_symbol(lib, name)
    m = re.search(r'\(extends "([^"]+)"\)', b)
    if m:
        parent = m.group(1)
        pb = raw_symbol(lib, parent)
        pb = pb.replace('(symbol "%s"' % parent, '(symbol "%s"' % name, 1)
        pb = pb.replace('(symbol "%s_' % parent, '(symbol "%s_' % name)
        for key in ("Value", "Footprint", "Datasheet", "Description", "ki_keywords", "ki_fp_filters"):
            v = prop(b, key)
            if v is not None:
                pb = re.sub(r'(\(property "%s" ")((?:[^"\\]|\\.)*)(")' % key,
                            lambda mm: mm.group(1) + v.replace('\\', '\\\\') + mm.group(3), pb, count=1)
        b = pb
    b = b.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)
    return b


def symbol_pins(lib_id):
    b = flat_symbol(lib_id)
    pins = []
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)', b):
        blk = sexpr_block(b, m.start())
        num = re.search(r'\(number "([^"]*)"', blk).group(1)
        pins.append((num, float(m.group(1)), float(m.group(2)), int(m.group(3))))
    return pins


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


POWER = {"+5V": "power:+5V", "GND": "power:GND", "+3V3": "power:+3V3", "VBUS": "power:VBUS", "+15V": "power:+15V"}
DIRS = {0: (2.54, 0), 90: (0, -2.54), 180: (-2.54, 0), 270: (0, 2.54)}
PWR_COUNT = [0]


def snap(v):
    return round(v / 1.27) * 1.27


class Sch:
    """Ein Blatt. Symbole werden erst gesetzt, danach verbindet connect() die Pins."""

    def __init__(self, name):
        self.name, self.items, self.libs, self.n = name, [], {}, 0
        self.tips, self.segs = {}, []          # (x,y) -> netz

    def uid(self, tag):
        self.n += 1
        return D.uid("sch/%s/%s/%d" % (self.name, tag, self.n))

    def text(self, s, x, y, size=2.54):
        self.items.append('(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)) (justify left bottom)) (uuid "%s"))'
                          % (q(s), fmt(x), fmt(y), fmt(size), fmt(size), self.uid("txt")))

    def symbol(self, lib_id, ref, value, fp, x, y, uuid_, fields=None, pinnets=None, nc=(), rot=0, hide_ref=False):
        self.libs.setdefault(lib_id, flat_symbol(lib_id))
        pins = symbol_pins(lib_id)
        no_bom = ref.startswith(("#", "H", "FID", "JP")) or ref in ("J3", "J4")
        props = [("Reference", ref, (x, y - 8.89), hide_ref), ("Value", value, (x, y + 8.89), hide_ref), ("Footprint", fp, (x, y), True), ("Datasheet", "", (x, y), True)]
        props += [(k, v, (x, y), True) for k, v in (fields or {}).items()]
        s = ['(symbol (lib_id %s) (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board %s) (dnp no) (uuid "%s")'
             % (q(lib_id), fmt(x), fmt(y), rot, "no" if no_bom else "yes", "no" if ref.startswith("#") else "yes", uuid_)]
        for k, v, (px, py), hide in props:
            s.append('(property %s %s (at %s %s 0) (effects (font (size 1.27 1.27))%s))' % (q(k), q(v), fmt(px), fmt(py), " (hide yes)" if hide else ""))
        for num in dict.fromkeys(p[0] for p in pins):
            s.append('(pin %s (uuid "%s"))' % (q(num), D.uid("pin/%s/%s" % (ref, num))))
        s.append('(instances (project %s (path "/%s/%s" (reference %s) (unit 1))))' % (q(D.PROJECT), D.ROOT_UUID, D.sheet_uuid(self.name), q(ref)))
        s.append(")")
        self.items.append(" ".join(s))
        out = []
        for num, px, py, ang in pins:
            X, Y = round(x + px, 3), round(y - py, 3)
            if pinnets and num in pinnets:
                out.append((X, Y, (ang + 180) % 360, pinnets[num]))
            elif num in nc:
                self.items.append('(no_connect (at %s %s) (uuid "%s"))' % (fmt(X), fmt(Y), self.uid("nc")))
        return out

    def power(self, net, X, Y, o):
        dx, dy = DIRS[o]
        ex, ey = round(X + dx, 3), round(Y + dy, 3)
        self.wire((X, Y), (ex, ey))
        PWR_COUNT[0] += 1
        gnd = net == "GND"
        rot = {270: 0, 0: 90, 90: 180, 180: 270}[o] if gnd else {90: 0, 180: 90, 270: 180, 0: 270}[o]
        self.symbol(POWER[net], "#PWR%04d" % PWR_COUNT[0], net, "", ex, ey, D.uid("pwr/%d" % PWR_COUNT[0]), hide_ref=True, rot=rot)

    def wire(self, a, b):
        if a != b:
            self.items.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), self.uid("w")))

    def label(self, net, X, Y, o, glob):
        just = "left bottom" if o in (0, 90) else "right bottom"
        if glob:
            self.items.append('(global_label %s (shape bidirectional) (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s")'
                              ' (property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes))))' % (q(net), fmt(X), fmt(Y), o, just, self.uid("gl"), fmt(X), fmt(Y)))
        else:
            self.items.append('(label %s (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))' % (q(net), fmt(X), fmt(Y), o, just, self.uid("lb")))

    # ---- Leitungen mit Kollisionspruefung
    def _on(self, p, a, b):
        return min(a[0], b[0]) - 1e-6 <= p[0] <= max(a[0], b[0]) + 1e-6 and min(a[1], b[1]) - 1e-6 <= p[1] <= max(a[1], b[1]) + 1e-6 and (abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6)

    def seg_free(self, a, b, net, pending):
        for p, n in self.tips.items():
            if n != net and self._on(p, a, b):
                return False
        for c, d, n in self.segs + pending:
            if n == net and {a, b} & {c, d}:
                continue
            for p in (c, d):
                if self._on(p, a, b):
                    return False
            for p in (a, b):
                if self._on(p, c, d):
                    return False
        return True

    def try_wire(self, net, pins):
        stubs, pending = [], []
        for X, Y, o, _ in pins:
            dx, dy = DIRS[o]
            e = (round(X + dx, 3), round(Y + dy, 3))
            if not self.seg_free((X, Y), e, net, pending):
                return False
            pending.append(((X, Y), e, net)); stubs.append(e)
        stubs = sorted(dict.fromkeys(stubs))
        for a, b in zip(stubs, stubs[1:]):
            for c in ((b[0], a[1]), (a[0], b[1])):
                tmp, ok = list(pending), True
                for u, v in ((a, c), (c, b)):
                    if u == v:
                        continue
                    if not self.seg_free(u, v, net, tmp):
                        ok = False; break
                    tmp.append((u, v, net))
                if ok:
                    pending = tmp
                    break
            else:
                return False
        for u, v, n in pending:
            self.wire(u, v)
        self.segs += pending
        self.named = stubs[0]
        return True

    def connect(self, by_net, cross):
        for net, pins in by_net.items():
            for X, Y, o, _ in pins:
                self.tips[(X, Y)] = net
        for net, pins in sorted(by_net.items(), key=lambda kv: len(kv[1])):
            pins = list({(p[0], p[1]): p for p in pins}.values())
            if net in POWER:
                for X, Y, o, _ in pins:
                    self.power(net, X, Y, o)
            elif net in cross:
                for X, Y, o, _ in pins:
                    self.label(net, X, Y, o, True)
            else:
                xs = [p[0] for p in pins]; ys = [p[1] for p in pins]
                if len(pins) <= 4 and max(xs) - min(xs) < 80 and max(ys) - min(ys) < 60 and self.try_wire(net, pins):
                    self.label(net, self.named[0], self.named[1], 0, False)
                else:
                    for X, Y, o, _ in pins:
                        self.label(net, X, Y, o, False)

    def write(self, path, title, page):
        out = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")', '(uuid "%s")' % D.uid("file/" + self.name), '(paper "A2")',
               '(title_block (title %s) (date "2026-11-08") (rev "3") (comment 1 "Generiert mit tools/gen_sch.py"))' % q(title), '(lib_symbols']
        out += list(self.libs.values()) + [')'] + self.items + ['(embedded_fonts no)', ')']
        open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


def write_root(path):
    items = []
    for i, (name, f) in enumerate(D.SHEETS.items()):
        x = 40 + i * 70
        u = D.sheet_uuid(name)
        items.append('(sheet (at %d 60) (size 55 30) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0)) (uuid "%s")'
                     ' (property "Sheetname" %s (at %d 59 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'
                     ' (property "Sheetfile" %s (at %d 91 0) (effects (font (size 1.27 1.27)) (justify left top)))'
                     ' (instances (project %s (path "/%s" (page "%d")))))' % (x, u, q(name), x, q(f), x, q(D.PROJECT), D.ROOT_UUID, i + 2))
    out = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")', '(uuid "%s")' % D.ROOT_UUID, '(paper "A3")',
           '(title_block (title "WortUhr LED-Board (4x identisch, Master/Slave)") (date "2026-11-08") (rev "3") (comment 1 "Versorgung: USB-C PD 15 V, Wandler 5 V / 6 A") (comment 2 "Generiert mit tools/gen_sch.py"))', '(lib_symbols)']
    out += items + ['(sheet_instances (path "/" (page "1")))', '(embedded_fonts no)', ')']
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


POS = {
    "Versorgung": {"J1": (40, 90), "F1": (90, 55), "U3": (90, 100), "C28": (115, 125), "U6": (140, 60), "R20": (115, 45), "C20": (115, 75), "R21": (115, 90), "C21": (185, 50), "C22": (200, 50),
                   "U7": (240, 80), "L1": (290, 70), "C26": (285, 95), "C27": (205, 100), "C23": (315, 60), "C24": (330, 60), "C25": (345, 60), "C1": (360, 60), "R22": (320, 100), "R23": (320, 125),
                   "U2": (240, 170), "C2": (205, 170), "C3": (285, 170)},
    "ESP32": {"U1": (130, 110), "C4": (55, 60), "C9": (70, 60), "R3": (55, 100), "C5": (55, 135), "SW1": (80, 135), "R4": (55, 170), "SW2": (80, 170),
              "U4": (230, 60), "C6": (265, 60), "R5": (265, 85), "U5": (230, 150), "R6": (195, 150), "C7": (195, 180), "C8": (265, 130), "R7": (285, 130), "R8": (300, 130), "R24": (195, 85), "R25": (195, 110)},
}


def main():
    parts = {p.ref: p for p in D.build_parts()}
    S = {n: Sch(n) for n in D.SHEETS}
    pins = {n: {} for n in D.SHEETS}
    netsheets = {}

    def put(p, x, y):
        sh = D.sheet_of(p.ref)
        for X, Y, o, net in S[sh].symbol(p.lib_id, p.ref, p.value, p.fp, snap(x), snap(y), p.uuid, dict(p.extra, Variante=p.variant), p.pins, p.nc):
            pins[sh].setdefault(net, []).append((X, Y, o, net))
            netsheets.setdefault(net, set()).add(sh)

    S["LED_Feld"].text("LED-Feld: Kammern in Reihenfolge der Datenkette (x,y = Spalte,Zeile der Master-Platine)", 25.4, 17.78, 3.0)
    S["Abblockung"].text("Abblock-Kondensatoren 100 nF je LED, Nummer = LED + 100", 25.4, 17.78, 3.0)
    for c, ((k, j), d) in enumerate(D.PATH):
        col, row = c % 6, c // 6
        bx, by = 25.4 + col * 66.04, 30.48 + row * 40.64
        S["LED_Feld"].text("Kammer %d,%d  (#%d)" % (k, j, c + 1), bx, by, 1.8)
        nA, nB = 2 * c + 1, 2 * c + 2
        put(parts.pop(f"D{nA}"), bx + 12.7, by + 17.78); put(parts.pop(f"D{nB}"), bx + 43.18, by + 17.78); put(parts.pop(f"JP{c+1}"), bx + 27.94, by + 33.02)
    for i, n in enumerate(list(range(1, 73)) + [75]):
        put(parts.pop(f"C{100+n}"), 30 + (i % 12) * 30, 40 + (i // 12) * 35)
    put(parts.pop("D75"), 450, 60)
    extra = {"J3": (450, 100), "J4": (450, 130)}
    for i in range(6):
        extra[f"H{i+1}"] = (430 + i * 12.7, 170); extra[f"FID{i+1}"] = (430 + i * 12.7, 190)
    for ref, xy in extra.items():
        put(parts.pop(ref), *xy)
    for sh, pos in POS.items():
        for ref, xy in pos.items():
            put(parts.pop(ref), *xy)
    assert not parts, parts.keys()
    for i, net in enumerate(["+5V", "GND", "VBUS", "+15V"]):
        x, y = snap(40 + i * 25), snap(200)
        u = D.uid("flag/" + net)
        for X, Y, o, n in S["Versorgung"].symbol("power:PWR_FLAG", "#FLG0%d" % (i + 1), "PWR_FLAG", "", x, y, u, pinnets={"1": net}, hide_ref=True):
            pins["Versorgung"].setdefault(net, []).append((X, Y, o, net)); netsheets.setdefault(net, set()).add("Versorgung")
    cross = {n for n, sh in netsheets.items() if len(sh) > 1}
    for n, s_ in S.items():
        s_.connect(pins[n], cross)
    titles = {"Versorgung": "Versorgung: USB-C PD, Wandler, LDO", "ESP32": "ESP32-S3, Pegelwandler, Lichtsensor", "LED_Feld": "LED-Feld und Verbinder", "Abblockung": "Abblock-Kondensatoren"}
    for i, (n, f) in enumerate(D.SHEETS.items()):
        S[n].write(os.path.join(PRJ, f), titles[n], i + 2)
    write_root(os.path.join(PRJ, "WortUhr.kicad_sch"))
    open(os.path.join(PRJ, "WortUhr.kicad_sym"), "w", encoding="utf-8").write(
        '(kicad_symbol_lib (version 20241209) (generator "wortuhr_gen") (generator_version "1.0")\n' + BH1750_SYM + "\n" + CH224_SYM + "\n" + SCT2360_SYM + "\n)\n")
    print("schematic written", {n: len(s_.items) for n, s_ in S.items()})


if __name__ == "__main__":
    main()
