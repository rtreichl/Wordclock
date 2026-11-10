# -*- coding: utf-8 -*-
"""Vergleich alt/neu fuer Platine und Schaltplan als Farbbilder.

Aufruf:  python tools/vergleich.py ALT [NEU] [--out ORDNER]
    ALT   Git-Stand des alten Entwurfs (Commit, Branch, Tag)
    NEU   Git-Stand des neuen Entwurfs; ohne Angabe die Dateien im Arbeitsordner
    --out Ausgabeordner (Standard: 02_Electronics/Vergleich)

Beide Staende werden mit kicad-cli schwarz-weiss als PDF ausgegeben (Platine: eine Seite je Lage mit
Platinenumriss; Schaltplan: jedes Blatt ohne Schriftfeld), gerastert und pixelweise verglichen:
    rot   nur im alten Stand (entfernt)
    gruen nur im neuen Stand (hinzugefuegt)
    grau  unveraendert
Erzeugt:
- Vergleich.pdf         eine Seite je Lage bzw. Blatt, geaenderte zuerst
- png/<Name>.png        dieselben Bilder einzeln
- Vergleich.md          Uebersicht: was hat sich wo geaendert
Braucht PyMuPDF (pymupdf) und numpy; in KiCads Python auf Windows enthalten.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile

import numpy as np
try:
    import pymupdf as fitz
except ImportError:
    import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)                                   # 02_Electronics/KiCad
ROOT = os.path.dirname(os.path.dirname(PRJ))
sys.path.insert(0, HERE)
import kicad_env  # noqa: E402

REL = os.path.relpath(PRJ, ROOT).replace("\\", "/")
EXT = (".kicad_pro", ".kicad_pcb", ".kicad_sch", ".kicad_sym")
LAYERS = ["F.Cu", "B.Cu", "F.Silkscreen", "B.Silkscreen", "F.Mask", "B.Mask", "F.Fab", "B.Fab"]
PAPIER = '(paper "A2")'                                       # 594 x 420 mm: Platine liegt bei x, y = 40...275 mm
DPI_PCB, DPI_SCH, MARGIN = 400, 200, 40
ROT, GRUEN, GRAU = (215, 25, 32), (0, 150, 60), (200, 200, 200)


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), check=True, capture_output=True).stdout


def stand(ref, ziel):
    """Projektdateien eines Git-Stands (oder des Arbeitsordners bei ref=None) nach ziel kopieren."""
    os.makedirs(ziel)
    if ref is None:
        namen = [f for f in os.listdir(PRJ) if f.endswith(EXT) and not f.startswith("_autosave")]
        for f in namen:
            shutil.copy2(os.path.join(PRJ, f), ziel)
        return namen
    try:
        liste = git("ls-tree", "--name-only", ref, REL + "/").decode().split()
    except subprocess.CalledProcessError:
        raise SystemExit("Git-Stand nicht gefunden: %s" % ref)
    namen = []
    for p in liste:
        f = p.rsplit("/", 1)[-1]
        if f.endswith(EXT) and not f.startswith("_autosave"):
            open(os.path.join(ziel, f), "wb").write(git("show", "%s:%s" % (ref, p)))
            namen.append(f)
    return namen


def cli(args):
    r = subprocess.run([kicad_env.cli()] + args, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("kicad-cli fehlgeschlagen: %s\n%s" % (" ".join(args), r.stdout + r.stderr))


def seiten(ordner, namen):
    """{Name: (PDF-Datei, Seitenindex, dpi)} fuer jede Platinenlage und jedes Schaltplanblatt."""
    out = {}
    pcb = next((f for f in namen if f.endswith(".kicad_pcb")), None)
    if pcb:
        # Die Platine reicht ueber das A4-Blatt hinaus; nur in der Arbeitskopie ein groesseres Blatt waehlen
        p = os.path.join(ordner, pcb)
        s = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(re.sub(r'\(paper "[^"]*"[^)]*\)', PAPIER, s, count=1))
        pdf = os.path.join(ordner, "pcb.pdf")
        cli(["pcb", "export", "pdf", "--mode-multipage", "--black-and-white", "--layers", ",".join(LAYERS),
             "--common-layers", "Edge.Cuts", "-o", pdf, p])
        for i, t in enumerate(blattnamen(pdf)):
            out["Platine " + t] = (pdf, i, DPI_PCB)
    haupt = os.path.splitext(pcb or "")[0] + ".kicad_sch"
    if haupt in namen:
        pdf = os.path.join(ordner, "sch.pdf")
        cli(["sch", "export", "pdf", "--black-and-white", "--exclude-drawing-sheet", "--exclude-pdf-property-popups",
             "--exclude-pdf-hierarchical-links", "--exclude-pdf-metadata", "-o", pdf, os.path.join(ordner, haupt)])
        for i, t in enumerate(blattnamen(pdf)):
            out["Schaltplan " + t] = (pdf, i, DPI_SCH)
    return out


def blattnamen(pdf):
    """Seitennamen aus den Lesezeichen der Seiten ("F.Cu (Seite 1)" -> "F.Cu", auf jeder Ebene); sonst Seitennummern."""
    doc = fitz.open(pdf)
    namen = ["Seite %d" % (i + 1) for i in range(doc.page_count)]
    for _lvl, t, pno in doc.get_toc():
        m = re.match(r"(.*?)\s*\([^()]*\d+\)$", t)                # "(Seite 1)", "(Page 1)"
        if m and 1 <= pno <= doc.page_count and namen[pno - 1].startswith("Seite "):
            namen[pno - 1] = m.group(1).strip("/ ") or "Hauptblatt"
    return namen


def raster(eintrag):
    if eintrag is None:
        return None
    pdf, i, dpi = eintrag
    pm = fitz.open(pdf)[i].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY, alpha=False)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width).copy()


def vergleich(alt, neu):
    """Farbbild und Anzahl entfernter/hinzugefuegter Pixel. Fehlt ein Stand, gilt er als leer."""
    h = max(a.shape[0] for a in (alt, neu) if a is not None)
    w = max(a.shape[1] for a in (alt, neu) if a is not None)

    def maske(a):
        m = np.zeros((h, w), bool)
        if a is not None:
            m[:a.shape[0], :a.shape[1]] = a < 128
        return m
    ma, mn = maske(alt), maske(neu)
    img = np.full((h, w, 3), 255, np.uint8)
    img[ma & mn] = GRAU
    img[ma & ~mn] = ROT
    img[mn & ~ma] = GRUEN
    ys, xs = np.nonzero(ma | mn)
    if len(ys):
        y0, y1 = max(ys.min() - MARGIN, 0), min(ys.max() + MARGIN, h)
        x0, x1 = max(xs.min() - MARGIN, 0), min(xs.max() + MARGIN, w)
        img = img[y0:y1, x0:x1]
    return img, int((ma & ~mn).sum()), int((mn & ~ma).sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("alt")
    ap.add_argument("neu", nargs="?")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(PRJ), "Vergleich"))
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="vergleich_")
    sa = seiten(os.path.join(tmp, "alt"), stand(a.alt, os.path.join(tmp, "alt")))
    sn = seiten(os.path.join(tmp, "neu"), stand(a.neu, os.path.join(tmp, "neu")))
    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    os.makedirs(os.path.join(a.out, "png"))

    reihen = []
    for name in list(sn) + [n for n in sa if n not in sn]:
        alt, neu = sa.get(name), sn.get(name)
        img, minus, plus = vergleich(raster(alt), raster(neu))
        dpi = (neu or alt)[2]
        datei = re.sub(r"[^\w.\-]", "_", name) + ".png"
        fitz.Pixmap(fitz.csRGB, img.shape[1], img.shape[0], img.tobytes(), False).save(os.path.join(a.out, "png", datei))
        status = "neu" if alt is None else "entfernt" if neu is None else "geaendert" if minus or plus else "unveraendert"
        reihen.append((name, status, minus, plus, datei, img.shape[:2], dpi))
        del img
    reihen.sort(key=lambda r: (r[1] == "unveraendert", r[0]))

    alt_txt = a.alt + " (" + git("rev-parse", "--short", a.alt).decode().strip() + ")"
    neu_txt = a.neu + " (" + git("rev-parse", "--short", a.neu).decode().strip() + ")" if a.neu else "Arbeitsordner"
    pdf = fitz.open()
    for name, status, minus, plus, datei, (hp, wp), dpi in reihen:
        w, h = wp * 72 / dpi, hp * 72 / dpi
        page = pdf.new_page(width=max(w, 420), height=h + 40)
        page.insert_text((10, 16), "%s  [%s]" % (name, status), fontsize=11)
        page.insert_text((10, 30), "alt: %s   neu: %s   rot = nur alt, gruen = nur neu, grau = gleich"
                         % (alt_txt, neu_txt), fontsize=7)
        page.insert_image(fitz.Rect(0, 40, w, 40 + h), filename=os.path.join(a.out, "png", datei))
    pdf.save(os.path.join(a.out, "Vergleich.pdf"), deflate=True)

    geaendert = [r for r in reihen if r[1] != "unveraendert"]
    with open(os.path.join(a.out, "Vergleich.md"), "w", encoding="utf-8") as f:
        f.write("# Vergleich Platine und Schaltplan\n\nalt: %s  \nneu: %s\n\n" % (alt_txt, neu_txt))
        f.write("Rot = nur im alten Stand (entfernt), Gruen = nur im neuen Stand (hinzugefuegt), Grau = unveraendert.\n\n")
        f.write("| Lage / Blatt | Status | Pixel entfernt | Pixel hinzugefuegt | Bild |\n|---|---|---:|---:|---|\n")
        for name, status, minus, plus, datei, _img, _dpi in reihen:
            f.write("| %s | %s | %d | %d | png/%s |\n" % (name, status, minus, plus, datei))
    shutil.rmtree(tmp, ignore_errors=True)
    print("%d von %d Lagen/Blaettern geaendert -> %s" % (len(geaendert), len(reihen), a.out))


if __name__ == "__main__":
    main()
