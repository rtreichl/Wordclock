# -*- coding: utf-8 -*-
"""Erzeugt den Schaltplan (WortUhr.kicad_sch + Unterblaetter + Projekt-Symbolbibliothek) aus design.py.

Darstellung nach den Regeln SCH-001 bis SCH-010 in ROUTING_GUIDE.md:
Funktionsbloecke mit Rahmen und Auslegungsnotiz, Leitungen innerhalb eines Blocks, Labels nur
zwischen Bloecken und Blaettern, benannte Versorgungssymbole, keine ueberlappenden Texte.

Jedes Blatt wird von Hand angeordnet (sheet_*). Der Generator prueft danach selbst:
- Netzliste der Zeichnung = Netze aus design.py (jeder Pin, jedes Netz, kein Kurzschluss)
- Lesbarkeit: keine ueberlappenden Texte, keine Leitung durch Text oder fremde Symbole

Aufruf:  python gen_sch.py            schreibt die Dateien
         python gen_sch.py --check    vergleicht den Generator-Stand mit den Dateien im Projekt
Alle Koordinaten in den sheet_*-Funktionen sind Rastereinheiten (1 E = 2,54 mm, halbe Schritte erlaubt).
"""
import os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import design as D

_KI = [os.environ.get("KICAD10_SYMBOL_DIR"), os.environ.get("KICAD_SYMBOL_DIR"),
       r"P:/Program Files/KiCad/10.0/share/kicad/symbols", "/usr/share/kicad/symbols"]
KI = next(p for p in _KI if p and os.path.isdir(p)).rstrip("/\\") + "/"
PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = 2.54


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace("\n", "\\n") + '"'


def tw(s, size=1.27):
    """Geschaetzte Textbreite in mm (KiCad-Standardschrift)."""
    return len(s) * size * 0.95


# ---------------------------------------------------------------- Projekt-Symbole
def mk_symbol(name, desc, fp, ds, w, h, pins):
    """Rechteck-Symbol. pins: (Nummer, Name, Typ, Seite L/R/T/B, Position auf der Seite in mm)."""
    f = '(effects (font (size 1.27 1.27)))'
    s = ['(symbol "%s" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)' % name,
         ' (property "Reference" "U" (at 0 %s 0) %s)' % (fmt(h + 2.54), f),
         ' (property "Value" "%s" (at 0 %s 0) %s)' % (name, fmt(-h - 2.54), f),
         ' (property "Footprint" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))' % fp,
         ' (property "Datasheet" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))' % ds,
         ' (property "Description" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))' % desc,
         ' (symbol "%s_0_1" (rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) (fill (type background))))'
         % (name, fmt(-w), fmt(h), fmt(w), fmt(-h)),
         ' (symbol "%s_1_1"' % name]
    for num, pname, typ, side, pos in pins:
        x, y, a = {"L": (-w - 2.54, pos, 0), "R": (w + 2.54, pos, 180), "B": (pos, -h - 2.54, 90), "T": (pos, h + 2.54, 270)}[side]
        s.append('  (pin %s line (at %s %s %d) (length 2.54) (name "%s" %s) (number "%s" %s))' % (typ, fmt(x), fmt(y), a, pname, f, num, f))
    return "\n".join(s + [' )', ' (embedded_fonts no)', ')'])


BH1750_SYM = mk_symbol("BH1750FVI", "Umgebungslichtsensor I2C, WSOF6I", "WortUhr:WSOF6I_BH1750",
                       "https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf", 7.62, 7.62,
                       [("1", "VCC", "power_in", "L", 5.08), ("5", "DVI", "input", "L", 0), ("2", "ADDR", "input", "L", -5.08),
                        ("4", "SDA", "bidirectional", "R", 2.54), ("6", "SCL", "input", "R", -2.54), ("3", "GND", "power_in", "B", 0)])
CH224_SYM = mk_symbol("CH224K", "USB-PD Sink-Controller", "Package_SO:SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm",
                      "https://www.wch-ic.com/products/CH224.html", 10.16, 10.16,
                      [("8", "VBUS", "input", "L", 7.62), ("1", "VDD", "passive", "L", 2.54), ("2", "CFG2", "input", "L", 0),
                       ("3", "CFG3", "input", "L", -2.54), ("9", "CFG1", "input", "L", -7.62),
                       ("7", "CC1", "bidirectional", "R", 7.62), ("6", "CC2", "bidirectional", "R", 5.08), ("4", "DP", "passive", "R", 0),
                       ("5", "DM", "passive", "R", -2.54), ("10", "PG", "open_collector", "R", -7.62), ("11", "GND", "power_in", "B", 0)])
SCT2360_SYM = mk_symbol("SCT2360", "Abwaertswandler 4-28 V, 6 A", "WortUhr:QFN-12_SCT2360", "https://www.silicontent.com/", 10.16, 15.24,
                        [("1", "VIN", "power_in", "L", 12.7), ("12", "EN", "input", "L", 7.62), ("4", "FSEL", "input", "L", 2.54),
                         ("6", "MODE", "input", "L", 0), ("9", "VCC", "power_out", "L", -5.08),
                         ("8", "BST", "passive", "R", 12.7), ("7", "SW", "power_out", "R", 5.08), ("5", "VOUT", "power_in", "R", 0),
                         ("11", "FB", "input", "R", -5.08), ("3", "PG", "open_collector", "R", -10.16),
                         ("10", "AGND", "power_in", "B", -2.54), ("2", "PGND", "power_in", "B", 2.54)])
PROJECT_SYMS = [BH1750_SYM, CH224_SYM, SCT2360_SYM]


# ---------------------------------------------------------------- Bibliothekssymbole lesen
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


_libcache, _flat, _pins, _body = {}, {}, {}, {}


def lib_text(lib):
    if lib not in _libcache:
        if lib == "WortUhr":
            _libcache[lib] = "(kicad_symbol_lib " + "".join(PROJECT_SYMS) + ")"
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
    if lib_id in _flat:
        return _flat[lib_id]
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
    _flat[lib_id] = b.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)
    return _flat[lib_id]


