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
            _libcache[lib] = "(kicad_symbol_lib " + BH1750_SYM + ")"
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


class Sch:
    def __init__(self):
        self.items = []
        self.libs = {}
        self.n = 0

    def uid(self, tag):
        self.n += 1
        return D.uid("sch/%s/%d" % (tag, self.n))

    def lib(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = flat_symbol(lib_id)

    def label(self, net, x, y, pin_angle):
        ang = (pin_angle + 180) % 360
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append('(label %s (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))'
                          % (q(net), fmt(x), fmt(y), ang, just, self.uid("lbl")))

    def noconn(self, x, y):
        self.items.append('(no_connect (at %s %s) (uuid "%s"))' % (fmt(x), fmt(y), self.uid("nc")))

    def text(self, s, x, y, size=2.54):
        self.items.append('(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)) (justify left bottom)) (uuid "%s"))'
                          % (q(s), fmt(x), fmt(y), fmt(size), fmt(size), self.uid("txt")))

    def symbol(self, lib_id, ref, value, fp, x, y, uuid_, fields=None, pinnets=None, nc=(), hide_ref=False):
        self.lib(lib_id)
        pins = symbol_pins(lib_id)
        props = [("Reference", ref, (x, y - 10.16), hide_ref), ("Value", value, (x, y + 10.16), False),
                 ("Footprint", fp, (x, y), True), ("Datasheet", "", (x, y), True)]
        for k, v in (fields or {}).items():
            props.append((k, v, (x, y), True))
        s = ['(symbol (lib_id %s) (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp no) (uuid "%s")'
             % (q(lib_id), fmt(x), fmt(y), "no" if ref.startswith("#") or ref.startswith("H") or ref.startswith("FID") or ref.startswith("JP") or ref in ("J3", "J4") else "yes", uuid_)]
        for k, v, (px, py), hide in props:
            s.append('(property %s %s (at %s %s 0) (effects (font (size 1.27 1.27))%s))'
                     % (q(k), q(v), fmt(px), fmt(py), " (hide yes)" if hide else ""))
        seen = set()
        for num, *_ in pins:
            if num in seen:
                continue
            seen.add(num)
            s.append('(pin %s (uuid "%s"))' % (q(num), D.uid("pin/%s/%s" % (ref, num))))
        s.append('(instances (project %s (path "/%s" (reference %s) (unit 1))))' % (q(D.PROJECT), D.ROOT_UUID, q(ref)))
        s.append(")")
        self.items.append(" ".join(s))
        placed = set()
        for num, px, py, ang in pins:
            X, Y = x + px, y - py
            key = (round(X, 3), round(Y, 3))
            if pinnets and num in pinnets:
                if key not in placed:
                    self.label(pinnets[num], X, Y, ang)
                    placed.add(key)
            elif num in nc:
                if key not in placed:
                    self.noconn(X, Y)
                    placed.add(key)

    def write(self, path):
        out = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")',
               '(uuid "%s")' % D.ROOT_UUID, '(paper "A1")',
               '(title_block (title "WortUhr LED-Board (4x identisch, Variante Master/Slave)") (date "2026-11-07") (rev "2")'
               ' (comment 1 "36 Kammern je Platine, 2 LED-Plaetze je Kammer (SK6812 RGBW, Pinbelegung wie WS2812B)")'
               ' (comment 2 "Master: ESP32-S3, USB-C + 5V-Hohlbuchse, BH1750 unter Lichtleiter; Slave: nur LED-Feld")'
               ' (comment 3 "Generiert mit tools/gen_sch.py"))',
               '(lib_symbols']
        out += list(self.libs.values())
        out.append(')')
        out += self.items
        out.append('(sheet_instances (path "/" (page "1")))')
        out.append('(embedded_fonts no)')
        out.append(')')
        open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


def snap(v):
    return round(v / 1.27) * 1.27


