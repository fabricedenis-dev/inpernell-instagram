#!/usr/bin/env python3
"""Rendert Sketche aus reels/warteschlange.json nach reels/fertig/ (mit Pflichtprüfung auf Vollständigkeit)
und erzeugt das Titelbild. Aufruf: python werkzeuge/sketche_rendern.py <id> [...]"""
import json
import os
import subprocess
import sys

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HIER)
os.chdir(HIER)
import zeichentrick_video as zv  # noqa: E402

q = json.load(open("reels/warteschlange.json", encoding="utf-8"))
for rid in sys.argv[1:]:
    r = next(x for x in q if x["id"] == rid)
    print("== RENDER", rid, flush=True)
    try:
        zv.main(r["fertig_video"], r["sketch"])
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", r["fertig_video"], "-frames:v", "1",
                        "-q:v", "2", r["fertig_titelbild"]], check=True)
        print("== FERTIG", rid, flush=True)
    except Exception as ex:
        print("== FEHLER", rid, ex, flush=True)