def symbol_pins(lib_id):
    if lib_id not in _pins:
        b = flat_symbol(lib_id)
        pins = []
        for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)', b):
            num = re.search(r'\(number "([^"]*)"', sexpr_block(b, m.start())).group(1)
            pins.append((num, float(m.group(1)), float(m.group(2))))
        _pins[lib_id] = pins
    return _pins[lib_id]


def pin_names(lib_id):
    """{Pinnummer: Pinname} eines Bibliothekssymbols."""
    b = flat_symbol(lib_id)
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at', b):
        blk = sexpr_block(b, m.start())
        out[re.search(r'\(number "([^"]*)"', blk).group(1)] = re.search(r'\(name "([^"]*)"', blk).group(1)
    return out


def symbol_body(lib_id):
    """Umriss des Symbolkoerpers (x1, y1, x2, y2) in Bibliothekskoordinaten: groesstes Rechteck, sonst Pin-Huelle."""
    if lib_id not in _body:
        b = flat_symbol(lib_id)
        best = None
        for m in re.finditer(r'\(rectangle\s*\(start ([\-\d.]+) ([\-\d.]+)\)\s*\(end ([\-\d.]+) ([\-\d.]+)\)', b):
            x1, y1, x2, y2 = map(float, m.groups())
            r = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            if best is None or (r[2] - r[0]) * (r[3] - r[1]) > (best[2] - best[0]) * (best[3] - best[1]):
                best = r
        pins = symbol_pins(lib_id)
        if (best is None or (best[2] - best[0]) * (best[3] - best[1]) < 30) and pins:
            xs = [p[1] for p in pins]; ys = [p[2] for p in pins]
            sh = lambda lo, hi: (lo + 2.54, hi - 2.54) if hi - lo > 6 else (lo - 1.5, hi + 1.5)
            (x1, x2), (y1, y2) = sh(min(xs), max(xs)), sh(min(ys), max(ys))
            best = (x1, y1, x2, y2)
        _body[lib_id] = best or (-2.0, -2.0, 2.0, 2.0)
    return _body[lib_id]


def rotate(px, py, rot):
    """Bibliothekspunkt (y nach oben) -> Blattversatz (y nach unten), Drehung gegen den Uhrzeigersinn."""
    return {0: (px, -py), 90: (-py, -px), 180: (-px, py), 270: (py, px)}[rot]


POWER = {"+5V": "power:+5V", "GND": "power:GND", "+3V3": "power:+3V3", "VBUS": "power:VBUS", "+15V": "power:+15V"}
TWO_PIN = {"Device:C": 3.0, "Device:C_Polarized": 3.2, "Device:R": 2.2, "Device:L": 2.6, "Device:Polyfuse": 2.6}
PWR_COUNT = [0]
r3 = lambda v: round(v, 3)


