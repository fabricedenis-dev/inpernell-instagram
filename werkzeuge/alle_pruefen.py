#!/usr/bin/env python3
"""Prüft alle fertigen Videos aus reels/warteschlange.json auf Vollständigkeit (jedes Wort zu hören).
Aufruf: python werkzeuge/alle_pruefen.py [id ...]"""
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import vollstaendig  # noqa: E402


def texte(r):
    if r.get("sprecher"):
        return [re.sub(r"\[[^\]]*\]\s*", "", s) for s in r["sprecher"]]
    if r.get("sketch"):
        sk = r["sketch"]
    elif "sketch" in r["id"]:
        import zeichentrick_video as zv
        sk = {"dialog": zv.DIALOG, "abspann": zv.ABSPANN_TEXT}
    else:
        return None
    return [e["text"] for e in sk["dialog"]] + [sk["abspann"], "Link in der Bio."]


q = json.load(open(os.path.join(HIER, "reels", "warteschlange.json"), encoding="utf-8"))
ergebnis = {}
for r in q:
    if not r.get("fertig_video") or (len(sys.argv) > 1 and r["id"] not in sys.argv[1:]):
        continue
    t = texte(r)
    if t is None:
        print(f"\n== {r['id']}: ohne Sprache, übersprungen")
        continue
    print(f"\n== {r['id']}")
    fehlt = vollstaendig.pruefe(os.path.join(HIER, r["fertig_video"]), t)
    ergebnis[r["id"]] = [w for w, _ in fehlt if len(w) > 3]
print("\nZUSAMMENFASSUNG")
for k, v in ergebnis.items():
    print(("OK      " if not v else "FEHLT   ") + k + ("" if not v else ": " + ", ".join(v)))
