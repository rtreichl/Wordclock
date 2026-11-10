# -*- coding: utf-8 -*-
"""Prueft, ob die freigegebenen Dateien in 05_Production noch zu ihren Berichten passen.

Jeder Bericht QUALIFIKATION.md nennt seine Dateien mit SHA256-Pruefsumme. Wer eine Datei in 05_Production
von Hand aendert (statt die Quelle zu aendern und neu zu qualifizieren), faellt hier auf. Dateien, die es
gleichnamig in einem Quellordner gibt, muessen dort denselben Inhalt haben.

Textdateien (CSV, DXF) haben je nach Git-Einstellung CRLF oder LF als Zeilenende; die Pruefsumme im Bericht
stammt vom Rechner, der den Bericht geschrieben hat. Deshalb gilt eine Datei als passend, wenn sie mit einem
der beiden Zeilenenden zur Pruefsumme passt.

Aufruf:  python 05_Production/tools/check_production.py     (Rueckgabewert 1 bei Abweichungen)
"""
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(ROOT, "05_Production")
SOURCES = ["01_Mechanic/Gitter", "01_Mechanic/Gitter/JLC3DP", "01_Mechanic/Rueckrahmen", "03_Software/WLED"]


def shas(p):
    """Pruefsummen der Datei, wie sie ist, mit LF und mit CRLF als Zeilenende."""
    d = open(p, "rb").read()
    CR_LF, LF = bytes([13, 10]), bytes([10])
    lf = d.replace(CR_LF, LF)
    return {hashlib.sha256(x).hexdigest() for x in (d, lf, lf.replace(LF, CR_LF))}


def main():
    bad, n = [], 0
    for part in sorted(os.listdir(PROD)):
        d = os.path.join(PROD, part)
        rep = os.path.join(d, "QUALIFIKATION.md")
        if not os.path.isfile(rep):
            continue
        listed = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{16})…` \|$", open(rep, encoding="utf-8").read(), re.M))
        present = {f for f in os.listdir(d) if f != "QUALIFIKATION.md"}
        for f in sorted(present - set(listed)):
            bad.append("%s/%s: liegt im Ordner, steht aber nicht im Bericht" % (part, f))
        for f, h in sorted(listed.items()):
            p = os.path.join(d, f); n += 1
            if not os.path.exists(p):
                bad.append("%s/%s: im Bericht, Datei fehlt" % (part, f))
            elif not any(x.startswith(h) for x in shas(p)):
                bad.append("%s/%s: Inhalt passt nicht zur Pruefsumme im Bericht" % (part, f))
            else:
                for s in SOURCES:
                    q = os.path.join(ROOT, s, f)
                    if os.path.exists(q) and not (shas(q) & shas(p)):
                        bad.append("%s/%s: weicht von der Quelle %s/%s ab" % (part, f, s, f))
    for b in bad:
        print("ABWEICHUNG", b)
    print("Produktionsdaten: %d Dateien geprueft, %d Abweichungen" % (n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