class Sch:
    """Ein Blatt. Koordinaten der oeffentlichen Methoden in Rastereinheiten relativ zum Blattursprung (ox, oy)."""

    def __init__(self, name, title, paper, parts, cross, ox=0, oy=0):
        self.name, self.title, self.paper, self.parts, self.cross = name, title, paper, parts, cross
        self.ox, self.oy = ox, oy
        self.items, self.libs, self.n = [], {}, 0
        self.segs, self.pinpts, self.named, self.ncs = [], {}, {}, set()
        self.texts, self.bodies, self.p = [], [], {}

    def P(self, x, y):
        return (r3((x + self.ox) * G), r3((y + self.oy) * G))

    def uid(self, tag):
        self.n += 1
        return D.uid("sch/%s/%s/%d" % (self.name, tag, self.n))

    # ---- Texte und Grafik
    def _tbox(self, s, x, y, just, owner, size=1.27):
        w = tw(s, size); h = size / 2
        x1 = {"left": x, "right": x - w, "center": x - w / 2}[just]
        self.texts.append((x1, y - h, x1 + w, y + h, owner, s))

    def note(self, s, x, y, size=1.27, bold=False, top=False):
        X, Y = self.P(x, y)
        self.items.append('(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) (justify left %s)) (uuid "%s"))'
                          % (q(s), fmt(X), fmt(Y), fmt(size), fmt(size), " (bold yes)" if bold else "", "top" if top else "bottom", self.uid("txt")))
        lines = s.split("\n"); lh = size * 1.62
        for i, ln in enumerate(lines):
            y1 = Y + i * lh if top else Y - size - (len(lines) - 1 - i) * lh
            self.texts.append((X, y1, X + tw(ln, size), y1 + size, "note", ln))

    def box(self, x1, y1, x2, y2, title):
        (X1, Y1), (X2, Y2) = self.P(x1, y1), self.P(x2, y2)
        self.items.append('(rectangle (start %s %s) (end %s %s) (stroke (width 0.15) (type dash)) (fill (type none)) (uuid "%s"))'
                          % (fmt(X1), fmt(Y1), fmt(X2), fmt(Y2), self.uid("box")))
        self.note(title, x1 + 0.5, y1 + 1.3, 1.8, bold=True)

    # ---- Symbole
    def _field(self, key, val, x, y, just, rot, hide, owner):
        ang = 90 if rot in (90, 270) else 0
        j = just
        if rot in (90, 180) and just != "center":      # KiCad spiegelt die Ausrichtung mit dem Symbol
            j = "right" if just == "left" else "left"
        js = "" if j == "center" else " (justify %s)" % j
        if not hide:
            self._tbox(val, x, y, just, owner)
        return '(property %s %s (at %s %s %d) (effects (font (size 1.27 1.27))%s%s))' % (q(key), q(val), fmt(x), fmt(y), ang, js, " (hide yes)" if hide else "")

    def _symbol(self, lib_id, ref, value, fp, X, Y, rot, uuid_, fields, pinnets, nc, ref_at, val_at, show_ref, show_val):
        self.libs.setdefault(lib_id, flat_symbol(lib_id))
        pins = symbol_pins(lib_id)
        bx1, by1, bx2, by2 = symbol_body(lib_id)
        cs = [rotate(px, py, rot) for px, py in ((bx1, by1), (bx2, by2))]
        body = (X + min(c[0] for c in cs), Y + min(c[1] for c in cs), X + max(c[0] for c in cs), Y + max(c[1] for c in cs))
        if not ref.startswith("#"):
            self.bodies.append(body + (ref,))
        if lib_id in TWO_PIN and rot in (0, 180):
            dr, dv = (TWO_PIN[lib_id], -1.25, "left"), (TWO_PIN[lib_id], 1.25, "left")
        elif lib_id in TWO_PIN:
            o = 2.4 if lib_id == "Device:R" else 3.2
            dr, dv = (0, -o, "center"), (0, o, "center")
        else:
            dr, dv = (body[0] - X, body[1] - Y - 1.6, "left"), (body[0] - X, body[3] - Y + 1.6, "left")
        dr, dv = ref_at or dr, val_at or dv
        no_bom = ref.startswith(("#", "H", "FID", "JP")) or ref in ("J3", "J4")
        s = ['(symbol (lib_id %s) (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board %s) (dnp no) (uuid "%s")'
             % (q(lib_id), fmt(X), fmt(Y), rot, "no" if no_bom else "yes", "no" if ref.startswith("#") else "yes", uuid_)]
        s.append(self._field("Reference", ref, X + dr[0], Y + dr[1], dr[2], rot, not show_ref, ref))
        s.append(self._field("Value", value, X + dv[0], Y + dv[1], dv[2], rot, not show_val, ref))
        for k, v in [("Footprint", fp), ("Datasheet", "")] + list((fields or {}).items()):
            s.append(self._field(k, v, X, Y, "center", 0, True, ref))
        for num in dict.fromkeys(p[0] for p in pins):
            s.append('(pin %s (uuid "%s"))' % (q(num), D.uid("pin/%s/%s" % (ref, num))))
        s.append('(instances (project %s (path "/%s/%s" (reference %s) (unit 1))))' % (q(D.PROJECT), D.ROOT_UUID, D.sheet_uuid(self.name), q(ref)))
        s.append(")")
        self.items.append(" ".join(s))
        out = {}
        for num, px, py in pins:
            dx, dy = rotate(px, py, rot)
            pt = (r3(X + dx), r3(Y + dy))
            out[num] = pt
            if pinnets is not None and num in pinnets:
                self.pinpts.setdefault(pt, []).append((ref, num, pinnets[num]))
            elif num in nc:
                if pt not in self.ncs:
                    self.ncs.add(pt)
                    self.items.append('(no_connect (at %s %s) (uuid "%s"))' % (fmt(pt[0]), fmt(pt[1]), self.uid("nc")))
            elif not ref.startswith("#"):
                raise ValueError("%s Pin %s: weder Netz noch nc" % (ref, num))
        return out

    def part(self, ref, x, y, rot=0, ref_at=None, val_at=None, show_ref=True, show_val=True):
        """Bauteil aus design.py setzen. Gibt {Pinnummer: (x, y)} in Rastereinheiten zurueck."""
        p = self.parts.pop(ref)
        assert D.sheet_of(ref) == self.name, ref
        X, Y = self.P(x, y)
        pts = self._symbol(p.lib_id, ref, p.value, p.fp, X, Y, rot, p.uuid, dict(p.extra, Variante=p.variant), p.pins, p.nc,
                           ref_at, val_at, show_ref, show_val)
        self.p[ref] = {n: (round(px / G - self.ox, 2), round(py / G - self.oy, 2)) for n, (px, py) in pts.items()}
        return self.p[ref]

    def v(self, ref, x, ytop, top="1", **kw):
        """Zweipol senkrecht, Pin `top` oben bei (x, ytop); der andere Pin liegt 3 E darunter."""
        return self.part(ref, x, ytop + 1.5, 0 if top == "1" else 180, **kw)

    def h(self, ref, xleft, y, left="1", **kw):
        """Zweipol waagrecht, Pin `left` links bei (xleft, y); der andere Pin liegt 3 E rechts."""
        return self.part(ref, xleft + 1.5, y, 90 if left == "1" else 270, **kw)

    def pwr(self, net, x, y, d=None):
        """Versorgungssymbol mit sichtbarem Netznamen (SCH-001). d: Richtung, in die das Symbol zeigt."""
        X, Y = self.P(x, y)
        gnd = net == "GND"
        d = d or ("down" if gnd else "up")
        rot = ({"down": 0, "right": 90, "up": 180, "left": 270} if gnd else {"up": 0, "left": 90, "down": 180, "right": 270})[d]
        w = tw(net)
        dx, dy = {"up": (0, -3.8), "down": (0, 3.9), "left": (-3.3 - w / 2, 0), "right": (3.3 + w / 2, 0)}[d]
        PWR_COUNT[0] += 1
        self._symbol(POWER[net], "#PWR%04d" % PWR_COUNT[0], net, "", X, Y, rot, D.uid("pwr/%d" % PWR_COUNT[0]), None, None, (),
                     (0, 0, "center"), (dx, dy, "center"), False, True)
        self._name((X, Y), net)
        self.pinpts.setdefault((X, Y), []).append(("#PWR", "1", net))

    def flag(self, net, x, y, d="up"):
        """PWR_FLAG fuer Netze ohne treibenden Pin (ERC)."""
        X, Y = self.P(x, y)
        self._symbol("power:PWR_FLAG", "#FLG%02d" % FLAGS.setdefault(net, len(FLAGS) + 1), "PWR_FLAG", "", X, Y, 0 if d == "up" else 180,
                     D.uid("flag/" + net), None, None, (), (0, 0, "center"), (0, 0, "center"), False, False)
        self.pinpts.setdefault((X, Y), []).append(("#FLG", "1", net))

    # ---- Leitungen und Labels
    def w(self, *pts):
        """Leitungszug durch die Punkte; aufeinanderfolgende Punkte muessen waagrecht oder senkrecht zueinander liegen."""
        pts = [self.P(*p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            assert a != b and (a[0] == b[0] or a[1] == b[1]), ("schraege oder leere Leitung", self.name, a, b)
            self.segs.append((a, b))

    def _name(self, pt, net):
        assert self.named.setdefault(pt, net) == net, (pt, net)

    def lab(self, net, x, y, o=0):
        """Netzlabel; Netze, die auf mehreren Blaettern vorkommen, bekommen automatisch ein globales Label. o=180: Text nach links."""
        assert net not in POWER, net
        X, Y = self.P(x, y)
        just = "left" if o == 0 else "right"
        if net in self.cross:
            self.items.append('(global_label %s (shape bidirectional) (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s")'
                              ' (property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes))))'
                              % (q(net), fmt(X), fmt(Y), o, just, self.uid("gl"), fmt(X), fmt(Y)))
            w = tw(net) + 3.2
            self.texts.append((X if o == 0 else X - w, Y - 1.1, X + w if o == 0 else X, Y + 1.1, "label", net))
        else:
            self.items.append('(label %s (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
                              % (q(net), fmt(X), fmt(Y), o, just, self.uid("lb")))
            w = tw(net)
            self.texts.append((X if o == 0 else X - w, Y - 2.1, X + w if o == 0 else X, Y - 0.3, "label", net))
        self._name((X, Y), net)

    # ---- Abschluss: Leitungen teilen, Knotenpunkte setzen, Netze und Lesbarkeit pruefen
    @staticmethod
    def _inner(p, a, b):
        if a[0] == b[0] == p[0]:
            return min(a[1], b[1]) < p[1] < max(a[1], b[1])
        if a[1] == b[1] == p[1]:
            return min(a[0], b[0]) < p[0] < max(a[0], b[0])
        return False

    def finish(self):
        named = self.named
        pts = set(self.pinpts) | set(named) | {p for s in self.segs for p in s}
        segs = []
        for a, b in self.segs:
            ch = [a] + sorted((p for p in pts if self._inner(p, a, b)), key=lambda p: abs(p[0] - a[0]) + abs(p[1] - a[1])) + [b]
            segs += list(zip(ch, ch[1:]))
        cnt = {}
        for a, b in segs:
            cnt[a] = cnt.get(a, 0) + 1; cnt[b] = cnt.get(b, 0) + 1
            self.items.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), self.uid("w")))
        for p, n in sorted(cnt.items()):
            if n + len(self.pinpts.get(p, [])) >= 3:
                self.items.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))' % (fmt(p[0]), fmt(p[1]), self.uid("j")))
        # Netze der Zeichnung
        par = {p: p for p in pts}

        def find(p):
            while par[p] != p:
                par[p] = par[par[p]]; p = par[p]
            return p
        for a, b in segs:
            par[find(a)] = find(b)
        err, groups = [], {}
        for p in pts:
            g = groups.setdefault(find(p), {"names": set(), "pins": []})
            if p in named:
                g["names"].add(named[p])
            g["pins"] += self.pinpts.get(p, [])
        for g in groups.values():
            want = {n for _, _, n in g["pins"]}
            who = ", ".join("%s.%s" % (r, n) for r, n, _ in g["pins"] if not r.startswith("#"))[:80]
            if len(g["names"] | want) > 1:
                err.append("Netz: Kurzschluss/Abweichung %s Labels %s an %s" % (sorted(want), sorted(g["names"]), who))
            elif not g["names"]:
                err.append("Netz: %s ohne Label oder Versorgungssymbol an %s" % (sorted(want), who))
        for p in self.ncs:
            if p in cnt or p in self.pinpts:
                err.append("Netz: Leitung an nc-Pin bei %s" % (p,))
        # Lesbarkeit (SCH-004)
        T = self.texts
        hit = lambda a, b, m=0.15: a[0] + m < b[2] and b[0] + m < a[2] and a[1] + m < b[3] and b[1] + m < a[3]
        for i, a in enumerate(T):
            for b in T[i + 1:]:
                if hit(a, b):
                    err.append("Text: '%s' ueberlappt '%s' bei %.0f/%.0f" % (a[5], b[5], a[0], a[1]))
            for bd in self.bodies:
                if bd[4] != a[4] and hit(a, bd):
                    err.append("Text: '%s' liegt auf %s" % (a[5], bd[4]))
            for s1, s2 in segs:
                sb = (min(s1[0], s2[0]) - 0.05, min(s1[1], s2[1]) - 0.05, max(s1[0], s2[0]) + 0.05, max(s1[1], s2[1]) + 0.05)
                if hit(a, sb, 0.2):
                    err.append("Text: Leitung durch '%s' bei %.0f/%.0f" % (a[5], a[0], a[1]))
        for s1, s2 in segs:
            sb = (min(s1[0], s2[0]) - 0.05, min(s1[1], s2[1]) - 0.05, max(s1[0], s2[0]) + 0.05, max(s1[1], s2[1]) + 0.05)
            for bd in self.bodies:
                if hit(sb, bd, 0.3):
                    err.append("Leitung durch Symbol %s bei %.0f/%.0f" % (bd[4], s1[0], s1[1]))
        return ["%s: %s" % (self.name, e) for e in err]

    def write(self, path):
        out = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")', '(uuid "%s")' % D.uid("file/" + self.name),
               '(paper "%s")' % self.paper,
               '(title_block (title %s) (date "%s") (rev "%s") (comment 1 "Generiert mit tools/gen_sch.py"))' % (q(self.title), D.REV_DATE, D.REV),
               '(lib_symbols']
        out += list(self.libs.values()) + [')'] + self.items + ['(embedded_fonts no)', ')']
        open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")


