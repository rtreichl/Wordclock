# -*- coding: utf-8 -*-
"""Prueft, ob die freigegebenen Dateien in 05_Production noch zu ihren Berichten passen.

Jeder Bericht QUALIFIKATION.md nennt seine Dateien mit SHA256-Pruefsumme. Wer eine Datei in 05_Production
von Hand aendert (statt die Quelle zu aendern und neu zu qualifizieren), faellt hier auf. Dateien, die es
gleichnamig in einem Quellordner gibt, muessen dort denselben Inhalt haben.

Aufruf:  python 05_Production/tools/check_production.py     (Rueckgabewert 1 bei Abweichungen)
"""
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(ROOT, "05_Production")
SOURCES = ["01_Mechanic/Gitter", "01_Mechanic/Gitter/JLC3DP", "01_Mechanic/Rueckrahmen", "03_Software/WLED"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


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
            elif not sha(p).startswith(h):
                bad.append("%s/%s: Inhalt passt nicht zur Pruefsumme im Bericht" % (part, f))
            else:
                for s in SOURCES:
                    q = os.path.join(ROOT, s, f)
                    if os.path.exists(q) and sha(q) != sha(p):
                        bad.append("%s/%s: weicht von der Quelle %s/%s ab" % (part, f, s, f))
    for b in bad:
        print("ABWEICHUNG", b)
    print("Produktionsdaten: %d Dateien geprueft, %d Abweichungen" % (n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