def main():
    parts = {p.ref: p for p in D.build_parts()}
    S = Sch()
    # LED-Feld: Kammerbloecke
    S.text("LED-Feld: Kammern in Reihenfolge der Datenkette (Kammer x,y = Spalte,Zeile, Master-Orientierung)", 25.4, 17.78, 3.0)
    for c, ((k, j), d) in enumerate(D.PATH):
        col, row = c % 6, c // 6
        bx, by = 25.4 + col * 66.04, 30.48 + row * 55.88
        S.text("Kammer %d,%d  (#%d)" % (k, j, c + 1), bx, by, 1.8)
        nA, nB = 2 * c + 1, 2 * c + 2
        for ref, x, y in ((f"D{nA}", bx + 12.7, by + 17.78), (f"D{nB}", bx + 43.18, by + 17.78),
                          (f"C{100+nA}", bx + 12.7, by + 40.64), (f"C{100+nB}", bx + 43.18, by + 40.64),
                          (f"JP{c+1}", bx + 27.94, by + 33.02)):
            p = parts.pop(ref)
            S.symbol(p.lib_id, p.ref, p.value, p.fp, x, y, p.uuid, dict(p.extra, Variante=p.variant), p.pins, p.nc)
    # restliche Teile
    S.text("Verbinder / alle Varianten", 444.5, 25.4, 3.0)
    S.text("D75: Minutenpunkt in der Aussenecke (Kette nach Kammer 5,5)", 574.04, 38.1, 1.8)
    S.text("Master-Variante (nur auf einer Platine bestuecken)", 444.5, 132.08, 3.0)
    S.text("Hinweise: SK6812RGBW-Pinbelegung vor Bestellung mit Datenblatt pruefen. JPx schliessen, wenn LED B einer Kammer nicht bestueckt wird.", 25.4, 375.92, 2.0)
    pos = {"J3": (457.2, 50.8), "J4": (500.38, 50.8), "C1": (543.56, 50.8), "D75": (589.28, 50.8), "C175": (619.76, 50.8),
           "H1": (457.2, 96.52), "H2": (482.6, 96.52), "H3": (508.0, 96.52), "H4": (533.4, 96.52), "H5": (558.8, 96.52), "H6": (584.2, 96.52),
           "FID1": (609.6, 96.52), "FID2": (622.3, 96.52), "FID3": (635.0, 96.52), "FID4": (647.7, 96.52), "FID5": (660.4, 96.52), "FID6": (673.1, 96.52),
           "J1": (467.36, 172.72), "R1": (510.54, 165.1), "R2": (523.24, 165.1), "U3": (558.8, 167.64),
           "D73": (558.8, 200.66), "J2": (464.82, 223.52), "D74": (505.46, 220.98),
           "U2": (558.8, 238.76), "C2": (530.86, 241.3), "C3": (586.74, 241.3), "C4": (599.44, 241.3),
           "U1": (660.4, 200.66), "R3": (613.41, 160.02), "C5": (626.11, 160.02), "SW1": (618.49, 137.16),
           "R4": (613.41, 279.4), "SW2": (618.49, 299.72),
           "U4": (469.9, 292.1), "C6": (500.38, 292.1), "R5": (523.24, 287.02),
           "U5": (558.8, 299.72), "R6": (590.55, 279.4), "C7": (581.66, 322.58), "C8": (530.86, 322.58),
           "R7": (713.74, 254.0), "R8": (726.44, 254.0)}
    for ref, (x, y) in pos.items():
        p = parts.pop(ref)
        S.symbol(p.lib_id, p.ref, p.value, p.fp, snap(x), snap(y), p.uuid, dict(p.extra, Variante=p.variant), p.pins, p.nc)
    assert not parts, parts.keys()
    # PWR_FLAGs
    for i, (net, x, y) in enumerate([("+5V", 457.2, 345.44), ("GND", 482.6, 345.44),
                                     ("VBUS", 533.4, 345.44), ("VDC", 558.8, 345.44)]):
        S.symbol("power:PWR_FLAG", "#FLG0%d" % (i + 1), "PWR_FLAG", "", x, y, D.uid("flag/" + net),
                 pinnets={"1": net}, hide_ref=True)
    S.write(os.path.join(PRJ, "WortUhr.kicad_sch"))
    # Projekt-Symbolbibliothek
    open(os.path.join(PRJ, "WortUhr.kicad_sym"), "w", encoding="utf-8").write(
        '(kicad_symbol_lib (version 20241209) (generator "wortuhr_gen") (generator_version "1.0")\n' + BH1750_SYM + "\n)\n")
    print("schematic written; libs:", len(S.libs), "items:", len(S.items))


if __name__ == "__main__":
    main()