FLAGS = {}
MASTER_NOTE = "Alle Bauteile dieses Blatts werden nur auf der Master-Platine bestückt"


# ---------------------------------------------------------------- Blatt Versorgung
def sheet_versorgung(S):
    S.note("Versorgung: USB-C Power Delivery 15 V, Abwärtswandler 5 V / 6 A, LDO 3,3 V", 8, 18.6, 2.5, bold=True)
    S.note(MASTER_NOTE + " (Ausnahme: C1 sitzt auf jeder Platine).", 8, 20.2, 1.5)

    # --- USB-C, Sicherung, ESD
    S.box(8, 22, 52, 48, "USB-C Eingang, Sicherung, ESD-Schutz")
    S.part("J1", 20, 34, ref_at=(-10.16, -19.6, "left"), val_at=(-6.3, -19.6, "left"))
    S.h("F1", 32.5, 28)
    S.w((26, 28), (32.5, 28)); S.pwr("VBUS", 28, 28); S.flag("VBUS", 30, 28)
    S.w((35.5, 28), (41, 28)); S.pwr("+15V", 38, 28); S.flag("+15V", 41, 28)
    S.w((26, 30), (29, 30)); S.lab("CC1", 29, 30, 180)
    S.w((26, 31), (29, 31)); S.lab("CC2", 29, 31, 180)
    S.part("U3", 35, 36, ref_at=(4.2, 5.2, "left"), val_at=(4.2, 7.4, "left"))
    S.w((26, 33), (32, 33), (32, 36), (33, 36)); S.w((26, 34), (27, 34), (27, 33)); S.lab("USB_D-", 27, 34)   # beide Steckerlagen
    S.w((26, 36), (29, 36), (29, 37), (33, 37)); S.w((26, 35), (27, 35), (27, 36)); S.lab("USB_D+", 27, 35)
    S.w((37, 36), (39, 36)); S.lab("USB_D-", 39, 36)
    S.w((37, 37), (39, 37)); S.lab("USB_D+", 39, 37)
    S.w((35, 34), (35, 32), (46, 32)); S.pwr("+5V", 35, 32)
    S.v("C28", 46, 32); S.pwr("GND", 46, 35)
    S.pwr("GND", 35, 39)
    S.w((17, 43), (17, 44), (20, 44)); S.w((20, 43), (20, 44)); S.pwr("GND", 20, 44); S.flag("GND", 17, 44, "down")
    S.note("F1: PTC-Sicherung im VBUS-Eingang\nU3 Pin 5 an +5V, da VBUS bis 15 V führt\nC28: C_BUS nach ST USBLC6-2 Figure 17", 24, 42.6, top=True)

    # --- USB-PD
    S.box(55, 22, 92, 48, "USB-PD Sink: fordert 15 V an")
    S.part("U6", 76, 34, val_at=(-5.4, -11.76, "left"))
    S.pwr("+15V", 58, 27); S.w((58, 27), (66, 27))
    S.v("R20", 62, 27); S.w((62, 30), (62, 33), (71, 33)); S.lab("PD_VDD", 63.5, 33)
    S.v("C20", 62, 33); S.pwr("GND", 62, 36)
    S.w((70, 33), (70, 35), (71, 35)); S.w((70, 34), (71, 34))                                  # CFG2 = CFG3 = VDD
    S.v("R21", 66, 27); S.w((66, 30), (66, 31), (71, 31)); S.lab("PD_SENSE", 66.5, 31)
    S.w((71, 37), (69, 37), (69, 40), (76, 40)); S.w((76, 39), (76, 40)); S.pwr("GND", 76, 40)  # CFG1 = GND
    S.w((81, 31), (84, 31)); S.lab("CC1", 84, 31, 180)
    S.w((81, 32), (84, 32)); S.lab("CC2", 84, 32, 180)
    S.w((81, 37), (84, 37)); S.lab("PD_GOOD", 84, 37)
    S.note("CFG1 = GND, CFG2 = CFG3 = VDD: Anforderung 15 V\nR20/C20: Versorgung VDD aus +15V, R21: Spannungsmessung\n"
           "PG: Open-Drain, low = PD-Spannung liegt an (Pull-up im ESP32)", 56, 42.6, top=True)

    # --- LDO
    S.box(96, 22, 150, 48, "LDO 3,3 V für ESP32 und Sensor")
    S.part("U2", 122, 34, val_at=(-1.2, -6.05, "left"))
    S.pwr("+5V", 102, 33); S.w((102, 33), (119, 33))
    S.v("C2", 108, 33); S.pwr("GND", 108, 36)
    S.w((119, 34), (117, 34), (117, 33))                                                         # EN = VIN
    S.pwr("GND", 122, 37)
    S.w((125, 33), (140, 33)); S.v("C3", 132, 33); S.pwr("GND", 132, 36); S.pwr("+3V3", 140, 33)
    S.note("EN an VIN: Regler dauernd eingeschaltet\nC2/C3: Stabilität nach Datenblatt (Regel PWR-003)", 97, 42.6, top=True)

    # --- Abwaertswandler
    S.box(16, 60, 120, 88, "Abwärtswandler 15 V → 5 V / 6 A")
    S.part("U7", 50, 72, val_at=(-5.4, -16.84, "left"))
    S.pwr("+15V", 20, 67); S.w((20, 67), (45, 67))
    S.v("C21", 26, 67); S.pwr("GND", 26, 70)
    S.v("C22", 34, 67); S.pwr("GND", 34, 70)
    S.w((45, 71), (43, 71)); S.pwr("GND", 43, 71, "left")                                        # FSEL = GND
    S.w((45, 74), (36, 74)); S.v("C27", 36, 74); S.pwr("GND", 36, 77); S.lab("BUCK_VCC", 40.5, 74)
    S.w((49, 79), (49, 80), (51, 80), (51, 79)); S.pwr("GND", 50, 80)
    S.w((55, 67), (60, 67)); S.lab("BUCK_BST", 55.5, 67)
    S.v("C26", 60, 67)                                                                           # unten direkt auf SW
    S.w((55, 70), (69.5, 70)); S.lab("BUCK_SW", 65, 70)
    S.h("L1", 69.5, 70)
    S.w((72.5, 70), (115.5, 70))                                                                 # +5V-Schiene
    S.w((55, 72), (75, 72), (75, 70))                                                            # VOUT-Messung
    S.v("R22", 79, 70); S.w((79, 73), (79, 74)); S.v("R23", 79, 74); S.pwr("GND", 79, 77)
    S.w((55, 74), (79, 74)); S.lab("BUCK_FB", 56, 74)
    for ref, x in (("C23", 85), ("C24", 92), ("C25", 99), ("C1", 106)):
        S.v(ref, x, 70); S.pwr("GND", x, 73)
    S.pwr("+5V", 113, 70); S.flag("+5V", 115.5, 70)
    S.note("FSEL = GND: 400 kHz · MODE offen: USM · EN offen: Start automatisch\n"
           "R22/R23: Vout = Vref × (1 + 75k / 10,2k); mit Vref = 0,6 V ergibt das 5,01 V\n"
           "C21/C22 direkt an VIN und PGND (Hot-Loop, SCT2360 Figure 22) · C1: Pufferelko, auf jeder Platine", 17, 83.2, top=True)

    S.note("Energiekette: USB-C PD 15 V  →  F1  →  U7 (5 V, bis 6 A)  →  LED-Feld und U2 (3,3 V).\n"
           "Die Firmware begrenzt den LED-Strom auf geschätzte 5 A und schaltet die LEDs nur bei PD_GOOD ein.", 16, 92, 1.5, top=True)


