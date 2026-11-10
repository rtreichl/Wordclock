# -*- coding: utf-8 -*-
"""Wo liegen KiCad und Freerouting? Einzige Stelle mit Installationspfaden.

Reihenfolge: Umgebungsvariable, dann PATH, dann die Vorgabe dieses Rechners (DEFAULT_KICAD).
    KICAD_CLI              kicad-cli (Datei)
    KICAD10_SYMBOL_DIR     Symbolbibliotheken (Ordner mit *.kicad_sym)
    KICAD10_FOOTPRINT_DIR  Footprint-Bibliotheken (Ordner mit *.pretty)
    FREEROUTING_JAR        freerouting.jar
    FREEROUTING_JAVA       java (Datei), passend zum Jar
Ohne die Bibliotheksvariablen werden die Ordner neben kicad-cli gesucht (../share/kicad/...).
"""
import glob, os, shutil, zipfile

DEFAULT_KICAD = r"P:/Program Files/KiCad/10.0"
FREEROUTING_HOME = os.path.expanduser("~/.kicad-mcp")
# Stand, mit dem die eingecheckte Platine geroutet wurde (Build-Revision aus dem Manifest des Jars).
# Freerouting arbeitet nicht deterministisch; ein anderer Stand kann zusaetzlich abweichen.
FREEROUTING_BUILD = "b647a2f824cfbc54bc4dcaee71b03b7cd945eb76"   # Build-Date 2026-10-05, Java 25


def cli():
    c = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli")
    if not c:
        c = os.path.join(DEFAULT_KICAD, "bin", "kicad-cli.exe")
    if not (os.path.exists(c) or shutil.which(c)):
        raise FileNotFoundError("kicad-cli nicht gefunden; KICAD_CLI setzen (siehe tools/kicad_env.py)")
    return c


def _lib_dir(env, sub):
    cands = [os.environ.get(env)]
    exe = shutil.which(cli()) or cli()
    cands.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(exe))), "share", "kicad", sub))
    cands += [os.path.join(DEFAULT_KICAD, "share", "kicad", sub), "/usr/share/kicad/" + sub]
    for c in cands:
        if c and os.path.isdir(c):
            return c.rstrip("/\\") + "/"
    raise FileNotFoundError("KiCad-Bibliotheken (%s) nicht gefunden; %s setzen (siehe tools/kicad_env.py)" % (sub, env))


def symbol_dir():
    return _lib_dir("KICAD10_SYMBOL_DIR", "symbols")


def footprint_dir():
    return _lib_dir("KICAD10_FOOTPRINT_DIR", "footprints")


def freerouting():
    """(java, jar) fuer den lokalen Lauf. Meldet einen anderen Freerouting-Stand als FREEROUTING_BUILD."""
    jar = os.environ.get("FREEROUTING_JAR") or os.path.join(FREEROUTING_HOME, "freerouting.jar")
    local = [p for name in ("java.exe", "java") for p in glob.glob(os.path.join(FREEROUTING_HOME, "jre", "*", "bin", name))]
    java = os.environ.get("FREEROUTING_JAVA") or (local[0] if local else shutil.which("java"))
    if not (java and os.path.exists(jar)):
        raise FileNotFoundError("Freerouting oder Java nicht gefunden; FREEROUTING_JAR / FREEROUTING_JAVA setzen (siehe tools/kicad_env.py)")
    build = freerouting_build(jar)
    if build != FREEROUTING_BUILD:
        print("WARNUNG: Freerouting-Stand %s, die Platine wurde mit %s geroutet" % (build, FREEROUTING_BUILD))
    return java, jar


def freerouting_build(jar):
    try:
        mf = zipfile.ZipFile(jar).read("META-INF/MANIFEST.MF").decode("utf-8", "replace")
        return next((ln.split(":", 1)[1].strip() for ln in mf.splitlines() if ln.startswith("Build-Revision:")), "unbekannt")
    except Exception:
        return "unbekannt"
