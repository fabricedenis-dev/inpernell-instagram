#!/usr/bin/env python3
"""Inpernell – Reels veröffentlichen (3 pro Woche) aus der Warteschlange reels/warteschlange.json.

Ablauf: nächstes fälliges Reel (datum <= heute, noch nicht im Protokoll) wählen -> Video und Titelbild
erzeugen -> in docs/reels/ ablegen (über topjob.inpernell.de öffentlich als video/mp4 erreichbar) ->
als Reel veröffentlichen -> Protokoll data/reels.csv -> Video wieder aus docs/ entfernen.

Zeitplan (Europe/Berlin): Dienstag und Donnerstag 07:30, Sonntag 17:00. ERZWINGEN=true ignoriert ihn.
Umgebungsvariablen wie agent.py (IG_ACCESS_TOKEN, IG_USER_ID, DRY_RUN, ERZWINGEN, KEIN_GIT),
dazu REEL_ID = bestimmtes Reel aus der Warteschlange.
"""
import csv
import json
import os
import shutil
import sys
import time
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

import agent
import reel_anim

HIER = os.path.dirname(os.path.abspath(__file__))
WARTESCHLANGE = os.path.join(HIER, "reels", "warteschlange.json")
PROTOKOLL = os.path.join(HIER, "data", "reels.csv")
SEITE = os.environ.get("REEL_BASIS_URL", "https://topjob.inpernell.de/reels/")
ZEITPLAN = {1: (7, 30), 3: (7, 30), 6: (17, 0)}   # Wochentag (0 = Montag) -> Stunde, Minute
SPALTEN = ["datum", "reel_id", "media_id", "url"]


def protokoll_lesen():
    if not os.path.exists(PROTOKOLL):
        return []
    with open(PROTOKOLL, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def protokoll_schreiben(zeile):
    zeilen = protokoll_lesen() + [zeile]
    with open(PROTOKOLL, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN, delimiter=";")
        w.writeheader()
        w.writerows(zeilen)


def _im_fenster(jetzt, stunde, minute):
    """Ab 15 Minuten vor der Planzeit bis 4 Stunden danach (GitHub startet geplante Läufe oft verspätet)."""
    m = jetzt.hour * 60 + jetzt.minute
    return stunde * 60 + minute - 15 <= m <= stunde * 60 + minute + 240


def faelliges_reel(heute):
    """Normale Reels der Reihe nach (ohne feste Uhrzeit). Sonder-Reels mit "zeit" nur über sonder_reel()."""
    warteschlange = json.load(open(WARTESCHLANGE, encoding="utf-8"))
    erledigt = {z["reel_id"] for z in protokoll_lesen()}
    wunsch = os.environ.get("REEL_ID", "").strip()
    for r in warteschlange:
        if wunsch and r["id"] != wunsch:
            continue
        if r["id"] in erledigt or (r.get("zeit") and not wunsch):
            continue
        if wunsch or r.get("datum", "0000") <= heute:
            return r
    return None


def sonder_reel(jetzt):
    """Sonder-Reel mit Datum + Uhrzeit ("zeit": "10:00"), nur wenn vom Inhaber freigegeben."""
    heute = jetzt.strftime("%Y-%m-%d")
    erledigt = {z["reel_id"] for z in protokoll_lesen()}
    for r in json.load(open(WARTESCHLANGE, encoding="utf-8")):
        if r.get("zeit") and r.get("datum") == heute and r["id"] not in erledigt:
            stunde, minute = (int(x) for x in r["zeit"].split(":"))
            if _im_fenster(jetzt, stunde, minute):
                if not r.get("freigegeben"):
                    print(f"::warning::Sonder-Reel {r['id']} ist fällig, aber noch nicht freigegeben – nichts veröffentlicht.")
                    return None
                return r
    return None


def warte_auf_url(url, versuche=40):
    """GitHub Pages braucht nach dem Push 1–3 Minuten, bis die Datei ausgeliefert wird."""
    for _ in range(versuche):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "inpernell-reels/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(10)
    raise RuntimeError("Das Video ist unter seiner öffentlichen Adresse nicht erreichbar: " + url)


def main():
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    heute = jetzt.strftime("%Y-%m-%d")
    probe = agent.wahr("DRY_RUN")
    plan = ZEITPLAN.get(jetzt.weekday())
    sonder = None if os.environ.get("REEL_ID") else sonder_reel(jetzt)
    if sonder:
        print("Sonder-Reel mit fester Uhrzeit:", sonder["id"])
    elif not agent.wahr("ERZWINGEN"):
        # Fenster ab 15 Minuten vor der Planzeit bis 4 Stunden danach (GitHub startet oft verspätet)
        if not plan or not _im_fenster(jetzt, *plan):
            print(f"Heute/jetzt ({jetzt:%a %H:%M}) ist kein Reel geplant. Ende.")
            return
    if not sonder and not probe and any(z["datum"] == heute for z in protokoll_lesen()) and not os.environ.get("REEL_ID"):
        print("Heute wurde bereits ein Reel veröffentlicht. Ende.")
        return
    reel = sonder or faelliges_reel(heute)
    if not reel:
        print("::warning::Die Reel-Warteschlange ist leer – bitte neue Reels in reels/warteschlange.json ergänzen.")
        return
    print("Reel:", reel["id"])

    ordner = os.path.join(HIER, "docs", "reels")
    os.makedirs(ordner, exist_ok=True)
    video_rel = f"docs/reels/{reel['id']}.mp4"
    titel_rel = f"docs/reels/{reel['id']}.jpg"
    if reel.get("fertig_video"):                       # fertig gebautes, vom Inhaber abgenommenes Video
        shutil.copyfile(os.path.join(HIER, reel["fertig_video"]), os.path.join(HIER, video_rel))
        shutil.copyfile(os.path.join(HIER, reel["fertig_titelbild"]), os.path.join(HIER, titel_rel))
    else:
        reel_anim.aus_definition(reel, os.path.join(HIER, video_rel), titelbild=os.path.join(HIER, titel_rel))
    print(f"Video erzeugt: {os.path.getsize(os.path.join(HIER, video_rel)) / 1e6:.1f} MB")
    if probe:
        print("PROBELAUF: Video liegt in", video_rel, "– es wurde NICHTS veröffentlicht.")
        return

    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Das Secret IG_ACCESS_TOKEN fehlt.")
    agent.git_sichern(f"Reel {reel['id']}: Video bereitgestellt", video_rel, titel_rel)
    video_url, titel_url = SEITE + reel["id"] + ".mp4", SEITE + reel["id"] + ".jpg"
    warte_auf_url(video_url)
    warte_auf_url(titel_url)
    media_id = agent.veroeffentlichen(token, reel["caption"][:2200], video_url=video_url, titelbild_url=titel_url)
    print("Reel veröffentlicht. ID:", media_id)
    protokoll_schreiben({"datum": heute, "reel_id": reel["id"], "media_id": media_id, "url": video_url})
    # Video wieder entfernen, damit das Repository klein bleibt (Instagram hat es bereits geladen)
    if not agent.wahr("KEIN_GIT"):
        agent.git("rm", "-q", video_rel)
    agent.git_sichern(f"Reel {reel['id']}: veröffentlicht", "data/reels.csv")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"::error::{e}")
        sys.exit(1)