# ---------------------------------------------------------------- Blatt ESP32
def sheet_esp32(S):
    S.note("ESP32-S3, Pegelwandler für die LED-Daten, Umgebungslichtsensor", 20, 22.6, 2.5, bold=True)
    S.note(MASTER_NOTE + ".", 20, 24.2, 1.5)

    S.box(20, 26, 93, 70, "ESP32-S3-MINI-1 mit Reset, Boot und USB")
    S.part("U1", 60, 50, val_at=(1.6, -29.54, "left"))
    S.w((60, 38), (60, 32)); S.w((45, 32), (60, 32)); S.pwr("+3V3", 60, 32)
    S.v("C9", 45, 32); S.pwr("GND", 45, 35)
    S.v("C4", 52, 32); S.pwr("GND", 52, 35)
    S.w((54, 40), (30, 40)); S.lab("EN", 46, 40)
    S.v("R3", 40, 37); S.pwr("+3V3", 40, 37)
    S.v("C5", 36, 40); S.pwr("GND", 36, 43)
    S.part("SW1", 30, 42, 270, ref_at=(-6.5, -1.3, "center"), val_at=(-6.5, 1.3, "center")); S.pwr("GND", 30, 44)
    S.w((54, 42), (48, 42), (48, 48), (30, 48)); S.lab("BOOT", 43, 48)
    S.v("R4", 40, 45); S.pwr("+3V3", 40, 45)
    S.part("SW2", 30, 50, 270, ref_at=(-6.5, -1.3, "center"), val_at=(-6.5, 1.3, "center")); S.pwr("GND", 30, 52)
    S.w((54, 43), (51, 43)); S.lab("SDA", 51, 43, 180)
    S.w((54, 44), (51, 44)); S.lab("SCL", 51, 44, 180)
    S.w((54, 50), (52, 50)); S.lab("LED_3V3", 52, 50, 180)
    S.w((66, 43), (74.5, 43)); S.lab("USB_D-_ESP", 66.5, 43)
    S.h("R24", 74.5, 43, left="2", ref_at=(-1.9, -2.5, "center"), val_at=(2.6, -2.5, "center"))
    S.w((77.5, 43), (80, 43)); S.lab("USB_D-", 80, 43)
    S.w((66, 44), (73, 44), (73, 46), (74.5, 46)); S.lab("USB_D+_ESP", 66.5, 44)
    S.h("R25", 74.5, 46, left="2", ref_at=(-1.9, 2.5, "center"), val_at=(2.6, 2.5, "center"))
    S.w((77.5, 46), (80, 46)); S.lab("USB_D+", 80, 46)
    S.w((66, 52), (70, 52)); S.lab("PD_GOOD", 70, 52)
    S.pwr("GND", 60, 62)
    S.note("USB: natives USB-Serial-JTAG, R24/R25 nahe am Modul (Espressif)\nIO0 = BOOT (SW2), auch Bedientaster der Firmware\n"
           "IO38 = PD_GOOD mit internem Pull-up · C4/C9 direkt am 3V3-Pin", 21, 65, top=True)

    S.box(98, 26, 150, 48, "Pegelwandler LED-Daten 3,3 V → 5 V")
    S.part("U4", 116, 40, ref_at=(3.0, 5.0, "left"), val_at=(3.0, 7.2, "left"))
    S.w((114, 36), (114, 34), (106, 34)); S.pwr("+5V", 114, 34)
    S.v("C6", 106, 34); S.pwr("GND", 106, 37)
    S.w((116, 36), (116, 35), (122, 35), (122, 36)); S.pwr("GND", 122, 36)                      # OE = GND
    S.pwr("GND", 114, 44)
    S.w((102, 40), (110, 40)); S.lab("LED_3V3", 102, 40)
    S.w((121, 40), (126.5, 40)); S.lab("LED_5V", 121.5, 40)
    S.h("R5", 126.5, 40)
    S.w((129.5, 40), (133, 40)); S.lab("DIN", 133, 40)
    S.note("OE = GND: Treiber dauernd aktiv · R5: Serienwiderstand am Anfang der Kette", 99, 46.2, top=True)

    S.box(98, 52, 150, 78, "Umgebungslichtsensor BH1750 (I2C 0x23)")
    S.part("U5", 120, 66, val_at=(-3.6, -9.22, "left"))
    S.pwr("+3V3", 104, 60); S.w((104, 60), (132, 60))
    S.v("R6", 106, 60); S.w((106, 63), (106, 66), (116, 66)); S.lab("DVI", 107, 66)
    S.v("C7", 106, 66); S.pwr("GND", 106, 69)
    S.v("C8", 110, 60); S.pwr("GND", 110, 63)
    S.w((116, 64), (114, 64), (114, 60))
    S.w((116, 68), (114, 68), (114, 71), (120, 71)); S.w((120, 70), (120, 71)); S.pwr("GND", 120, 71)   # ADDR = GND
    S.v("R7", 128, 60); S.w((128, 63), (128, 65), (124, 65)); S.lab("SDA", 124.5, 65)
    S.v("R8", 132, 60); S.w((132, 63), (132, 67), (124, 67)); S.lab("SCL", 124.5, 67)
    S.note("ADDR = GND: Adresse 0x23 · DVI: Reset über R6/C7 beim Einschalten\nR7/R8: I2C-Pull-ups · Sensor sitzt unter dem Lichtleiter", 99, 74.6, top=True)


# ---------------------------------------------------------------- Blatt LED-Feld
def sheet_led(S):
    S.note("LED-Feld: 36 Kammern in der Reihenfolge der Datenkette (alle Platinen)", 7, 6.1, 2.2, bold=True)
    S.note("Kammer x,y = Spalte,Zeile auf der Master-Platine · D1…D75: SK6812RGBW · C101…C175: 100 nF am +5V-Pin der LED\n"
           "LED A wird immer bestückt, LED B wahlweise · JPn schließen, wenn LED B fehlt", 72, 5.0, 1.27, top=True)
    for c, ((k, j), d) in enumerate(D.PATH):
        col, row = c % 6, c // 6
        x0, y0 = 7 + col * 25, 9 + row * 15.5
        yc, nA, nB = y0 + 6, 2 * c + 1, 2 * c + 2
        a_out = S.parts[f"D{nA}"].pins["2"]; b_out = S.parts[f"D{nB}"].pins["2"]; a_in = S.parts[f"D{nA}"].pins["4"]
        S.note("Kammer %d,%d  (#%d)" % (k, j, c + 1), x0, y0 - 1.4, 1.5)
        for n, x in ((nA, x0 + 6), (nB, x0 + 17)):
            S.part(f"D{n}", x, yc, ref_at=(1.2, -9.0, "left"), show_val=False)
            S.w((x, y0 + 3), (x, y0)); S.pwr("GND", x, y0 + 9)
            S.v(f"C{100 + n}", x + 5, y0, top="2", ref_at=(2.6, 0, "left"), show_val=False); S.pwr("GND", x + 5, y0 + 3)
        S.w((x0 + 6, y0), (x0 + 22, y0)); S.pwr("+5V", x0 + 14, y0)
        S.part(f"JP{c + 1}", x0 + 17, y0 + 11.5, ref_at=(11.4, -1.5, "center"), show_val=False)
        S.w((x0 + 9, yc), (x0 + 14, yc)); S.lab(a_out, x0 + 9.5, yc)
        S.w((x0 + 10, yc), (x0 + 10, y0 + 11.5), (x0 + 15, y0 + 11.5))
        S.w((x0 + 19, y0 + 11.5), (x0 + 24, y0 + 11.5), (x0 + 24, yc))
        S.w((x0 + 20, yc), (x0 + (28 if col < 5 else 24 if c in (D.MINUTE_AFTER, 35) else 25), yc)); S.lab(b_out, x0 + 20.5, yc)
        if c == 0:
            S.w((x0 + 2, yc), (x0 + 3, yc)); S.lab(a_in, x0 + 2, yc, 180)
        elif c == D.MINUTE_AFTER + 1:
            S.w((x0 - 1, yc), (x0 + 3, yc)); S.lab(a_in, x0 - 1, yc)
        elif col == 0:                       # Zeilenwechsel als Leitung: rechts herunter, unter der Zeile zurueck
            S.w((157, yc - 15.5), (157, y0 - 2.5), (x0 - 1, y0 - 2.5), (x0 - 1, yc), (x0 + 3, yc))

    S.box(7, 100.5, 33, 111.5, "Minutenpunkt")
    d75 = S.parts["D75"].pins
    S.part("D75", 16, 106, ref_at=(1.2, -9.0, "left"), show_val=False)
    S.w((8, 106), (13, 106)); S.lab(d75["4"], 8, 106)
    S.w((19, 106), (24, 106)); S.lab(d75["2"], 24, 106, 180)
    S.w((16, 103), (28, 103)); S.pwr("+5V", 22, 103); S.pwr("GND", 16, 109)
    S.v("C175", 28, 103, top="2", ref_at=(2.6, 0, "left"), show_val=False); S.pwr("GND", 28, 106)

    S.box(38, 100.5, 82, 111.5, "Kantenbrücken zur Nachbarplatine (0R 2512, von Hand)")
    for ref, x in (("J3", 50), ("J4", 72)):
        pins = S.parts[ref].pins
        S.part(ref, x, 106, ref_at=(-1.27, -8.0, "left"), val_at=(2.6, -8.0, "left"))
        for i in range(5):
            net, y = pins[str(i + 1)], 104 + i
            S.w((x - 2, y), (x - 3, y))
            if net in POWER:
                S.pwr(net, x - 3, y, "left")
            elif net in S.cross:
                S.lab(net, x - 3, y, 180)
            else:                            # lokales Label links neben den Versorgungssymbolen
                S.w((x - 3, y), (x - 10, y)); S.lab(net, x - 10, y)

    S.box(85, 100.5, 112, 111.5, "Montagelöcher M3, Passermarken")
    for i in range(6):
        S.part(f"H{i + 1}", 88 + i * 4, 105, ref_at=(0, -3.3, "center"), show_val=False)
        S.part(f"FID{i + 1}", 88 + i * 4, 109.5, ref_at=(0, -2.7, "center"), show_val=False)


# ---------------------------------------------------------------- Wurzelblatt (Blockschaltbild, SCH-008)
def write_root(path):
    it, n = [], [0]

    def uid(tag):
        n[0] += 1
        return D.uid("sch/root/%s/%d" % (tag, n[0]))

    def text(s, x, y, size=1.5, bold=False):
        it.append('(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) (justify left top)) (uuid "%s"))'
                  % (q(s), fmt(x), fmt(y), fmt(size), fmt(size), " (bold yes)" if bold else "", uid("txt")))

    def arrow(pts, label, lx, ly):
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        dx, dy = (1 if x2 > x1 else -1 if x2 < x1 else 0), (1 if y2 > y1 else -1 if y2 < y1 else 0)
        head = [(x2 - 2.5 * dx - 1.2 * dy, y2 - 2.5 * dy - 1.2 * dx), (x2, y2), (x2 - 2.5 * dx + 1.2 * dy, y2 - 2.5 * dy + 1.2 * dx)]
        for pl in (pts, head):
            it.append('(polyline (pts %s) (stroke (width 0.3) (type default)) (fill (type none)) (uuid "%s"))'
                      % (" ".join("(xy %s %s)" % (fmt(x), fmt(y)) for x, y in pl), uid("pl")))
        text(label, lx, ly, 1.27)

    text("WortUhr LED-Board rev%s: Blockschaltbild" % D.REV, 25, 22, 3.0, True)
    text("Eine Platine, viermal bestellt. Jede trägt das LED-Feld; die Master-Platine trägt zusätzlich Versorgung und ESP32.\n"
         "Versorgungsnetze und blattübergreifende Signale sind global und in den Blättern als Versorgungssymbol oder globales Label gezeichnet.", 25, 29, 1.5)
    info = {"Versorgung": (25, "nur Master\n\nUSB-C mit Sicherung und ESD-Schutz\nUSB-PD Sink CH224K (15 V)\nAbwärtswandler SCT2360 (5 V / 6 A)\nLDO AP2112K (3,3 V)"),
            "ESP32": (115, "nur Master\n\nESP32-S3-MINI-1, Reset/Boot, USB\nPegelwandler 74AHCT1G125\nLichtsensor BH1750 (I2C)"),
            "LED_Feld": (205, "alle Platinen\n\n36 Kammern mit LED A/B und Lötbrücke\nMinutenpunkt, Abblock-Kondensatoren\nKantenbrücken, Montagelöcher, Passermarken")}
    for i, (name, f) in enumerate(D.SHEETS.items()):
        x, body = info[name]
        it.append('(sheet (at %d 60) (size 60 30) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0)) (uuid "%s")'
                  ' (property "Sheetname" %s (at %d 59 0) (effects (font (size 1.8 1.8)) (justify left bottom)))'
                  ' (property "Sheetfile" %s (at %d 91 0) (effects (font (size 1.27 1.27)) (justify left top)))'
                  ' (instances (project %s (path "/%s" (page "%d")))))' % (x, D.sheet_uuid(name), q(name), x, q(f), x, q(D.PROJECT), D.ROOT_UUID, i + 2))
        text(body, x + 2, 62, 1.5)
    arrow([(85, 70), (115, 70)], "+5V, +3V3\nUSB_D+, USB_D-\nPD_GOOD", 88, 72)
    arrow([(175, 70), (205, 70)], "DIN\n(LED-Daten 5 V)", 180, 72)
    arrow([(55, 60), (55, 48), (235, 48), (235, 60)], "+5V, GND (LED-Versorgung, bis 6 A)", 115, 44)
    arrow([(13, 75), (25, 75)], "USB-C\n(PD 15 V)", 13, 78)
    arrow([(265, 75), (280, 75)], "Kanten-\nbrücken", 266, 78)
    out = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")', '(uuid "%s")' % D.ROOT_UUID, '(paper "A4")',
           '(title_block (title "WortUhr LED-Board (4x identisch, Master/Slave)") (date "%s") (rev "%s") (comment 1 "Versorgung: USB-C PD 15 V, Wandler 5 V / 6 A") (comment 2 "Generiert mit tools/gen_sch.py"))'
           % (D.REV_DATE, D.REV), '(lib_symbols)']
    out += it + ['(sheet_instances (path "/" (page "1")))', '(embedded_fonts no)', ')']
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")


# ---------------------------------------------------------------- Aufbau
SHEET_DEF = {"Versorgung": ("Versorgung: USB-C PD, Wandler, LDO", "A3", 0, -8, sheet_versorgung),
             "ESP32": ("ESP32-S3, Pegelwandler, Lichtsensor", "A3", -8, -10, sheet_esp32),
             "LED_Feld": ("LED-Feld, Abblockung und Verbinder", "A3", 0, 0, sheet_led)}


def build(outdir):
    """Schreibt alle Dateien nach outdir. Gibt (Dateinamen, Befunde) zurueck."""
    PWR_COUNT[0] = 0; FLAGS.clear()
    parts = {p.ref: p for p in D.build_parts()}
    netsheets = {}
    for p in parts.values():
        for net in p.pins.values():
            netsheets.setdefault(net, set()).add(D.sheet_of(p.ref))
    cross = {n for n, sh in netsheets.items() if len(sh) > 1}
    issues, files = [], []
    for name, f in D.SHEETS.items():
        title, paper, ox, oy, fn = SHEET_DEF[name]
        S = Sch(name, title, paper, parts, cross, ox, oy)
        fn(S)
        issues += S.finish()
        S.write(os.path.join(outdir, f)); files.append(f)
    if parts:
        issues.append("nicht gezeichnet: " + ", ".join(sorted(parts)))
    write_root(os.path.join(outdir, D.PROJECT + ".kicad_sch")); files.append(D.PROJECT + ".kicad_sch")
    open(os.path.join(outdir, D.PROJECT + ".kicad_sym"), "w", encoding="utf-8", newline="\n").write(
        '(kicad_symbol_lib (version 20241209) (generator "wortuhr_gen") (generator_version "1.0")\n' + "\n".join(PROJECT_SYMS) + "\n)\n")
    files.append(D.PROJECT + ".kicad_sym")
    return files, issues


def check():
    """Befunde des Generators plus Abweichungen zwischen Generator-Stand und Projektdateien."""
    rd = lambda p: open(p, "rb").read().replace(bytes([13, 10]), bytes([10]))   # Zeilenenden haengen von der Git-Einstellung ab
    with tempfile.TemporaryDirectory() as tmp:
        files, issues = build(tmp)
        stale = [f for f in files if not os.path.exists(os.path.join(PRJ, f))
                 or rd(os.path.join(tmp, f)) != rd(os.path.join(PRJ, f))]
    return issues, stale


def main():
    if "--check" in sys.argv:
        issues, stale = check()
        for i in issues:
            print("BEFUND", i)
        for f in stale:
            print("VERALTET", f)
        print("Schaltplan-Pruefung: %d Befunde, %d Dateien weichen vom Generator ab" % (len(issues), len(stale)))
        sys.exit(1 if issues or stale else 0)
    files, issues = build(PRJ)
    for i in issues:
        print("BEFUND", i)
    print("Schaltplan geschrieben:", ", ".join(files), "-", len(issues), "Befunde")
    sys.exit(1 if any("Netz:" in i or i.startswith("nicht") for i in issues) else 0)


if __name__ == "__main__":
    main()
